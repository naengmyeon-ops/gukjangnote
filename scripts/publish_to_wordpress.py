#!/usr/bin/env python3
import base64
import json
import os
import pathlib
import re
import urllib.request
from datetime import datetime

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
POSTS_DIR = BASE_DIR / "posts"
ENV_FILE = BASE_DIR / ".env"


def load_env(path: pathlib.Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def parse_front_matter(md: str):
    if not md.startswith("---\n"):
        return {}, md
    end = md.find("\n---\n", 4)
    if end == -1:
        return {}, md
    fm_raw = md[4:end].strip().splitlines()
    body = md[end + 5 :].strip()
    meta = {}
    for line in fm_raw:
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, body


def md_to_html(md: str):
    html_lines = []
    for line in md.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("## "):
            html_lines.append(f"<h2>{s[3:].strip()}</h2>")
        elif s.startswith("- "):
            if not html_lines or not html_lines[-1].startswith("<ul>"):
                html_lines.append("<ul>")
            html_lines.append(f"<li>{s[2:].strip()}</li>")
        else:
            if html_lines and html_lines[-1] == "</ul>":
                pass
            html_lines.append(f"<p>{s}</p>")

    normalized = []
    in_ul = False
    for l in html_lines:
        if l == "<ul>":
            if in_ul:
                continue
            in_ul = True
            normalized.append(l)
        elif l.startswith("<li>"):
            if not in_ul:
                normalized.append("<ul>")
                in_ul = True
            normalized.append(l)
        else:
            if in_ul:
                normalized.append("</ul>")
                in_ul = False
            normalized.append(l)
    if in_ul:
        normalized.append("</ul>")
    return "\n".join(normalized)


def latest_post_file():
    files = sorted(POSTS_DIR.glob("*.md"))
    if not files:
        raise SystemExit("posts 디렉토리에 마크다운 파일이 없습니다.")
    return files[-1]


def publish_wp(title: str, content_html: str, status: str):
    wp_url = os.getenv("WP_URL", "").rstrip("/")
    username = os.getenv("WP_USERNAME", "")
    app_password = os.getenv("WP_APP_PASSWORD", "")

    if not (wp_url and username and app_password):
        raise SystemExit("WP_URL/WP_USERNAME/WP_APP_PASSWORD 설정이 필요합니다. (.env 확인)")

    endpoint = f"{wp_url}/wp-json/wp/v2/posts"
    payload = json.dumps({
        "title": title,
        "content": content_html,
        "status": status,
    }).encode("utf-8")

    token = base64.b64encode(f"{username}:{app_password}".encode("utf-8")).decode("ascii")

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "User-Agent": "OpenClaw-KRBlog/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.loads(r.read().decode("utf-8"))
    return res


def main():
    load_env(ENV_FILE)
    status = os.getenv("WP_STATUS", "draft")

    fp = latest_post_file()
    raw = fp.read_text(encoding="utf-8")
    meta, body = parse_front_matter(raw)
    title = meta.get("title") or fp.stem
    html = md_to_html(body)

    res = publish_wp(title, html, status)
    print(json.dumps({
        "ok": True,
        "local_file": str(fp),
        "wp_post_id": res.get("id"),
        "wp_link": res.get("link"),
        "status": res.get("status"),
        "published_at": datetime.now().isoformat(),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
