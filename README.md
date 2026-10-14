# 폴시랩

[falsy.me](https://falsy.me) 블로그의 소스 코드입니다. Astro와 Markdown을 사용하며, `main` 브랜치에 푸시하면 GitHub Pages로 자동 배포됩니다.

## 로컬 실행

Node.js 24 LTS를 권장합니다.

```bash
npm ci
npm run dev
```

## 글 작성

```bash
npm run new -- "글 제목" --slug my-new-post --category programming
```

`src/content/posts/`에 생성된 파일을 작성하고, 공개할 때 `draft: false`로 변경합니다.
