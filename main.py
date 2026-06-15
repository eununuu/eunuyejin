import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. 웹앱 기본 설정
st.set_page_config(
    page_title="안전한 의약품 복용 가이드",
    page_icon="💊",
    layout="wide"
)

# 2. 데이터 로드 함수
@st.cache_data
def load_incident_data():
    paths = [
        "한국의약품안전관리원_연도별증상별 이상사례보고현황_20241231.csv",
        "data/한국의약품안전관리원_연도별증상별 이상사례보고현황_20241231.csv"
    ]
    for p in paths:
        try:
            return pd.read_csv(p, encoding="cp949")
        except:
            continue
    return None

@st.cache_data
def load_contra_data():
    paths = [
        "한국의약품안전관리원_병용금기약물_20240625_2.csv",
        "data/한국의약품안전관리원_병용금기약물_20240625_2.csv"
    ]
    for p in paths:
        try:
            df = pd.read_csv(p, encoding="cp949")
            for col in ['성분명1', '성분명2', '제품명1', '제품명2']:
                df[col] = df[col].fillna('').astype(str).str.strip()
            return df
        except:
            continue
    return None

df_incident = load_incident_data()
df_contra = load_contra_data()

# 3. 사이드바 메뉴
st.sidebar.title("💊 메뉴 선택")
page = st.sidebar.radio(
    "이동할 페이지를 선택하세요:",
    ["Page 1: 왜 약을 섞어 먹으면 위험할까?", "Page 2: 주요 병용금기 성분 가이드"]
)

# ==========================================
# PAGE 1: 왜 약을 섞어 먹으면 위험할까?
# ==========================================
if page == "Page 1: 왜 약을 섞어 먹으면 위험할까?":
    st.title("❓ 왜 약을 섞어 먹으면 위험할까?")
    st.markdown("---")
    st.markdown("""
    ### 🚨 의약품 오남용과 병용금기 복용의 위험성
    우리가 흔히 접하는 감기약, 진통제, 영양제조차도 함께 분해되면서 서로의 성분에 영향을 미칠 수 있습니다. 
    특히 **'병용금기 약물'**이란 두 가지 이상의 의약품을 함께 복용했을 때, **부작용 발생 위험이 현저히 높아지거나 치료 효과가 급격히 저하되어 동시에 투여해서는 안 되는 성분 조합**을 뜻합니다.
    """)
    
    if df_incident is not None:
        st.subheader("📊 국내 의약품 이상사례 보고 현황 (최근 5개년 TOP 5)")
        try:
            top_2024 = df_incident[['순위', '연도별증상(2024)', '연도별보고건수(2024)']].head(5)
            top_2024.columns = ['순위', '부작용 증상', '보고 건수(건)']
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.dataframe(top_2024, use_container_width=True, hide_index=True)
            with col2:
                fig = px.bar(top_2024, x='부작용 증상', y='보고 건수(건)', color='부작용 증상', text_auto=True)
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
        except:
            st.warning("시각화 데이터를 처리하는 중 일부 문제가 발생했습니다.")
    else:
        st.warning("이상사례 보고현황 CSV 데이터를 찾을 수 없어 통계 그래프를 표시할 수 없습니다.")

# ==========================================
# PAGE 2: 주요 병용금기 성분 가이드
# ==========================================
elif page == "Page 2: 주요 병용금기 성분 가이드":
    st.title("🔍 알아두어야 할 주요 병용금기 성분 가이드")
    st.markdown("데이터베이스에 등록된 **실제 약물 이름(제품명)** 또는 **성분명**을 선택하여 복용 중인 약을 여러 개 체크해 보세요.")
    st.markdown("---")
    
    if df_contra is not None:
        # 일반인이 알아보기 쉽게 제품명을 정제하는 함수
        def clean_product_name(name):
            if not name: 
                return ""
            name = re.sub(r'_\(.*?\)|\(.*?\)|_.*?밀리그램|_.*?mg|_.*?밀리그람', '', name)
            return name.strip()

        drug_dict = {}
        sample_placeholders = []
        
        for idx, row in df_contra.iterrows():
            ing1, ing2 = row['성분명1'], row['성분명2']
            prod1, prod2 = row['제품명1'], row['제품명2']
            
            c_prod1 = clean_product_name(prod1)
            c_prod2 = clean_product_name(prod2)
            
            # 1) 성분명 사전 등록
            if ing1: 
                drug_dict[f"[성분] {ing1}"] = ing1
            if ing2: 
                drug_dict[f"[성분] {ing2}"] = ing2
            
            # 2) 제품명 사전 등록
            if c_prod1 and ing1: 
                drug_dict[f"[제품] {c_prod1} ({ing1})"] = ing1
                if c_prod1 not in sample_placeholders:
                    sample_placeholders.append(c_prod1)
            if c_prod2 and ing2: 
                drug_dict[f"[제품] {c_prod2} ({ing2})"] = ing2
                if c_prod2 not in sample_placeholders:
                    sample_placeholders.append(c_prod2)

        # 사전의 Key값들을 가나다/ABC 순서로 정렬
        sorted_display_names = sorted(list(drug_dict.keys()))
        
        # 안내 문구(Placeholder)를 에러가 절대 안 나도록 가장 안전하게 생성
        if len(sample_placeholders) >= 2:
            hint = sample_placeholders[0] + ", " + sample_placeholders[1]
            placeholder_text = "예: " + hint + " 등을 검색 또는 선택"
        else:
            placeholder_text = "검색할 의약품명을 입력하세요."
        
        # 🌟 실제 데이터 기반 멀티 셀렉트 박스 (오류 구간 완벽 수정)
        selected_displays =
