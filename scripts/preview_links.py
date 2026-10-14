"""Resolve migrated preview links without changing code examples."""

import html
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
LOCAL_HOSTS = {"falsy.me", "www.falsy.me", "cheolguso.com", "www.cheolguso.com"}
IMAGE_RESULTS = json.loads((ROOT / "scripts/preview-images.json").read_text(encoding="utf-8"))


def local_preview_url(url):
    try:
        parsed = urlsplit(html.unescape(url))
    except ValueError:
        return url
    if parsed.hostname and parsed.hostname not in LOCAL_HOSTS:
        return url
    path = unquote(parsed.path)
    if not path.startswith("/preview/"):
        return url
    destination = IMAGE_RESULTS.get(path, path)
    public = ROOT / "public"
    target = (public / destination.lstrip("/")).resolve()
    if not target.is_relative_to(public.resolve()) or not target.is_file():
        return url
    return destination + ("?" + parsed.query if parsed.query else "") + ("#" + parsed.fragment if parsed.fragment else "")


def rewrite_preview_links(body):
    parts = re.split(r"(<pre\b[\s\S]*?</pre>)", body, flags=re.I)
    for index, part in enumerate(parts):
        if re.match(r"<pre\b", part, flags=re.I):
            continue
        parts[index] = re.sub(
            r"https?://(?:www\.)?(?:falsy\.me|cheolguso\.com)/preview/[^\s<>\"']+",
            lambda match: local_preview_url(match.group(0)),
            part,
        )
    return "".join(parts)
