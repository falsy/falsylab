import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const common = {
  title: z.string(),
  description: z.string().default(''),
  slug: z.string().min(1),
  originalPath: z.string().optional(),
  date: z.coerce.date(),
  updated: z.coerce.date().optional(),
  wordpressId: z.number().optional(),
  wordpressAutoParagraphs: z.boolean().default(true),
  draft: z.boolean().default(false),
};

export const collections = {
  posts: defineCollection({
    loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
    schema: z.object({
      ...common,
      categories: z.array(z.enum(['programming', 'project', 'blog', 'essay', 'other'])).default(['programming']),
      tags: z.array(z.string()).default([]),
      image: z.string().optional(),
    }),
  }),
  pages: defineCollection({
    loader: glob({ pattern: '**/*.md', base: './src/content/pages' }),
    schema: z.object(common),
  }),
};
