#!/usr/bin/env python3
import csv
import datetime as dt
import json
import pathlib
import random
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
POSTS_DIR = BASE_DIR / "posts"
DATA_DIR = BASE_DIR / "data"


def fetch_json(url: str, timeout: int = 10):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 OpenClawKRBlog/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_rss_titles(url: str, limit: int = 8):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 OpenClawKRBlog/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        xml = r.read().decode("utf-8", errors="ignore")
    root = ET.fromstring(xml)
    titles = []
    for item in root.findall("./channel/item"):
        title = item.findtext("title", default="").strip()
        title = re.sub(r"\s+", " ", title)
        if title:
            titles.append(title)
        if len(titles) >= limit:
            break
    return titles


def get_index_snapshot(symbol: str, name: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range=5d&interval=1d"
    data = fetch_json(url)
    result = data["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    closes = [c for c in quote["close"] if c is not None]
    if len(closes) < 2:
        return {"name": name, "close": None, "change_pct": None}
    close = closes[-1]
    prev = closes[-2]
    pct = (close - prev) / prev * 100
    return {"name": name, "close": close, "change_pct": pct}


def classify_market_tone(kospi_pct: float, kosdaq_pct: float):
    avg = (kospi_pct + kosdaq_pct) / 2
    if avg >= 1.0:
        return "강한 상승 분위기"
    if avg >= 0.2:
        return "완만한 상승 분위기"
    if avg <= -1.0:
        return "뚜렷한 하락 분위기"
    if avg <= -0.2:
        return "약세 우위 흐름"
    return "보합권 혼조 흐름"


def make_candidates(headlines, tone):
    base = [
        f"오늘 {tone}에서 개인투자자가 먼저 볼 체크포인트 3가지",
        "코스피·코스닥 흐름을 한눈에 보는 저녁 브리핑",
        "외국인 수급 한 줄 해석: 오늘 장에서 실제로 중요했던 것",
        "내일 장 전에 꼭 볼 변수: 환율·금리·수급",
    ]
    for h in headlines[:3]:
        clean = re.sub(r"\[.*?\]", "", h).strip()
        base.append(f"뉴스로 읽는 오늘 시장: {clean}")
    return base


def compose_post(date_str, idx_kospi, idx_kosdaq, headlines):
    tone = classify_market_tone(idx_kospi["change_pct"], idx_kosdaq["change_pct"])
    candidates = make_candidates(headlines, tone)
    selected = candidates[0]

    intro = (
        f"오늘 한국 증시는 **{tone}**이었습니다. "
        f"코스피는 {idx_kospi['change_pct']:+.2f}%, 코스닥은 {idx_kosdaq['change_pct']:+.2f}% 마감에 가까운 흐름을 보였어요."
    )

    key_points = [
        f"코스피: {idx_kospi['close']:.2f} ({idx_kospi['change_pct']:+.2f}%)",
        f"코스닥: {idx_kosdaq['close']:.2f} ({idx_kosdaq['change_pct']:+.2f}%)",
        "핵심: 지수 방향보다 수급 주도 업종이 어디인지 확인",
    ]

    checks = [
        "미국 증시/미국채 금리 야간 흐름",
        "원/달러 환율 갭 출발 여부",
        "외국인 선물 포지션 변화",
    ]

    md = []
    md.append(f"---\ntitle: \"{selected}\"\ndate: \"{date_str}\"\ncategory: \"daily\"\ntags: [\"코스피\", \"코스닥\", \"국내증시\"]\n---\n")
    md.append("## 한 줄 요약")
    md.append(intro)
    md.append("\n## 오늘 시장 핵심")
    for p in key_points:
        md.append(f"- {p}")
    md.append("\n## 오늘 많이 본 이슈")
    if headlines:
        for h in headlines[:5]:
            md.append(f"- {h}")
    else:
        md.append("- 주요 헤드라인 수집 실패: 수동 확인 필요")
    md.append("\n## 내일 체크포인트")
    for c in checks:
        md.append(f"- {c}")
    md.append("\n## 주제 후보 (내일 발행용)")
    for c in candidates[1:5]:
        md.append(f"- {c}")

    return "\n".join(md), selected, candidates


def main():
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now().date().isoformat()

    kospi = get_index_snapshot("^KS11", "KOSPI")
    kosdaq = get_index_snapshot("^KQ11", "KOSDAQ")

    q = urllib.parse.quote("코스피 코스닥 주식시장")
    news_url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    headlines = fetch_rss_titles(news_url, limit=8)

    post_md, title, candidates = compose_post(today, kospi, kosdaq, headlines)
    slug = re.sub(r"[^a-z0-9-]", "", re.sub(r"\s+", "-", title.lower()))[:64].strip("-")
    if len(slug) < 8:
        slug = "daily-market-brief"
    out_file = POSTS_DIR / f"{today}-{slug}.md"
    out_file.write_text(post_md, encoding="utf-8")

    summary = {
        "date": today,
        "title": title,
        "file": str(out_file),
        "kospi_change_pct": round(kospi["change_pct"], 2),
        "kosdaq_change_pct": round(kosdaq["change_pct"], 2),
        "topic_candidates": candidates[:5],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
