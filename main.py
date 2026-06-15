import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 웹앱 기본 설정
st.set_page_config(
    page_title="안전한 의약품 복용 가이드",
    page_icon="💊",
    layout="wide"
)

# 2. 데이터 로드 함수 (경로 에러 방지를 위해 data/ 제거 후 유연하게 처리)
@st.cache_data
def load_incident_data():
    # 여러 경로 후보를 탐색하여 안전하게 로드
    paths = ["한국의약품안전관리원_연도별증상별 이상사례보고현황_20241231.csv", "data/한국의약품안전관리원_연도별증상별 이상사례보고현황_20241231.csv"]
    for p in paths:
        try:
            return pd.read_csv(p, encoding="cp949")
        except FileNotFoundError:
            continue
    st.error("이상사례 데이터 파일을 찾을 수 없습니다. 파일명을 확인해주세요.")
    return None

@st.cache_data
def load_contra_data():
    paths = ["한국의약품안전관리원_병용금기약물_20240625_2.csv", "data/한국의약품안전관리원_병용금기약물_20240625_2.csv"]
    for p in paths:
        try:
            df = pd.read_csv(p, encoding="cp949")
            # 검색 정확도를 위해 문자열 처리 및 결측치 제거
            df['성분명1'] = df['성분명1'].fillna('').astype(str).str.strip()
            df['성분명2'] = df['성분명2'].fillna('').astype(str).str.strip()
            df['성분명1_clean'] = df['성분명1'].str.lower()
            df['성분명2_clean'] = df['성분명2'].str.lower()
            return df
        except FileNotFoundError:
            continue
    st.error("병용금기 데이터 파일을 찾을 수 없습니다. 파일명을 확인해주세요.")
    return None

# 데이터 미리 로드
df_incident = load_incident_data()
df_contra = load_contra_data()

# 3. 사이드바 메뉴 구성 (페이지 전환)
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
    
    * **체내 독성 증가:** 한 약물이 다른 약물의 대사(분해)를 방해하여 몸속 약물 농도가 비정상적으로 높아지면 간, 신장 등에 치명적인 손상을 줄 수 있습니다.
    * **심각한 부작용 초래:** 가벼운 구토나 두드러기부터 시작해 심한 경우 심부정맥, 호흡곤란, 종양용해증후군 등 위험한 상황에 직면할 수 있습니다.
    """)
    
    st.write("")
    st.subheader("📊 국내 의약품 이상사례 보고 현황 (최근 5개년 TOP 5)")
    st.caption("출처: 한국의약품안전관리원 데이터 기반")
    
    if df_incident is not None:
        top_2024 = df_incident[['순위', '연도별증상(2024)', '연도별보고건수(2024)']].head(5)
        top_2024.columns = ['순위', '부작용 증상', '보고 건수(건)']
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write("#### 2024년 다빈도 부작용 증상 순위")
            st.dataframe(top_2024, use_container_width=True, hide_index=True)
            
        with col2:
            fig = px.bar(
                top_2024, 
                x='부작용 증상', 
                y='보고 건수(건)',
                title="2024년 주요 부작용 보고 건수 그래프",
                color='부작용 증상',
                text_auto=True
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
    st.markdown("---")
    st.info("💡 왼쪽 사이드바 메뉴에서 **'Page 2: 주요 병용금기 성분 가이드'**를 선택하시면 드시는 약물의 금기 성분을 직접 검색해보실 수 있습니다.")

# ==========================================
# PAGE 2: 주요 병용금기 성분 가이드
# ==========================================
elif page == "Page 2: 주요 병용금기 성분 가이드":
    st.title("🔍 알아두어야 할 주요 병용금기 성분 가이드")
    st.markdown("사용자가 확인하고자 하는 약물의 **성분명(한국어 또는 영어)**을 입력하면 함께 먹으면 안 되는 성분과 부작용 요약을 보여줍니다.")
    st.markdown("---")
    
    if df_contra is not None:
        # 1. 고유 성분명 목록 전체 추출 (성분명1과 성분명2 합치기)
        ing1 = df_contra['성분명1'].unique()
        ing2 = df_contra['성분명2'].unique()
        all_ingredients = sorted(list(set(ing1) | set(ing2)))
        # 빈 문자열 제거
        all_ingredients = [x for x in all_ingredients if x.strip()]
        
        # 2. 통합 검색창 구성 (한국어/영어 모두 입력 가능)
        search_input = st.text_input("💊 성분명을 입력하세요 (한글 또는 영문):", placeholder="예: 아스피린, ibuprofen, venetoclax 등")
        
        selected_ingredient = ""
        
        # 무언가 타이핑 했을 때 자동완성 리스트 박스를 아래에 동적으로 띄워줌
        if search_input:
            search_keyword = search_input.lower().strip()
            filtered_list = [ing for ing in all_ingredients if search_keyword in ing.lower()]
            
            if filtered_list:
                selected_ingredient = st.selectbox(
                    f"💡 '{search_input}' 관련 성분 검색 결과입니다. 정확한 성분을 선택하세요:",
                    options=filtered_list
                )
            else:
                st.warning("⚠️ 일치하는 성분명이 검색되지 않았습니다. 다른 성분명이나 철자를 확인해 주세요.")
        else:
            # 아무것도 입력 안 했을 때는 전체 리스트에서 직접 고를 수 있는 기본 선택창 제공
            selected_ingredient = st.selectbox(
                "또는 아래의 전체 리스트에서 성분명을 직접 선택하세요:",
                options=["선택하세요"] + all_ingredients
            )
            
        # 3. 결과 출력 로직
        if selected_ingredient and selected_ingredient != "선택하세요":
            st.markdown(f"### 🛡️ '{selected_ingredient}' 관련 병용금기 검색 결과")
            
            clean_name = selected_ingredient.lower().strip()
            
            # 성분명1 혹은 성분명2에 매칭되는 데이터 필터링
            res_df = df_contra[
                (df_contra['성분명1_clean'] == clean_name) | 
                (df_contra['성분명2_clean'] == clean_name)
            ]
            
            if not res_df.empty:
                display_data = []
                for _, row in res_df.iterrows():
                    # 검색한 성분이 1번에 있으면 상대 성분은 2번, 반대면 1번으로 정의
                    if str(row['성분명1']).lower().strip() == clean_name:
                        my_prod = row['제품명1']
                        contra_ing = row['성분명2']
                        contra_prod = row['제품명2']
                    else:
                        my_prod = row['제품명2']
                        contra_ing = row['성분명1']
                        contra_prod = row['제품명1']
                        
                    display_data.append({
                        "조회성분 제품 예시": my_prod,
                        "함께 먹으면 안 되는 성분": contra_ing,
                        "상대성분 제품 예시": contra_prod,
                        "금기 사유": row['금기사유']
                    })
                
                # 중복 행 제거 후 정렬
                display_df = pd.DataFrame(display_data).drop_duplicates()
                st.write(f"총 **{len(display_df)}**개의 병용금기 조합이 조회되었습니다.")
                
                # 결과 카드식 배열
                for idx, row in display_df.iterrows():
                    with st.expander(f"❌ 병용 금기 성분: {row['함께 먹으면 안 되는 성분']}"):
                        st.markdown(f"**· 내가 검색한 성분의 제품 예시:** {row['조회성분 제품 예시']}")
                        st.markdown(f"**· 같이 먹으면 위험한 약 제품 예시:** {row['상대성분 제품 예시']}")
                        st.error(f"**· 위험성 및 부작용 사유:**\n\n{row['금기 사유']}")
            else:
                st.success("✅ 해당 성분은 현재 데이터베이스 내에 등록된 병용금기 조합 정보가 없습니다.")
