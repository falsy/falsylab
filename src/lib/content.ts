import { getCollection, type CollectionEntry } from 'astro:content';
import originalTags from '../data/tags.json';

export const sections = [
  { slug: 'programming', name: 'Programming' },
  { slug: 'project', name: 'Project' },
  { slug: 'blog', name: 'Blog' },
  { slug: 'essay', name: 'Essay' },
] as const;

export type Post = CollectionEntry<'posts'>;
export const getPosts = async () => (await getCollection('posts', ({ data }) => !data.draft))
  .sort((a, b) => b.data.date.getTime() - a.data.date.getTime());
export const getPages = () => getCollection('pages', ({ data }) => !data.draft);

export function href(entry: CollectionEntry<'posts' | 'pages'>) {
  return entry.data.originalPath ?? `/${encodeURI(entry.data.slug)}/`;
}

export function dateLabel(date: Date) {
  return new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Seoul' }).format(date);
}

export function tagSlug(name: string) {
  const tags: Record<string, string> = originalTags;
  return tags[name] ?? name.normalize('NFC').toLowerCase().trim().replace(/\s+/g, '-');
}

export const tagHref = (name: string) => `/tag/${encodeURIComponent(tagSlug(name))}/`;

export function escapeXml(text: string) {
  return text.replace(/[<>&"']/g, (char) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' }[char]!));
}
