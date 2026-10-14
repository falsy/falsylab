"""Import public WXR content, keeping private backups and unreferenced uploads local."""

import argparse
import html
import json
import re
import shutil
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from preview_links import local_preview_url

ROOT = Path(__file__).resolve().parent.parent
NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}
LOCAL_HOSTS = {"falsy.me", "www.falsy.me", "cheolguso.com", "www.cheolguso.com"}
MEDIA_PREFIX = "/wp-content/uploads/"


def value(node, key):
    return node.findtext(key, default="", namespaces=NS)


def plain(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        for key, val in attrs:
            if not val:
                continue
            if key in ("src", "href", "poster", "data-src"):
                self.urls.add(val)
            elif key == "srcset":
                self.urls.update(part.strip().split()[0] for part in val.split(",") if part.strip())
            elif key == "style":
                self.urls.update(re.findall(r"url\(['\"]?([^)'\"]+)", val))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", nargs="?", type=Path)
    parser.add_argument("--uploads", type=Path, default=ROOT / "uploads")
    parser.add_argument("--theme", type=Path, default=ROOT.parent / "falsy.me")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing imported Markdown files")
    args = parser.parse_args()
    exports = sorted(ROOT.glob("WordPress*.xml"))
    xml_path = args.xml or (exports[-1] if exports else None)
    if not xml_path or not xml_path.is_file():
        parser.error("Provide a WordPress XML export path.")
    raw = xml_path.read_text(encoding="utf-8-sig")
    clean, control_count = re.subn(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]", "", raw)
    channel = ET.fromstring(clean).find("channel")
    items = channel.findall("item")
    public = [item for item in items if value(item, "wp:status") == "publish"
              and value(item, "wp:post_type") in ("post", "page")]
    routes = {unquote(urlsplit(value(item, "link")).path) for item in public}
    attachments = {value(item, "wp:post_id"): value(item, "wp:attachment_url")
                   for item in items if value(item, "wp:post_type") == "attachment"}
    media = set()
    missing = {}
    tags = {}
    comments = {}
    report = {"public_posts": 0, "public_pages": 0, "converted_links": 0,
              "converted_code_blocks": 0, "control_characters_removed": control_count,
              "skipped_private_items": sum(value(i, "wp:status") == "private" for i in items)}

    def media_path(url):
        try:
            parsed = urlsplit(html.unescape(url))
        except ValueError:
            return None
        if parsed.hostname and parsed.hostname not in LOCAL_HOSTS:
            return None
        path = unquote(parsed.path)
        if not path.startswith(MEDIA_PREFIX):
            return None
        relative = Path(path[len(MEDIA_PREFIX):])
        source = (args.uploads / relative).resolve()
        if not source.is_relative_to(args.uploads.resolve()):
            raise ValueError(f"Unsafe media path: {relative}")
        return relative

    def register_media(url, context):
        relative = media_path(url)
        if relative is None:
            return
        if relative.suffix.lower() in (".php", ".log", ".pem", ".json"):
            raise ValueError(f"Unexpected non-media file referenced by {context}: {relative}")
        source = args.uploads / relative
        if source.is_file():
            media.add(relative)
        else:
            missing.setdefault(str(relative), set()).add(context)

    def local_url(url):
        try:
            parsed = urlsplit(html.unescape(url))
        except ValueError:
            return url
        if parsed.hostname not in LOCAL_HOSTS:
            return url
        if unquote(parsed.path).startswith("/preview/"):
            return local_preview_url(url)
        if media_path(url) is not None or unquote(parsed.path) in routes:
            return parsed.path + ("?" + parsed.query if parsed.query else "") + ("#" + parsed.fragment if parsed.fragment else "")
        return url

    def convert(body, context):
        code_blocks = []

        def code(match):
            attrs, content = match.groups()
            lang = re.search(r"(?:lang[:=]|language-)[\"']?([\w+-]+)", attrs)
            language = lang.group(1).lower() if lang else "text"
            language = {"xhtml": "html", "js": "javascript", "sh": "bash"}.get(language, language)
            content = re.sub(r"^\s*<code\b[^>]*>|</code>\s*$", "", content)
            block = '<pre class="legacy-code"><code class="language-' + language + '">' + html.escape(html.unescape(content.strip("\n"))) + "</code></pre>"
            code_blocks.append(block)
            report["converted_code_blocks"] += 1
            return f"<!--FALSY_CODE_{len(code_blocks) - 1}-->"

        body = re.sub(r"<pre\b([^>]*)>([\s\S]*?)</pre>", code, body, flags=re.I)
        body = re.sub(r"<!--\s*/?wp:[\s\S]*?-->", "", body)

        def link(match):
            options, url = match.groups()
            target = "_self" if re.search(r"self=['\"]true['\"]", options) else "_blank"
            url = html.unescape(url.strip())
            report["converted_links"] += 1
            return '<a href="' + html.escape(local_url(url), quote=True) + '" target="' + target + '" rel="noopener noreferrer">' + html.escape(url) + "</a>"

        body = re.sub(r"\[al([^\]]*)\]([\s\S]*?)\[/al\]", link, body)
        # Rewrite actual URLs outside code examples; old domain media now use local files.
        body = re.sub(r"https?://(?:www\.)?(?:falsy\.me|cheolguso\.com)/[^\s<>\"']+", lambda m: local_url(m.group(0)), body)
        assets = Assets()
        assets.feed(body)
        for url in assets.urls:
            register_media(url, context)
        for index, block in enumerate(code_blocks):
            body = body.replace(f"<!--FALSY_CODE_{index}-->", block)
        return body.strip() + "\n"

    def write_markdown(path, metadata, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not args.overwrite:
            return
        frontmatter = "\n".join(key + ": " + json.dumps(val, ensure_ascii=False) for key, val in metadata.items())
        path.write_text("---\n" + frontmatter + "\n---\n\n" + body, encoding="utf-8")

    for item in public:
        kind = value(item, "wp:post_type")
        identifier = int(value(item, "wp:post_id"))
        original_path = urlsplit(value(item, "link")).path
        slug = unquote(original_path).strip("/")
        title = plain(value(item, "title"))
        source_body = value(item, "content:encoded")
        body = convert(source_body, title)
        categories = [cat.attrib.get("nicename", "") for cat in item.findall("category") if cat.attrib.get("domain") == "category"]
        tag_names = []
        for tag in item.findall("category"):
            if tag.attrib.get("domain") == "post_tag":
                name = tag.text or ""
                tag_names.append(name)
                tags[name] = unquote(tag.attrib.get("nicename", ""))
        metadata = {
            "title": title,
            "description": plain(value(item, "excerpt:encoded")),
            "slug": slug,
            "originalPath": original_path,
            "date": value(item, "wp:post_date").replace(" ", "T") + "+09:00",
            "updated": value(item, "wp:post_modified").replace(" ", "T") + "+09:00",
            "wordpressId": identifier,
            "draft": False,
        }
        if "<!-- wp:" in source_body:
            # WordPress disables wpautop for block editor content.
            metadata["wordpressAutoParagraphs"] = False
        if kind == "post":
            metadata.update({"categories": categories, "tags": tag_names})
            for meta in item.findall("wp:postmeta", NS):
                if value(meta, "wp:meta_key") != "_thumbnail_id":
                    continue
                url = attachments.get(value(meta, "wp:meta_value"), "")
                relative = media_path(url)
                if relative and (args.uploads / relative).is_file():
                    # Use WordPress's existing smaller thumbnail for listing cards.
                    variants = [file for file in sorted((args.uploads / relative.parent).glob(relative.stem + "-300x*" + relative.suffix))
                                if file.is_file() and file.stat().st_size > 0]
                    if variants:
                        relative = variants[0].relative_to(args.uploads)
                    metadata["image"] = MEDIA_PREFIX + relative.as_posix()
                    register_media(metadata["image"], title + " (thumbnail)")
            date = metadata["date"][:10]
            write_markdown(ROOT / "src/content/posts" / f"{date}-{identifier}.md", metadata, body)
            report["public_posts"] += 1
            visible_comments = []
            for comment in item.findall("wp:comment", NS):
                if value(comment, "wp:comment_approved") != "1":
                    continue
                visible_comments.append({
                    "id": int(value(comment, "wp:comment_id")),
                    "parent": int(value(comment, "wp:comment_parent") or "0"),
                    "author": value(comment, "wp:comment_author"),
                    "date": value(comment, "wp:comment_date")[:10],
                    "content": value(comment, "wp:comment_content"),
                })
            if visible_comments:
                comments[str(identifier)] = visible_comments
        elif slug == "about":
            write_markdown(ROOT / "src/content/pages/about.md", metadata, body)
        if kind == "page":
            report["public_pages"] += 1

    # Logo and social preview images are referenced by the original PHP theme.
    for url in [MEDIA_PREFIX + "2018/11/logo.png", MEDIA_PREFIX + "2020/07/falsylab.jpg"]:
        register_media(url, "theme")
    destination = ROOT / "public/wp-content/uploads"
    for relative in sorted(media):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.uploads / relative, target)
    if not args.theme.is_dir():
        parser.error("The WordPress theme folder was not found; provide --theme.")
    for relative in ["css/style.css", "css/responsive_style.css", "img/favicon_v4.ico", "LICENSE",
                     "js/webfonts/390C5D_0_0.woff2"]:
        target = ROOT / "public/theme" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.theme / relative, target)
    data = ROOT / "src/data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "tags.json").write_text(json.dumps(tags, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (data / "wordpress-comments.json").write_text(json.dumps(comments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["public_comments"] = sum(len(entries) for entries in comments.values())
    report["copied_media_files"] = len(media)
    report["missing_media"] = [{"path": path, "referenced_by": sorted(contexts)} for path, contexts in sorted(missing.items())]
    (ROOT / "migration-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
