/**
 * mohamedsharaf.com Worker. Only /api/* reaches this code (run_worker_first in wrangler.toml);
 * every page and file is served straight from static assets.
 *
 * POST /api/contact: the contact form. A message is delivered only when it passes, in order:
 * same-origin request, JSON body under 16 KB, empty honeypot, per-IP rate limit,
 * Turnstile (siteverify: success, action "contact", an approved hostname) and field validation.
 * It is emailed to the owner's verified Email Routing address and never stored.
 *
 * Bindings and settings:
 *   EMAIL             send_email binding (Cloudflare Email Routing, verified destinations only)
 *   CONTACT_LIMIT     rate limit binding, keyed by visitor IP
 *   TURNSTILE_SECRET  secret
 *   CONTACT_TO        secret: the verified destination address (kept out of the public repo)
 *   CONTACT_FROM      sender on mohamedsharaf.com
 *   ALLOWED_ORIGINS   comma-separated origins allowed to post the form
 *   TURNSTILE_HOSTNAMES  comma-separated hostnames Turnstile must report
 *   ALLOW_TEST_KEYS   "1" only in local .dev.vars, to accept Turnstile's test keys
 */

const MAX_BODY = 16 * 1024;
const TOPICS = new Set(['Just saying hello', 'A second opinion', 'A test or an audit', 'Ongoing advice', 'Something else']);
const EMAIL_RE = /^[^\s@<>()[\]\\,;:"]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/;

const API_HEADERS = {
	'Content-Type': 'application/json; charset=utf-8',
	'Cache-Control': 'no-store',
	'X-Content-Type-Options': 'nosniff',
	'Content-Security-Policy': "default-src 'none'; frame-ancestors 'none'",
	'Referrer-Policy': 'no-referrer',
	'Cross-Origin-Resource-Policy': 'same-origin',
};

const reply = (status, body, extra = {}) =>
	new Response(JSON.stringify(body), { status, headers: { ...API_HEADERS, ...extra } });

const list = (value) => new Set(String(value ?? '').split(',').map((s) => s.trim()).filter(Boolean));

// Plain single-line text: no control characters, collapsed spaces
const oneLine = (value) => String(value ?? '').replace(/[\u0000-\u001f\u007f-\u009f\u2028\u2029]/g, ' ').replace(/\s+/g, ' ').trim();

// Multi-line text: keep line breaks and tabs, drop other control characters
const multiLine = (value) =>
	String(value ?? '')
		.replace(/\r\n?/g, '\n')
		.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u2028\u2029]/g, '')
		.replace(/\n{4,}/g, '\n\n\n')
		.trim();

async function verifyTurnstile(token, ip, env) {
	if (typeof token !== 'string' || token.length === 0 || token.length > 2048) return false;
	const hostnames = list(env.TURNSTILE_HOSTNAMES);
	if (!env.TURNSTILE_SECRET || hostnames.size === 0) return false;
	let result;
	try {
		const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
			method: 'POST',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			signal: AbortSignal.timeout(10_000),
			body: new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: token, remoteip: ip }),
		});
		if (!r.ok) return false;
		result = await r.json();
	} catch {
		return false; // network error, timeout or a non-JSON answer: fail closed
	}
	if (result.success !== true || !hostnames.has(result.hostname)) return false;
	// Turnstile's test keys report no action; they are only accepted when running locally
	if (result.metadata?.result_with_testing_key) return env.ALLOW_TEST_KEYS === '1';
	return result.action === 'contact';
}

function validate(data) {
	const name = oneLine(data.name);
	const email = oneLine(data.email);
	const topic = oneLine(data.topic);
	const message = multiLine(data.message);
	const lang = data.lang === 'ar' ? 'ar' : 'en';
	const ok =
		name.length >= 1 && name.length <= 100 &&
		email.length <= 254 && EMAIL_RE.test(email) &&
		TOPICS.has(topic) &&
		message.length >= 10 && message.length <= 5000;
	return ok ? { name, email, topic, message, lang } : null;
}

async function contact(request, env) {
	if (request.method !== 'POST') return reply(405, { ok: false, error: 'method' }, { Allow: 'POST' });

	// Only the site's own pages may post here
	const origin = request.headers.get('Origin');
	const site = request.headers.get('Sec-Fetch-Site');
	if (!origin || !list(env.ALLOWED_ORIGINS).has(origin) || (site && site !== 'same-origin')) {
		return reply(403, { ok: false, error: 'origin' });
	}
	if (!(request.headers.get('Content-Type') || '').toLowerCase().startsWith('application/json')) {
		return reply(415, { ok: false, error: 'type' });
	}
	if (Number(request.headers.get('Content-Length') || 0) > MAX_BODY) return reply(413, { ok: false, error: 'size' });

	const raw = await request.text();
	if (raw.length > MAX_BODY) return reply(413, { ok: false, error: 'size' });
	let data;
	try {
		data = JSON.parse(raw);
	} catch {
		return reply(400, { ok: false, error: 'invalid' });
	}
	if (!data || typeof data !== 'object' || Array.isArray(data)) return reply(400, { ok: false, error: 'invalid' });

	// Honeypot filled in: a bot. Answer as if it worked so it learns nothing.
	if (data.website) return reply(200, { ok: true });

	const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
	const { success: allowed } = await env.CONTACT_LIMIT.limit({ key: ip });
	if (!allowed) return reply(429, { ok: false, error: 'rate' }, { 'Retry-After': '60' });

	if (!(await verifyTurnstile(data.token, ip, env))) return reply(403, { ok: false, error: 'verification' });

	const form = validate(data);
	if (!form) return reply(400, { ok: false, error: 'invalid' });

	const country = request.headers.get('CF-IPCountry') || request.cf?.country || '?';
	try {
		await env.EMAIL.send({
			from: { email: env.CONTACT_FROM, name: 'mohamedsharaf.com' },
			to: env.CONTACT_TO,
			replyTo: { email: form.email, name: form.name },
			subject: `New message: ${form.topic}`,
			text: [
				`Name: ${form.name}`,
				`Email: ${form.email}`,
				`Topic: ${form.topic}`,
				`Page: ${form.lang === 'ar' ? 'Arabic' : 'English'}`,
				`Country: ${country}`,
				'',
				form.message,
				'',
				'--',
				'Sent from the contact form on mohamedsharaf.com. Reply to answer directly.',
			].join('\n'),
		});
	} catch (error) {
		console.error('contact: email failed', error?.code || error?.message);
		return reply(502, { ok: false, error: 'send' });
	}
	return reply(200, { ok: true });
}

export default {
	async fetch(request, env) {
		const { pathname } = new URL(request.url);
		if (pathname === '/api/contact') return contact(request, env);
		return reply(404, { ok: false, error: 'not_found' });
	},
};
