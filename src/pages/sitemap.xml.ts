import type { APIRoute } from 'astro';
import { getPosts, getPages, href, sections, tagHref, escapeXml } from '../lib/content';

export const GET: APIRoute = async ({ site }) => {
  const posts = await getPosts();
  const pages = await getPages();
  const tags = [...new Set(posts.flatMap((post) => post.data.tags))];
  const paths = [...new Set(['/', ...sections.map((section) => `/${section.slug}/`), ...tags.map(tagHref), ...posts.map(href), ...pages.map(href)])];
  const urls = paths.map((path) => `<url><loc>${escapeXml(new URL(path, site).href)}</loc></url>`).join('');
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
