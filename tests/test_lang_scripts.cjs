const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const scripts = path.join(__dirname, '..', 'assets', 'js');

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
