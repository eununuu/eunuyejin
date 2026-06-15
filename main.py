import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 웹앱 기본 설정
st.set_page_config(
    page_title="안전한 의약품 복용 가이드",
    page_icon="💊",
    layout="wide"
)

# 2. 데이터 로드 함수
@st.cache_data
def load_incident_data():
    paths = ["한국의약품안전관리원_연도별증상별 이상사례보고현황_20241231.csv", "data/한국의약품안전관리원_연도별증상별 이상사례보고현황_20241231.csv"]
    for p in paths:
        try: return pd.read_csv(p, encoding="cp949")
        except FileNotFoundError: continue
    st.error("이상사례 데이터 파일을 찾을 수 없습니다.")
    return None

@st.cache_data
def load_contra_data():
    paths = ["한국의약품안전관리원_병용금기약물_20240625_2.csv", "data/한국의약품안전관리원_병용금기약물_20240625_2.csv"]
    for p in paths:
        try:
            df = pd.read_csv(p, encoding="cp949")
            # 모든 텍스트 컬럼 결측치 제거 및 문자열 변환
            for col in ['성분명1', '성분명2', '제품명1', '제품명2']:
                df[col] = df[col].fillna('').astype(str).str.strip()
            return df
        except FileNotFoundError: continue
    st.error("병용금기 데이터 파일을 찾을 수 없습니다.")
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
        top_2024 = df_incident[['순위', '연도별증상(2024)', '연도별보고건수(2024)']].head(5)
        top_2024.columns = ['순위', '부작용 증상', '보고 건수(건)']
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(top_2024, use_container_width=True, hide_index=True)
        with col2:
            fig = px.bar(top_2024, x='부작용 증상', y='보고 건수(건)', color='부작용 증상', text_auto=True)
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# PAGE 2: 주요 병용금기 성분 가이드 (대폭 수정)
# ==========================================
elif page == "Page 2: 주요 병용금기 성분 가이드":
    st.title("🔍 알아두어야 할 주요 병용금기 성분 가이드")
    st.markdown("어려운 성분명을 몰라도 괜찮습니다! **약물 이름(제품명)** 또는 **성분명**을 편하게 입력하여 복용 중이거나 복용 예정인 약들을 **여러 개 선택**해 보세요.")
    st.markdown("---")
    
    if df_contra is not None:
        # 매핑용 사전 데이터 구축 (검색 효율화 및 일반인 편의성 향상)
        # 약물 사전: { "표시할 이름 (제품명 또는 성분명)": "실제 내부 성분명" }
        drug_dict = {}
        
        for _, row in df_contra.iterrows():
            ing1, ing2 = row['성분명1'], row['성분명2']
            prod1, prod2 = row['제품명1'], row['제품명2']
            
            # 성분명 등록
            if ing1: drug_dict[f"[성분] {ing1}"] = ing1
            if ing2: drug_dict[f"[성분] {ing2}"] = ing2
            # 제품명 등록 (사용자가 찾기 쉽게 제품명 뒤에 성분명도 괄호로 표기)
            if prod1 and ing1: drug_dict[f"[제품] {prod1} ({ing1})"] = ing1
            if prod2 and ing2: drug_dict[f"[제품] {prod2} ({ing2})"] = ing2

        # 가나다 및 알파벳 순 정렬
        sorted_display_names = sorted(list(drug_dict.keys()))
        
        # 🌟 핵심 기능: 멀티 셀렉트 박스 (원하는 약물을 여러 개 선택 가능)
        selected_displays = st.multiselect(
            "💊 복용 중이거나 확인할 약물들을 모두 선택하세요 (한글/영문 검색 가능):",
            options=sorted_display_names,
            placeholder="예: 타이레놀, 아스피린, ibuprofen 등을 검색하여 선택"
        )
        
        # 사용자가 선택한 아이템들의 실제 '성분명' 리스트 추출
        selected_ingredients = list(set([drug_dict[name] for name in selected_displays]))
        
        if selected_displays:
            st.markdown("### 🛒 선택한 약물 성분 목록")
            st.write(", ".join([f"`{ing}`" for ing in selected_ingredients]))
            
            st.markdown("---")
            st.markdown("### 🛡️ 병용금기 교차 검증 결과")
            
            # 1단계: 선택한 약물들 '끼리' 서로 금기 조합이 있는지 검사 (상호 교차 검증)
            danger_pairs_found = False
            
            if len(selected_ingredients) >= 2:
                st.subheader("🚨 내 장바구니 약물 간 위험 조합 체크")
                
                # 선택된 성분들의 쌍(Pair)을 확인
                for i in range(len(selected_ingredients)):
                    for j in range(i + 1, len(selected_ingredients)):
                        ingA = selected_ingredients[i]
                        ingB = selected_ingredients[j]
                        
                        # 두 성분이 데이터베이스에서 병용금기로 묶여있는지 확인
                        match_df = df_contra[
                            ((df_contra['성분명1'] == ingA) & (df_contra['성분명2'] == ingB)) |
                            ((df_contra['성분명1'] == ingB) & (df_contra['성분명2'] == ingA))
                        ]
                        
                        if not match_df.empty:
                            danger_pairs_found = True
                            reason = match_df.iloc[0]['금기사유']
                            st.error(f"⚠️ **위험! 동시 복용 금지**: `{ingA}` 와 `{ingB}` 조합은 함께 드시면 안 됩니다.")
                            st.caption(f"**이유/부작용:** {reason}")
                
                if not danger_pairs_found:
                    st.success("✅ 선택하신 약물들 상호 간에는 함께 먹으면 안 되는 금기 조합이 발견되지 않았습니다.")
            
            # 2단계: 선택한 각 약물들이 '전체 데이터베이스'에서 어떤 약들과 금기인지 개별 조회 리스트 제공
            st.write("")
            st.subheader("🔍 각 약물별 전체 병용금기 상대 성분 안내")
            st.caption("내가 선택한 약이 이외에 또 어떤 약들과 만나면 안 되는지 개별적으로 확인할 수 있습니다.")
            
            for ing in selected_ingredients:
                res_df = df_contra[(df_contra['성분명1'] == ing) | (df_contra['성분명2'] == ing)]
                
                with st.expander(f"📋 {ing} 성분의 전체 금기 리스트 보기 (총 {len(res_df)}건)"):
                    if not res_df.empty:
                        display_data = []
                        for _, row in res_df.iterrows():
                            if row['성분명1'] == ing:
                                contra_ing = row['성분명2']
                                contra_prod = row['제품명2']
                            else:
                                contra_ing = row['성분명1']
                                contra_prod = row['제품명1']
                                
                            display_data.append({
                                "함께 먹으면 안 되는 성분": contra_ing,
                                "상대 약물 제품명 예시": contra_prod,
                                "위험 사유": row['금기사유']
                            })
                        
                        display_df = pd.DataFrame(display_data).drop_duplicates()
                        
                        # 표 형태로 깔끔하게 출력
                        st.dataframe(
                            display_df, 
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.write("이 성분은 데이터베이스에 등록된 금기 조합이 없습니다.")
        else:
            st.info("💡 위의 검색창에 드시는 약 이름을 한글이나 영어로 입력하여 선택해 주세요. 여러 개를 동시에 고를 수 있습니다.")
