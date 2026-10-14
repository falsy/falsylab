"""Copy static preview demos and link fixed PHP image results saved from EC2."""

import argparse
import html
import shutil
from pathlib import Path

from preview_links import IMAGE_RESULTS, ROOT, rewrite_preview_links

STATIC_EXTENSIONS = {".html", ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ttf", ".woff", ".woff2"}
JQUERY_CDN = "//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"
JQUERY_LOCAL = "/preview/vendor/jquery-1.10.2.min.js"
BACKUP_SOURCE = ROOT / "backups/preview"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path,
                        default=ROOT / "preview" if (ROOT / "preview").is_dir() else BACKUP_SOURCE)
    args = parser.parse_args()
    if not args.source.is_dir():
        parser.error("The downloaded preview folder was not found.")
    public = ROOT / "public"
    for url in IMAGE_RESULTS.values():
        image = public / url.lstrip("/")
        if not image.is_file() or not image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            parser.error(f"Save the original PHP output as a PNG first: {image}")
    jquery = public / JQUERY_LOCAL.lstrip("/")
    if not jquery.is_file() or b"jQuery v1.10.2" not in jquery.read_bytes()[:150]:
        parser.error(f"The demos need the original jQuery 1.10.2 library: {jquery}")

    # Astro's dev route guard can reject /preview/... when the same file also
    # exists at the project root. Keep the downloaded originals off that path.
    if args.source.resolve() == (ROOT / "preview").resolve():
        if BACKUP_SOURCE.exists():
            parser.error("Both preview/ and backups/preview/ exist. Keep the originals in backups/preview/ before importing.")
        BACKUP_SOURCE.parent.mkdir(parents=True, exist_ok=True)
        args.source.rename(BACKUP_SOURCE)
        args.source = BACKUP_SOURCE
        print("Moved downloaded originals to backups/preview/ to avoid dev-server path conflicts.")

    copied = 0
    for source in sorted(args.source.rglob("*")):
        if not source.is_file() or source.suffix.lower() not in STATIC_EXTENSIONS:
            continue
        relative = source.relative_to(args.source)
        if any(part.startswith(".") for part in relative.parts):
            continue
        target = public / "preview" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() == ".html":
            target.write_text(source.read_text(encoding="utf-8").replace(JQUERY_CDN, JQUERY_LOCAL), encoding="utf-8")
        else:
            shutil.copy2(source, target)
        copied += 1

    # A directory index also lets old .php demo links reach the saved PNG on Pages.
    for old_url, image_url in IMAGE_RESULTS.items():
        target = public / old_url.lstrip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        escaped = html.escape(image_url, quote=True)
        target.write_text(
            '<!doctype html>\n<html lang="ko"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="robots" content="noindex">'
            f'<meta http-equiv="refresh" content="0; url={escaped}">'
            '<title>PHP GD 데모 이미지</title></head><body>'
            f'<a href="{escaped}"><img src="{escaped}" alt="PHP GD 데모 결과"></a>'
            '</body></html>\n',
            encoding="utf-8",
        )

    changed = 0
    for folder in (ROOT / "src/content/posts", ROOT / "src/content/pages"):
        for path in sorted(folder.glob("*.md")):
            original = path.read_text(encoding="utf-8")
            frontmatter = original.split("---", 2)
            if len(frontmatter) < 3 or "\nwordpressId:" not in frontmatter[1]:
                continue
            updated = rewrite_preview_links(original)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                changed += 1
    print(f"Copied {copied} demo assets; preserved {len(IMAGE_RESULTS)} PHP image results; updated {changed} posts/pages.")


if __name__ == "__main__":
    main()
