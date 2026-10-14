# 폴시랩

워드프레스 블로그를 Astro 정적 사이트로 옮긴 프로젝트입니다. `main` 브랜치에 푸시하면 GitHub Actions가 검증과 빌드 후 GitHub Pages에 배포합니다. 글은 Markdown 파일로 관리합니다.

## 로컬 실행

Node.js 24 LTS를 권장합니다. Astro의 최소 요구 버전은 Node.js 22.12입니다.

```bash
npm ci
npm run dev
```

터미널에 표시되는 `http://127.0.0.1:4321/`에서 확인합니다.

```bash
npm run check
npm run build
npm run preview
```

`dist/`에는 배포할 HTML, CSS, JavaScript와 이미지가 생성됩니다.

## 새 글 작성

```bash
npm run new -- "글 제목" --slug my-new-post --category programming
```

`src/content/posts/날짜-my-new-post.md` 파일을 생성합니다. 처음에는 `draft: true`이므로 공개 목록, RSS, 사이트맵과 배포 파일에 포함되지 않습니다. 아래와 같이 작성하고 준비가 되면 `draft: false`로 바꿉니다.

```markdown
---
title: "글 제목"
description: "목록과 검색 결과에 표시할 짧은 설명"
slug: "my-new-post"
date: "2026-10-14T12:00:00+09:00"
categories: ["programming"]
tags: ["JavaScript", "Astro"]
draft: false
---

여기에 Markdown으로 본문을 작성합니다.
```

- 글 주소는 `https://falsy.me/my-new-post/`가 됩니다. 공개 후 `slug`를 유지하면 기존 링크와 댓글 연결이 유지됩니다.
- 카테고리는 `programming`, `project`, `blog`, `essay`, `other`를 사용합니다.
- 이미지는 `public/images/`에 넣고 `![이미지 설명](/images/example.png)`으로 참조합니다.
- 목록용 이미지가 필요한 글에는 `image: "/images/example.png"`를 추가합니다.
- 본문에 코드 펜스를 사용하면 빌드할 때 구문 강조를 적용합니다.

검증한 뒤 평소처럼 커밋하고 푸시합니다.

```bash
npm run check
npm run build
git add .
git commit -m "새 글 작성"
git push origin main
```

## 워드프레스에서 가져온 글

공개 글 187개는 `src/content/posts/`에 있습니다. 파일명은 원래 작성일과 WordPress ID이며, 주소는 frontmatter의 `slug`와 `originalPath`에 저장되어 있습니다.

기존 글은 레이아웃, 표, 이미지 배치와 코드 예제를 보존하기 위해 Markdown 파일 안에 HTML 본문을 유지했습니다. 클래식 에디터 글은 WordPress의 공식 `@wordpress/autop` 패키지로 출력 시 줄바꿈과 문단을 복원합니다. 블록 에디터 글은 `wordpressAutoParagraphs: false`로 기존 HTML을 그대로 출력합니다. 새 글은 일반 Markdown으로 작성하면 됩니다. `originalPath`는 기존 URL의 인코딩까지 보존하기 위한 값이므로 기존 글 수정 시 유지합니다.

예전 블로그 주소인 `lab.falsy.me`가 들어 있던 이미지와 내부 글 링크도 현재 사이트의 내부 경로로 연결했습니다. 과거 설명과 명령어·서버 설정 등 코드 예제 안의 도메인은 원문 그대로 유지합니다.

About 페이지는 `src/content/pages/about.md`에서 수정합니다. 홈, Programming, Project, Blog, Essay 페이지는 공개 글의 카테고리로 자동 생성합니다. 태그 페이지와 RSS(`/rss.xml`, 기존 `/feed/` 경로), 사이트맵도 자동 생성됩니다.

기존 테마의 CSS, 폰트와 파비콘은 `public/theme/`에 있습니다. 추가 스타일은 `src/styles/site.css`에서 관리합니다. 라이트/다크 모드, Google Analytics와 기존 Utterances 저장소(`falsy/falsylab-theme`) 설정을 유지했습니다. 워드프레스 댓글 58개는 기존 글 하단의 접을 수 있는 영역에서 읽을 수 있습니다. 댓글 작성자의 이메일과 IP 주소는 가져오지 않았습니다.

## 기존 예제 데모

Select, Placeholder, Drag Slider, SVG 데모는 `public/preview/`에 있습니다. 기존 jQuery 1.10.2와 필요한 이미지도 함께 저장해 사용합니다.

PHP GD 예제 두 개는 입력값 없이 고정된 이미지를 출력하므로, EC2에서 실제 출력된 PNG를 `public/preview/gd/image-result.png`, `image2-result.png`로 저장했습니다. 글의 데모 링크는 이 이미지로 연결되며 기존 PHP 예제 코드는 그대로 유지합니다. 예전 `/preview/gd/image.php`, `image2.php` 주소에는 이미지로 이동하는 정적 페이지를 두었습니다.

다운로드한 원본은 `backups/preview/`에 보관합니다. 프로젝트 루트의 `preview/`와 `public/preview/`에 같은 경로의 파일이 있으면 Astro 개발 서버에서 브라우저 요청이 404가 될 수 있어 분리했습니다. 루트에 처음 다운로드한 `preview/`는 가져오기 명령이 `backups/preview/`로 옮깁니다.

원본을 다시 복사하려면 다음 명령을 사용합니다. PHP 원본은 배포하지 않으며 결과 이미지와 jQuery는 `public/preview/`에 유지합니다.

```bash
npm run import:preview
```

## 최초 GitHub Pages 연결

1. [저장소 Pages 설정](https://github.com/falsy/falsylab/settings/pages)에서 **Source → GitHub Actions**를 선택합니다.
2. 저장소의 Pages 설정에서 **Custom domain → `falsy.me`**를 저장합니다.
3. 소스를 `main`에 푸시하고 Actions에서 **Deploy to GitHub Pages**가 성공하는지 확인합니다.
4. 새 사이트를 확인한 뒤 DNS의 `falsy.me` A 레코드를 GitHub Pages의 아래 네 주소로 변경합니다.
5. DNS 확인과 인증서 발급이 끝나면 Pages 설정에서 **Enforce HTTPS**를 켭니다.

| 레코드 | 이름 | 값 |
| --- | --- | --- |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |

GitHub Actions로 배포할 때 도메인은 **저장소의 Pages 설정에서** 지정해야 합니다. `public/CNAME`만 추가해서는 도메인이 설정되지 않습니다. 이 프로젝트는 `https://falsy.me`의 루트 경로로 배포하도록 구성되어 있으므로, 도메인을 연결하지 않은 `https://falsy.github.io/falsylab/` 경로에서 사용하려면 `base`와 내부 링크 설정을 별도로 바꿔야 합니다.

DNS 제공업체에 `www`를 사용한다면 CNAME을 `falsy.github.io`로 설정합니다. `lab.falsy.me`를 참조하던 기존 글의 이미지와 내부 링크는 현재 사이트로 이전되어 블로그에서 더 이상 이 서브도메인에 의존하지 않습니다. 현재 이 서브도메인에 다른 서비스를 운영 중이라면 해당 DNS 설정은 별도로 관리합니다.

공식 문서: [Astro의 GitHub Pages 배포](https://docs.astro.build/en/guides/deploy/github/), [GitHub의 사용자 도메인 설정](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).

## 내보내기 재실행

원본 XML, 다운로드한 `uploads/`와 `backups/`(처음 다운로드한 `preview/` 포함), `.pem` 키와 로컬 이관 보고서는 `.gitignore`로 제외됩니다. 공개 글에서 실제로 사용하는 이미지와 테마 로고만 `public/wp-content/uploads/`에 복사되어 배포됩니다.

```bash
npm run import:wordpress -- WordPress.2026-10-14.xml
```

기존 Markdown 파일은 덮어쓰지 않습니다. 원본으로 다시 덮어써야 할 때만 `--overwrite`를 명시합니다. 원본 테마는 기본적으로 `../falsy.me`에서 읽으며 `--theme 경로`로 변경할 수 있습니다. 가져오기 작업은 로컬에서 한 번 수행하고, CI는 이미 변환된 Markdown과 이미지를 빌드합니다.

이번 XML의 제어문자 9개를 메모리에서 제거했고, 비공개 글 3개와 페이지 1개는 제외했습니다. `[al]` 링크 320개와 기존 코드 블록 1,176개를 변환했습니다. 상세 결과는 로컬 `migration-report.json`에서 확인할 수 있습니다.

공개 글 `DocumentDB #2 DocumentDB - Lambda 연결하기 (use Nodejs, Mongoose)`가 참조하는 `2021/06/1.png`는 다운로드 폴더에 없고, 원래 사이트에서도 404를 반환합니다. 이 이미지가 확보되면 같은 경로의 `public/wp-content/uploads/2021/06/1.png`에 추가하면 됩니다.
