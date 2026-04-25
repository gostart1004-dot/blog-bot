import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

try:
    import streamlit as st
    NAVER_CLIENT_ID = st.secrets.get("NAVER_CLIENT_ID") or os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = st.secrets.get("NAVER_CLIENT_SECRET") or os.getenv("NAVER_CLIENT_SECRET")
except Exception:
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def get_blog_links(keyword: str, count: int = 5) -> list[str]:
    """
    Naver 블로그 검색 API로 키워드 관련 최근 6개월 게시글 링크를 count개 반환.
    결과가 부족하면 가능한 만큼만 반환한다.
    """
    url = "https://openapi.naver.com/v1/search/blog"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": keyword,
        "display": 30,   # 필터링 여유분
        "sort": "date",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()

    cutoff = datetime.now() - timedelta(days=180)
    links: list[str] = []

    for item in resp.json().get("items", []):
        try:
            # 네이버 블로그 검색 API는 postdate(YYYYMMDD) 형식 사용
            pub_dt = datetime.strptime(item["postdate"], "%Y%m%d")
        except Exception:
            continue

        if pub_dt >= cutoff:
            links.append(item["link"])

        if len(links) >= count:
            break

    return links


def _extract_naver_blog(url: str) -> str:
    """네이버 블로그는 모바일 URL로 접근해 se-main-container 영역 추출."""
    mobile_url = url.replace("://blog.naver.com", "://m.blog.naver.com")
    mobile_headers = {
        **_HEADERS,
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        ),
    }
    resp = requests.get(mobile_url, headers=mobile_headers, timeout=10)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding

    soup = BeautifulSoup(resp.text, "html.parser")

    # 네이버 스마트에디터 본문 컨테이너 우선, 없으면 구형 뷰어
    container = (
        soup.find("div", class_="se-main-container")
        or soup.find("div", id="postViewArea")
        or soup.find("div", class_="post-view")
    )

    if container:
        for tag in container(["script", "style"]):
            tag.decompose()
        return _clean_text(container.get_text(separator="\n"))

    return ""


def _extract_generic(url: str) -> str:
    """일반 블로그(티스토리 등) 본문 추출."""
    resp = requests.get(url, headers=_HEADERS, timeout=10)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "iframe"]):
        tag.decompose()

    # 의미 있는 본문 컨테이너를 순서대로 시도
    container = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=lambda c: c and any(
            kw in c.lower() for kw in ("content", "entry", "post", "article", "본문")
        ))
        or soup.find("body")
    )

    raw = container.get_text(separator="\n") if container else soup.get_text(separator="\n")
    return _clean_text(raw)


def _clean_text(text: str) -> str:
    """연속 빈 줄 제거 후 반환."""
    lines = [line.strip() for line in text.splitlines()]
    cleaned = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False
    return "\n".join(cleaned).strip()


def extract_text_from_url(url: str) -> str:
    """URL 하나에서 본문 텍스트 추출. 네이버 블로그는 전용 파서 사용."""
    if "blog.naver.com" in url:
        text = _extract_naver_blog(url)
        if text:
            return text

    return _extract_generic(url)


def scrape_keyword(keyword: str, count: int = 5) -> str:
    """
    키워드로 블로그 링크를 수집하고 각 링크의 본문을 하나의 문자열로 합쳐 반환.
    각 출처는 구분 헤더로 분리된다.
    """
    links = get_blog_links(keyword, count)

    if not links:
        return f"[{keyword}] 검색 결과 없음 (최근 6개월)"

    parts: list[str] = []
    for i, link in enumerate(links, 1):
        try:
            text = extract_text_from_url(link)
            parts.append(f"=== 출처 {i}: {link} ===\n{text}")
        except Exception as exc:
            parts.append(f"=== 출처 {i}: {link} ===\n[수집 실패: {exc}]")

    return "\n\n".join(parts)


if __name__ == "__main__":
    import sys

    kw = sys.argv[1] if len(sys.argv) > 1 else "파이썬 자동화"
    result = scrape_keyword(kw)
    print(result[:3000])
