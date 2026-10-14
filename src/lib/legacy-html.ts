import { createHighlighter, bundledLanguages } from 'shiki';
import { autop } from '@wordpress/autop';

let highlighter: ReturnType<typeof createHighlighter> | undefined;
const entities: Record<string, string> = { amp: '&', lt: '<', gt: '>', quot: '"', '#x27': "'" };
const decode = (text: string) => text.replace(/&(amp|lt|gt|quot|#x27);/g, (_, entity: string) => entities[entity]);

// Classic WordPress posts rely on wpautop for paragraphs and line breaks.
// Block editor content already contains its own formatting; neither goes through Markdown.
export async function legacyHtml(body: string, autoParagraphs = true) {
  const formatted = autoParagraphs ? autop(body) : body;
  const pattern = /<pre class="legacy-code"><code class="language-([\w+-]+)">([\s\S]*?)<\/code><\/pre>/g;
  const matches = [...formatted.matchAll(pattern)];
  if (!matches.length) return formatted;
  highlighter ??= createHighlighter({ themes: ['github-light', 'github-dark'], langs: [] });
  const syntax = await highlighter;
  const replacements: string[] = [];
  for (const match of matches) {
    const language = match[1] as keyof typeof bundledLanguages;
    const loader = Object.hasOwn(bundledLanguages, language) ? bundledLanguages[language] : undefined;
    if (loader && !syntax.getLoadedLanguages().includes(language)) await syntax.loadLanguage(loader);
    replacements.push(syntax.codeToHtml(decode(match[2]), {
      lang: loader ? language : 'text',
      themes: { light: 'github-light', dark: 'github-dark' },
    }));
  }
  let index = 0;
  return formatted.replace(pattern, () => replacements[index++]);
}
