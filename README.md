# 오늘의 국장노트

한국 주식시장(코스피/코스닥) 데일리 블로그 자동 운영 템플릿입니다.

## 구성

- `scripts/generate_daily_post.py`  
  오늘 시장 데이터 + 뉴스 헤드라인을 바탕으로 주제 후보/게시글 초안 생성
- `scripts/recommend_next_topics.py`  
  조회수(`data/views.csv`) 기반 다음 주제 추천
- `scripts/publish_to_wordpress.py`  
  최신 글을 워드프레스 REST API로 발행/임시저장
- `scripts/sync_posts_to_pages.py`  
  생성된 글을 GitHub Pages(Jekyll)용 `_posts`로 동기화
- `posts/`  
  생성된 마크다운 글 저장 경로
- `data/views.csv`  
  조회수 로그(수동/자동 수집)

## 실행

```bash
python3 scripts/generate_daily_post.py
python3 scripts/recommend_next_topics.py
python3 scripts/publish_to_wordpress.py
python3 scripts/sync_posts_to_pages.py
```

## 무료 운영: GitHub Pages (추천)

1. GitHub에서 새 저장소 생성 (예: `gukjangnote`)
2. 이 프로젝트를 푸시
3. 저장소 설정 > Pages > Source: **GitHub Actions** 선택
4. 글 생성 후 동기화 실행:

```bash
python3 scripts/generate_daily_post.py
python3 scripts/sync_posts_to_pages.py
git add .
git commit -m "chore: publish daily post"
git push
```

- 배포 워크플로: `.github/workflows/pages.yml`
- 블로그 소스: `site/`

## 워드프레스 발행 연결 (선택)

1. `.env.example`를 `.env`로 복사 후 값 입력
2. 워드프레스 사용자에서 Application Password 생성
3. 아래 실행

```bash
cd /Users/sean/.openclaw/workspace/kr-stock-blog
cp .env.example .env
python3 scripts/publish_to_wordpress.py
```

## 조회수 파일 형식

`data/views.csv`

```csv
post_date,title,slug,views,tags
2026-03-15,외국인 수급이 코스피에 미치는 영향,2026-03-15-foreign-flow,1240,"수급,외국인,코스피"
```

- `tags`는 쉼표로 구분
- 추천 엔진은 조회수 상위 태그/키워드를 기반으로 다음 주제를 제안

## 문체 원칙

`templates/style_guide.md` 참고.
