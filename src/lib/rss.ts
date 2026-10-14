import { getPosts, href, escapeXml } from './content';

export async function rssXml(site: URL | undefined) {
  const posts = await getPosts();
  const items = posts.map((post) => {
    const url = new URL(href(post), site).href;
    return `<item><title>${escapeXml(post.data.title)}</title><link>${escapeXml(url)}</link><guid isPermaLink="true">${escapeXml(url)}</guid><pubDate>${post.data.date.toUTCString()}</pubDate><description>${escapeXml(post.data.description || post.data.title)}</description></item>`;
  }).join('');
  return `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>폴시랩</title><link>https://falsy.me/</link><description>개발과 프로젝트, 그리고 일상의 기록.</description><language>ko</language><atom:link href="https://falsy.me/rss.xml" rel="self" type="application/rss+xml"/>${items}</channel></rss>`;
}
