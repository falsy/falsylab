import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

const root = new URL('../', import.meta.url);
const fallback = readFileSync(new URL('dist/404.html', root), 'utf8');
const entry = readFileSync(new URL('dist/tracker/index.html', root), 'utf8');
const scripts = (html) => [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map((match) => match[1]);
const redirect = scripts(fallback).find((script) => script.includes("entry.searchParams.set('route'"));
const restore = scripts(entry).find((script) => script.includes('window.history.replaceState'));
assert(redirect && restore, 'Build the tracker page and 404 route handler before testing.');

function execute(script, address) {
  const url = new URL(address);
  let navigation;
  let restored;
  const window = {
    location: { origin: url.origin, pathname: url.pathname, search: url.search, hash: url.hash,
      replace: (target) => { navigation = target; } },
    history: { replaceState: (_state, _title, target) => { restored = target; } },
  };
  runInNewContext(script, { window, URL, URLSearchParams }, { timeout: 100 });
  return { navigation, restored };
}

const carrier = '2de91044-1fda-11ef-8884-0a8cb08d3aea';
for (const suffix of ['', '/', '?source=whale#result']) {
  test(`the original popup URL survives the Pages fallback: ${suffix || 'no trailing slash'}`, () => {
    const original = `/tracker/${carrier}/1234567890${suffix}`;
    const { navigation } = execute(redirect, `https://falsy.me${original}`);
    assert.equal(new URL(navigation).pathname, '/tracker/');
    assert.equal(execute(restore, navigation).restored, original);
  });
}

test('normal missing blog pages keep their 404 page', () => {
  for (const path of ['/missing-post/', '/tracker-other/a/b', '/about/']) {
    assert.equal(execute(redirect, `https://falsy.me${path}`).navigation, undefined);
  }
});

test('direct tracker entry needs no URL restoration', () => {
  assert.equal(execute(restore, 'https://falsy.me/tracker/').restored, undefined);
});

test('restoration rejects external URLs and unrelated paths', () => {
  for (const route of ['https://example.com/tracker/a/b', '//example.com/tracker/a/b',
    '/about/', '/tracker/../about/', '/tracker-other/a/b', 'javascript:alert(1)']) {
    const url = new URL('https://falsy.me/tracker/');
    url.searchParams.set('route', route);
    assert.equal(execute(restore, url.href).restored, undefined);
  }
});

test('the original self-contained tracker bundle is used', () => {
  for (const extension of ['js', 'css']) {
    const filename = `tracker/assets/tracker-v1.0.10.${extension}`;
    assert(entry.includes(`/${filename}`));
    assert.deepEqual(readFileSync(new URL(`dist/${filename}`, root)), readFileSync(new URL(`public/${filename}`, root)));
  }
  assert(entry.indexOf('window.history.replaceState') < entry.indexOf('type="module"'));
  assert(entry.includes('<div id="root"></div>'));
});
