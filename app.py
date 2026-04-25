import streamlit as st
from datetime import date
from scraper import scrape_keyword
from generator import generate_blog_post

st.set_page_config(page_title="블로그 자동 생성기", page_icon="📝", layout="centered")

st.title("블로그 포스팅 자동 생성기")
st.caption("키워드를 입력하면 네이버 블로그 자료를 수집해 SEO 최적화 포스팅을 생성합니다.")

keyword = st.text_input("키워드", placeholder="예: 신지 결혼 문원")

if st.button("생성하기", type="primary", disabled=not keyword.strip()):
    with st.status("작업 중...", expanded=True) as status:
        st.write(f"'{keyword}' 관련 블로그 수집 중...")
        source_text = scrape_keyword(keyword)

        if not source_text.strip() or source_text.startswith(f"[{keyword}] 검색 결과 없음"):
            status.update(label="실패", state="error")
            st.error("수집된 데이터가 없습니다. 키워드를 바꿔 다시 시도해보세요.")
            st.stop()

        st.write(f"수집 완료 ({len(source_text):,}자) — 포스팅 생성 중...")
        content = generate_blog_post(keyword, source_text)

        if not content.strip():
            status.update(label="실패", state="error")
            st.error("포스팅 생성에 실패했습니다.")
            st.stop()

        status.update(label="완료!", state="complete")

    st.subheader("생성된 포스팅")
    st.code(content, language="html")

    filename = f"{keyword.replace(' ', '_')}_{date.today().strftime('%Y-%m-%d')}.html"
    st.download_button(
        label="HTML 파일 다운로드",
        data=content.encode("utf-8"),
        file_name=filename,
        mime="text/html",
    )
