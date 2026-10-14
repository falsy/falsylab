import { writeFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const args = process.argv.slice(2);
const title = args[0];
const option = (name) => { const index = args.indexOf(name); return index >= 0 ? args[index + 1] : undefined; };
if (!title || title.startsWith('--')) {
  console.error('Usage: npm run new -- "글 제목" --slug my-post [--category programming]');
  process.exit(1);
}
const slug = option('--slug') ?? title.normalize('NFC').toLowerCase().trim().replace(/[^\p{L}\p{N}\s-]/gu, '').replace(/\s+/g, '-');
const category = option('--category') ?? 'programming';
if (!slug || !/^[\p{L}\p{N}-]+$/u.test(slug) || !['programming', 'project', 'blog', 'essay', 'other'].includes(category)) {
  console.error('Use a slug containing letters, numbers, and hyphens, and a valid category.');
  process.exit(1);
}
const date = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Seoul' }).format(new Date());
const folder = resolve('src/content/posts');
await mkdir(folder, { recursive: true });
const path = resolve(folder, `${date}-${slug}.md`);
await writeFile(path, `---\ntitle: ${JSON.stringify(title)}\ndescription: ""\nslug: ${JSON.stringify(slug)}\ndate: "${date}T00:00:00+09:00"\ncategories: [${JSON.stringify(category)}]\ntags: []\ndraft: true\n---\n\n여기에 글을 작성하세요.\n`, { flag: 'wx' });
console.log(`Created ${path}\nSet draft: false when ready to publish.`);
