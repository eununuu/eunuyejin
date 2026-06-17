import streamlit as st

# 웹앱 기본 설정
st.set_page_config(
    page_title="안전한 의약품 복용 가이드",
    page_icon="💊",
    layout="wide"
)

# 다중 페이지 내비게이션 정의
pages = [
    st.Page("page1.py", title="왜 약을 섞어 먹으면 위험할까?", icon="❓"),
    st.Page("page2.py", title="주요 병용금기 성분 가이드", icon="🔍")
]

# 내비게이션 실행 및 구동
pg = st.navigation(pages)
pg.run()
