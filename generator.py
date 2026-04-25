import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    _api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
except Exception:
    _api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=_api_key)

_SYSTEM_PROMPT = """\
당신은 전문 SEO 블로그 작가입니다. 제공된 참고 자료만을 근거로 한국어 블로그 포스팅을 작성합니다.

## HTML 구조 규칙
- 포스팅 제목: <h1> 태그
- 주요 소제목: <h2> 태그
- 세부 소제목: <h3> 태그
- 단락: <p> 태그
- 목록: <ul>/<li> 또는 <ol>/<li>

## 키워드 규칙
- <h1> 제목에 메인 키워드 포함
- 서론 첫 번째 <p>의 100자 이내에 메인 키워드를 자연스럽게 2번 이상 포함

## 팩트 기반 작성 (최우선 원칙)
- 참고 자료에 명시된 내용만 작성
- 자료에 없는 통계·수치·사실 임의 추가 금지 (할루시네이션 금지)
- 불확실한 내용은 "~로 알려져 있습니다" 형식으로 표현

## 가독성 규칙
- 문단은 3~5문장으로 짧게 유지
- <ul>/<li> 목록에는 날짜, 장소, 주요 사건 등 글의 핵심 요약 정보를 3가지 이상 담을 것 (소제목을 그대로 반복하지 말 것)
- 각 <h2> 섹션에 요약 목록 권장

## 금지 규칙
- 같은 문장이나 같은 인터뷰 인용구를 두 번 이상 반복 금지
- 한자(漢字) 사용 금지 — 100% 자연스러운 한국어 구어체로만 작성
- 타겟 키워드를 문장에 억지로 이어 붙이지 말 것 — 반드시 문맥에 맞게 풀어서 자연스럽게 녹여낼 것

## 결론 작성 규칙
- 결론(마지막 <p>)에서는 서론·본문에서 사용한 문장을 그대로 반복하지 말 것
- 글 전체를 한 문장으로 요약한 뒤, 독자의 공감을 유도하는 새로운 문장으로 마무리할 것

## 출력 형식
- 순수 HTML만 출력 (```html 코드 블록, 마크다운 금지)
- 메타 코멘트·설명 없이 HTML 본문만 반환\
"""


def generate_blog_post(keyword: str, source_text: str) -> str:
    source_text = source_text[:3000]

    user_prompt = (
        f"## 메인 키워드\n{keyword}\n\n"
        f"## 참고 자료\n"
        f"아래 내용만을 근거로 작성하세요. 자료에 없는 내용은 절대 추가하지 마세요.\n\n"
        f"{source_text}\n\n"
        f"---\n"
        f'위 자료를 바탕으로 "{keyword}" 키워드의 SEO 최적화 블로그 포스팅을 HTML로 작성하세요.'
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import sys
    from scraper import scrape_keyword

    kw = sys.argv[1] if len(sys.argv) > 1 else "파이썬 자동화"

    print(f"[1/2] '{kw}' 블로그 수집 중...")
    source = scrape_keyword(kw)

    print("[2/2] 포스팅 생성 중...")
    html = generate_blog_post(kw, source)
    print(html[:2000])
