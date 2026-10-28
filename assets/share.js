// Share bar on article pages: the plain links work without JavaScript; this adds
// "copy link" and the phone's own share sheet where the browser supports them.
(function () {
  var bar = document.querySelector('.share');
  if (!bar) return;
  var url = bar.getAttribute('data-url');
  var title = bar.getAttribute('data-title');
  var copy = bar.querySelector('.share-copy');
  var native = bar.querySelector('.share-native');

  if (copy && navigator.clipboard) {
    copy.hidden = false;
    copy.addEventListener('click', function () {
      navigator.clipboard.writeText(url).then(function () {
        var label = copy.textContent;
        copy.textContent = copy.getAttribute('data-done');
        setTimeout(function () { copy.textContent = label; }, 2500);
      });
    });
  }
  if (native && navigator.share) {
    native.hidden = false;
    native.addEventListener('click', function () {
      navigator.share({ title: title, url: url }).catch(function () {});
    });
  }
})();
