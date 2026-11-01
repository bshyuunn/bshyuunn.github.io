const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const scripts = path.join(__dirname, '..', 'assets', 'js');

test('index shows only articles in the selected language', () => {
  const storage = new Map();
  const buttons = ['en', 'ko'].map(lang => ({
    lang,
    attrs: {},
    getAttribute(name) { return name === 'data-lang' ? lang : this.attrs[name]; },
    setAttribute(name, value) { this.attrs[name] = value; },
    addEventListener(event, callback) { this.click = callback; },
  }));
  function row(en, ko) {
    const title = {};
    const marker = en && ko ? { textContent: '· KO', title: 'Also in Korean' } : null;
    return {
      attrs: {
        'data-href-en': en ? '/en/' : '', 'data-href-ko': ko ? '/ko/' : '',
        'data-title-en': en, 'data-title-ko': ko,
      },
      title, marker,
      getAttribute(name) { return this.attrs[name]; },
      querySelector(selector) { return selector === '.t' ? title : marker; },
    };
  }
  const bilingual = row('English title', '한국어 제목');
  const englishOnly = row('English only', '');
  const koreanOnly = row('', '한국어 전용');
  const document = {
    querySelectorAll(selector) { return selector.includes('post-row') ? [bilingual, englishOnly, koreanOnly] : buttons; },
  };
  const localStorage = {
    getItem(key) { return storage.get(key); },
    setItem(key, value) { storage.set(key, value); },
  };
  const location = { search: '?lang=ko', pathname: '/blog/', hash: '' };
  const history = { replaceState(state, title, url) { location.search = url.split('?')[1] ? '?' + url.split('?')[1] : ''; } };
  vm.runInNewContext(fs.readFileSync(path.join(scripts, 'blog-lang.js'), 'utf8'), {
    document, localStorage, location, history, URLSearchParams,
  });
  assert.equal(bilingual.href, '/ko/');
  assert.equal(bilingual.title.textContent, '한국어 제목');
  assert.equal(bilingual.title.lang, 'ko');
  assert.equal(bilingual.hidden, false);
  assert.equal(bilingual.marker.textContent, '· EN');
  assert.equal(bilingual.marker.title, 'Also in English');
  assert.equal(bilingual.marker.hidden, false);
  assert.equal(englishOnly.hidden, true);
  assert.equal(koreanOnly.hidden, false);
  assert.equal(storage.get('lang'), 'ko');
  buttons[0].click();
  assert.equal(bilingual.href, '/en/');
  assert.equal(bilingual.marker.textContent, '· KO');
  assert.equal(bilingual.marker.title, 'Also in Korean');
  assert.equal(bilingual.marker.hidden, false);
  assert.equal(englishOnly.hidden, false);
  assert.equal(koreanOnly.hidden, true);
  assert.equal(storage.get('lang'), 'en');
  assert.equal(location.search, '?lang=en');
});

test('switch maps section 2.2 to the fourth heading and scrolls to it', () => {
  const headings = [250, 100, 70, 40, 400, 600].map(top => ({
    getBoundingClientRect() { return { top }; },
    scrollIntoView() { this.scrolled = true; },
  }));
  const prose = { querySelectorAll() { return headings; } };
  let click;
  const link = {
    href: '/ko/blog/post/',
    addEventListener(event, callback) { click = callback; },
  };
  const document = {
    querySelector(selector) {
      if (selector === '.prose') return prose;
      if (selector.includes('lang-switch')) return link;
      return null;
    },
  };
  const location = { hash: '', href: '/blog/post/' };
  const window = { innerHeight: 600, addEventListener() {} };
  const source = fs.readFileSync(path.join(scripts, 'toc.js'), 'utf8');
  vm.runInNewContext(source, { document, location, window });
  click({ preventDefault() {} });
  assert.equal(location.href, '/ko/blog/post/#sec-3');

  const loadEvents = [];
  vm.runInNewContext(source, {
    document, location: { hash: '#sec-3' },
    window: { innerHeight: 600, addEventListener(event, callback) { if (event === 'load') loadEvents.push(callback); } },
  });
  loadEvents.forEach(callback => callback());
  assert.equal(headings[3].scrolled, true);
});

test('switching languages before the first heading uses the clean post URL', () => {
  const prose = { querySelectorAll() { return [{ getBoundingClientRect() { return { top: 300 }; } }]; } };
  let click;
  const link = {
    href: '/ko/blog/post/',
    addEventListener(event, callback) { click = callback; },
  };
  const document = {
    querySelector(selector) {
      if (selector === '.prose') return prose;
      if (selector.includes('lang-switch')) return link;
      return null;
    },
  };
  const location = { hash: '', href: '/blog/post/' };
  vm.runInNewContext(fs.readFileSync(path.join(scripts, 'toc.js'), 'utf8'), {
    document, location, window: { innerHeight: 600, addEventListener() {} },
  });
  click({ preventDefault() {} });
  assert.equal(location.href, '/ko/blog/post/');
});
