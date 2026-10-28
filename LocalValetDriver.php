<?php

use Valet\Drivers\ValetDriver;

/**
 * Local preview only: makes https://mohamedsharaf.test serve the built site in dist/
 * (run `sh build.sh` first), the way Cloudflare serves it. Never copied into dist/.
 */
class LocalValetDriver extends ValetDriver
{
    public function serves(string $sitePath, string $siteName, string $uri): bool
    {
        return is_dir($sitePath.'/dist');
    }

    public function isStaticFile(string $sitePath, string $siteName, string $uri)/* : string|false */
    {
        $dist = $sitePath.'/dist';
        if (str_contains($uri, '..') || $this->redirectFor($dist) !== null) {
            return false;
        }
        foreach ([$uri, rtrim($uri, '/').'.html'] as $candidate) {
            if ($candidate !== '/' && is_file($dist.$candidate)) {
                return $dist.$candidate;
            }
        }
        if (str_ends_with($uri, '/') && is_file($dist.$uri.'index.html')) {
            return $dist.$uri.'index.html';
        }

        return false;
    }

    public function frontControllerPath(string $sitePath, string $siteName, string $uri): ?string
    {
        $dist = $sitePath.'/dist';
        $target = $this->redirectFor($dist);
        if ($target === null && !str_ends_with($uri, '/') && is_file($dist.$uri.'/index.html')) {
            $target = $uri.'/';
        }
        if ($target !== null) {
            header('Location: '.$target, true, 301);
            exit;
        }
        // Valet never asks isStaticFile() about "/", so the homepage is served here
        if (str_ends_with($uri, '/') && is_file($dist.$uri.'index.html')) {
            header('Content-Type: text/html; charset=utf-8');
            readfile($dist.$uri.'index.html');
            exit;
        }
        http_response_code(404);
        header('Content-Type: text/html; charset=utf-8');
        readfile($dist.'/404.html');
        exit;
    }

    /** First matching rule in dist/_redirects for this request, or null. */
    private function redirectFor(string $dist): ?string
    {
        $path = explode('?', $_SERVER['REQUEST_URI'] ?? '/')[0];
        $file = $dist.'/_redirects';
        if (!is_file($file)) {
            return null;
        }
        foreach (file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $rule = preg_split('/\s+/', trim($line));
            if (count($rule) < 2 || $rule[0][0] === '#') {
                continue;
            }
            [$from, $to] = $rule;
            if (str_ends_with($from, '*') ? str_starts_with($path, substr($from, 0, -1)) : $path === $from) {
                return $to;
            }
        }

        return null;
    }
}
