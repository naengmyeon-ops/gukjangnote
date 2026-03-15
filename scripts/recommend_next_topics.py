#!/usr/bin/env python3
import csv
import json
import pathlib
from collections import Counter, defaultdict

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
VIEWS_CSV = BASE_DIR / "data" / "views.csv"


def load_rows(path: pathlib.Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def recommend(rows):
    if not rows:
        return {
            "message": "조회수 데이터가 없어 기본 주제를 추천합니다.",
            "recommendations": [
                "외국인 수급으로 읽는 코스피 방향",
                "코스닥 강세 업종 체크",
                "환율과 국내증시 상관관계 쉽게 보기",
            ],
        }

    tag_score = Counter()
    title_words = Counter()

    for r in rows:
        views = int(r.get("views", 0) or 0)
        tags = [t.strip() for t in (r.get("tags") or "").split(",") if t.strip()]
        for t in tags:
            tag_score[t] += views

        words = [w.strip() for w in (r.get("title") or "").replace(":", " ").split() if len(w.strip()) >= 2]
        for w in words:
            title_words[w] += views

    top_tags = [t for t, _ in tag_score.most_common(5)]
    top_words = [w for w, _ in title_words.most_common(5)]

    recs = []
    if top_tags:
        recs.append(f"{top_tags[0]} 중심으로 보는 이번 주 시장 포인트")
    if len(top_tags) > 1:
        recs.append(f"{top_tags[0]}·{top_tags[1]} 같이 보면 보이는 매매 힌트")
    if top_words:
        recs.append(f"독자 반응 높은 키워드 '{top_words[0]}'로 정리한 오늘 장 요약")

    recs += [
        "개인투자자 관점에서 본 오늘 수급의 의미",
        "내일 장 시작 전 체크할 숫자 3개",
    ]

    return {
        "message": "조회수 상위 태그/제목 키워드를 반영해 주제를 추천했습니다.",
        "top_tags": top_tags,
        "top_words": top_words,
        "recommendations": recs[:5],
    }


def main():
    rows = load_rows(VIEWS_CSV)
    print(json.dumps(recommend(rows), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
