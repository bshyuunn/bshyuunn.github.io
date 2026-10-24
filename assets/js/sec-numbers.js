// Turn a leading "01. " on post h2s into a colored "§1" marker, matching the About page's section style.
(function () {
  var heads = document.querySelectorAll('.prose h2');
  heads.forEach(function (h) {
    var m = h.innerHTML.match(/^\s*(\d{1,2})\.\s+/);
    if (!m) return;
    var num = parseInt(m[1], 10);
    h.innerHTML = '<span class="sec">§' + num + '</span>' + h.innerHTML.slice(m[0].length);
  });
})();
