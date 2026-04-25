import os
import sys
from datetime import date

from scraper import scrape_keyword
from generator import generate_blog_post

OUTPUT_DIR = "outputs"


def _sanitize(keyword: str) -> str:
    """파일명으로 사용할 수 없는 문자를 언더스코어로 치환."""
    forbidden = r'\/:*?"<>|'
    result = "".join("_" if c in forbidden else c for c in keyword)
    return result.strip().replace(" ", "_")


def _get_keyword() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()
    kw = input("키워드를 입력하세요: ").strip()
    return kw


def main() -> None:
    keyword = _get_keyword()
    if not keyword:
        print("오류: 키워드가 비어 있습니다.")
        sys.exit(1)

    # 1단계: 데이터 수집
    print(f"\n[1/3] '{keyword}' 관련 블로그 수집 중...")
    source_text = scrape_keyword(keyword)

    if not source_text.strip() or source_text.startswith(f"[{keyword}] 검색 결과 없음"):
        print("수집된 데이터가 없습니다. 키워드를 바꿔 다시 시도해 보세요.")
        sys.exit(1)

    print(f"      수집 완료 ({len(source_text):,}자)")

    # 2단계: 포스팅 생성
    print("[2/3] 블로그 포스팅 생성 중...")
    content = generate_blog_post(keyword, source_text)

    if not content.strip():
        print("포스팅 생성에 실패했습니다.")
        sys.exit(1)

    # 3단계: 파일 저장
    today = date.today().strftime("%Y-%m-%d")
    filename = f"{_sanitize(keyword)}_{today}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[3/3] 저장 완료 → {filepath}")
    print(f"\n{'─' * 50}")
    print(content[:600])
    if len(content) > 600:
        print(f"\n... (이하 {len(content) - 600:,}자 생략)")
    print(f"{'─' * 50}")


if __name__ == "__main__":
    main()
