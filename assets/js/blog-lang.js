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
      var en = row.getAttribute('data-href-en');
      var ko = row.getAttribute('data-href-ko');
      var displayed = lang === 'ko' && ko ? 'ko' : en ? 'en' : 'ko';
      var title = row.querySelector('.t');
      var marker = row.querySelector('.lang-marker');
      row.href = row.getAttribute('data-href-' + displayed);
      title.textContent = row.getAttribute('data-title-' + displayed);
      title.lang = displayed;

      if (lang === 'en' && en && ko) {
        marker.textContent = '· KO';
        marker.title = 'Also in Korean';
        marker.hidden = false;
      } else if (lang === 'en' && !en) {
        marker.textContent = '· KO only';
        marker.title = 'Only in Korean';
        marker.hidden = false;
      } else if (lang === 'ko' && !ko) {
        marker.textContent = '· EN';
        marker.title = 'Only in English';
        marker.hidden = false;
      } else {
        marker.textContent = '';
        marker.removeAttribute('title');
        marker.hidden = true;
      }
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
    });
  });
})();
