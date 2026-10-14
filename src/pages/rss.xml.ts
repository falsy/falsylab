import type { APIRoute } from 'astro';
import { rssXml } from '../lib/rss';

export const GET: APIRoute = async ({ site }) => {
  return new Response(await rssXml(site), { headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' } });
};
