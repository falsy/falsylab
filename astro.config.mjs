import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://falsy.me',
  output: 'static',
  trailingSlash: 'ignore',
  devToolbar: { enabled: false },
  markdown: {
    shikiConfig: {
      themes: { light: 'github-light', dark: 'github-dark' },
      wrap: false,
    },
  },
});
