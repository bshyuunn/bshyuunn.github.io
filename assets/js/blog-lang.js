(function () {
  var rows = document.querySelectorAll('.post-list .post-row');
  var buttons = document.querySelectorAll('.page-head .lang-switch button[data-lang]');
  if (!rows.length || !buttons.length) return;

  function remember(lang) {
    try { localStorage.setItem('lang', lang); } catch (error) { /* storage may be blocked */ }
  }

  function show(lang) {
    Array.prototype.forEach.call(buttons, function (button) {
      button.setAttribute('aria-pressed', String(button.getAttribute('data-lang') === lang));
    });
    Array.prototype.forEach.call(rows, function (row) {
      var href = row.getAttribute('data-href-' + lang);
      row.hidden = !href;
      var marker = row.querySelector('.lang-marker');
      if (marker) {
        marker.textContent = lang === 'ko' ? '· EN' : '· KO';
        marker.title = lang === 'ko' ? 'Also in English' : 'Also in Korean';
        marker.hidden = false;
      }
      if (!href) return;
      var title = row.querySelector('.t');
      row.href = href;
      title.textContent = row.getAttribute('data-title-' + lang);
      title.lang = lang;
    });
  }

  var query = new URLSearchParams(location.search).get('lang');
  var saved;
  try { saved = localStorage.getItem('lang'); } catch (error) { /* storage may be blocked */ }
  var initial = query === 'ko' || query === 'en' ? query : saved === 'ko' ? 'ko' : 'en';
  show(initial);
  remember(initial);

  Array.prototype.forEach.call(buttons, function (button) {
    button.addEventListener('click', function () {
      var lang = button.getAttribute('data-lang');
      show(lang);
      remember(lang);
      var params = new URLSearchParams(location.search);
      params.set('lang', lang);
      history.replaceState(null, '', location.pathname + '?' + params.toString() + location.hash);
    });
  });
})();
