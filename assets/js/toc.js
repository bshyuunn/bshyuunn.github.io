// Table of contents for posts: built from the post's ## / ### headings,
// with the current section highlighted while scrolling.
(function () {
  var toc = document.querySelector('.toc');
  var list = toc && toc.querySelector('.toc-list');
  var prose = document.querySelector('.prose');
  if (!toc || !list || !prose) return;

  var heads = Array.prototype.filter.call(prose.querySelectorAll('h2, h3'), function (h) { return h.id; });
  if (heads.length < 2) return;

  var links = heads.map(function (h) {
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent.trim();
    if (h.tagName === 'H3') a.className = 'sub';
    list.appendChild(a);
    return a;
  });
  toc.hidden = false;

  // Start the rail level with the article, then let it stick.
  function place() {
    var grid = toc.parentElement;
    toc.style.marginTop = Math.max(0, prose.getBoundingClientRect().top - grid.getBoundingClientRect().top) / (parseFloat(getComputedStyle(document.body).zoom) || 1) + 'px';
  }

  var current = -1, queued = false;
  function spy() {
    queued = false;
    var line = Math.min(160, window.innerHeight * 0.3);
    var i = 0;
    for (var k = 0; k < heads.length; k++) {
      if (heads[k].getBoundingClientRect().top <= line) i = k;
    }
    var se = document.scrollingElement || document.documentElement;
    if (se.scrollTop + window.innerHeight >= se.scrollHeight - 2) i = heads.length - 1;
    if (i === current) return;
    if (current >= 0) links[current].removeAttribute('aria-current');
    links[i].setAttribute('aria-current', 'location');
    current = i;
  }
  function onScroll() { if (!queued) { queued = true; requestAnimationFrame(spy); } }

  place();
  spy();
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', function () { place(); onScroll(); }, { passive: true });
  window.addEventListener('load', function () { place(); spy(); });
})();
