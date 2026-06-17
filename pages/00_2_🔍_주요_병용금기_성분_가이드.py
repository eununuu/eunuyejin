import streamlit as st
import pandas as pd
import re
import os

st.title("🔍 알아두어야 할 주요 병용금기 성분 가이드")
st.markdown("데이터베이스에 등록된 **실제 약물 이름(제품명)** 또는 **성분명**을 선택하여 복용 중인 약을 여러 개 체크해 보세요.")
st.markdown("---")

# ==========================================
# 🛑 무적의 데이터 로드 함수 (BOM 및 경로 완벽 제어)
# ==========================================
@st.cache_data
def load_contra_data():
    filename = "한국의약품안전관리원_병용금기약물_20240625_2.csv"
    
    # 1. 파일이 존재할 수 있는 모든 경로를 과학적으로 탐색
    possible_paths = [
        filename,                                # 루트 폴더에 있을 때
        os.path.join("data", filename),          # data 폴더에 있을 때
        os.path.join("..", filename),            # 상위 폴더에 있을 때
        os.path.join("..", "data", filename)     # 상위 폴더의 data 폴더에 있을 때
    ]
    
    target_path = None
    for p in possible_paths:
        if os.path.exists(p):
            target_path = p
            break
            
    # 만약 위 경로에서 못 찾았다면 현재 스크립트 파일 위치를 기준으로 재탐색
    if not target_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        fallback_paths = [
            os.path.join(parent_dir, filename),
            os.path.join(parent_dir, "data", filename),
            os.path.join(current_dir, filename)
        ]
        for p in fallback_paths:
            if os.path.exists(p):
                target_path = p
                break

    # 2. 파일을 찾았다면 가장 안전한 인코딩 순서로 로드 시도
    if target_path:
        # 공공데이터 특유의 한글 깨짐 및 서명 에러를 막기 위해 utf-8-sig를 최우선으로 배치
        encodings = ["utf-8-sig", "cp949", "utf-8", "ecu-kr"]
        for enc in encodings:
            try:
                df = pd.read_csv(target_path, encoding=enc)
                
                # 필수 컬럼 존재 여부 확인 및 공백 제거 전처리
                required_cols = ['성분명1', '성분명2', '제품명1', '제품명2']
                for col in required_cols:
                    if col in df.columns:
                        df[col] = df[col].fillna('').astype(str).str.strip()
                    else:
                        df[col] = '' # 혹시 컬럼이 없으면 빈 컬럼 생성하여 에러 방지
                return df
            except Exception:
                continue
                
    return None

df_contra = load_contra_data()

# ==========================================
# 🛒 화면 UI 및 데이터 렌더링 구간
# ==========================================
if df_contra is not None and not df_contra.empty:
    
    # 일반인이 알아보기 쉽게 제품명 정제하는 함수
    def clean_product_name(name):
        if not name or name == 'nan': 
            return ""
        name = re.sub(r'_\(.*?\)|\(.*?\)|_.*?밀리그램|_.*?mg|_.*?밀리그람', '', name)
        return name.strip()

    drug_dict = {}
    sample_placeholders = []
    
    # 데이터 가공 및 딕셔너리 빌드
    for idx, row in df_contra.iterrows():
        ing1, ing2 = row.get('성분명1', ''), row.get('성분명2', '')
        prod1, prod2 = row.get('제품명1', ''), row.get('제품명2', '')
        
        c_prod1 = clean_product_name(prod1)
        c_prod2 = clean_product_name(prod2)
        
        if ing1 and ing1 != 'nan': 
            drug_dict[f"[성분] {ing1}"] = ing1
        if ing2 and ing2 != 'nan': 
            drug_dict[f"[성분] {ing2}"] = ing2
            
        if c_prod1 and ing1 and c_prod1 != 'nan': 
            drug_dict[f"[제품] {c_prod1} ({ing1})"] = ing1
            if c_prod1 not in sample_placeholders: 
                sample_placeholders.append(c_prod1)
                
        if c_prod2 and ing2 and c_prod2 != 'nan': 
            drug_dict[f"[제품] {c_prod2} ({ing2})"] = ing2
            if c_prod2 not in sample_placeholders: 
                sample_placeholders.append(c_prod2)

    # 가나다순 정렬
    sorted_display_names = sorted(list(drug_dict.keys()))
    
    # 검색창 힌트(Placeholder) 안전하게 조립
    if len(sample_placeholders) >= 2:
        placeholder_text = f"예: {sample_placeholders[0]}, {sample_placeholders[1]} 등을 입력"
    else:
        placeholder_text = "검색할 의약품명을 입력하세요."

    # 🌟 실제 데이터 기반 멀티 셀렉트 박스
    selected_displays = st.multiselect(
        label="💊 복용 중이거나 확인할 약물들을 모두 선택하세요 (리스트 선택 및 검색 지원):",
        options=sorted_display_names,
        placeholder=placeholder_text
    )
    
    # 사용자가 선택한 성분 고유값 추출
    selected_ingredients = []
    for name in selected_displays:
        if name in drug_dict:
            selected_ingredients.append(drug_dict[name])
    selected_ingredients = list(set(selected_ingredients))
    
    if selected_displays:
        st.markdown("### 🛒 선택한 약물 성분 목록")
        st.write(", ".join([f"`{ing}`" for ing in selected_ingredients]))
        st.markdown("---")
        st.markdown("### 🛡️ 병용금기 교차 검증 결과")
        
        danger_pairs_found = False
        
        # 1단계: 장바구니 약물 간 상호 교차 검증
        if len(selected_ingredients) >= 2:
            st.subheader("🚨 내 장바구니 약물 간 위험 조합 체크")
            
            for i in range(len(selected_ingredients)):
                for j in range(i + 1, len(selected_ingredients)):
                    ingA = selected_ingredients[i]
                    ingB = selected_ingredients[j]
                    
                    match_df = df_contra[
                        ((df_contra['성분명1'] == ingA) & (df_contra['성분명2'] == ingB)) |
                        ((df_contra['성분명1'] == ingB) & (df_contra['성분명2'] == ingA))
                    ]
                    
                    if not match_df.empty:
                        danger_pairs_found = True
                        reason = match_df.iloc[0].get('금기사유', '이유 미기재')
                        st.error(f"⚠️ **위험! 동시 복용 금지**: `{ingA}` 와 `{ingB}` 조합은 함께 드시면 안 됩니다.")
                        st.caption(f"**이유/부작용:** {reason}")
            
            if not danger_pairs_found:
                st.success("✅ 선택하신 약물들 상호 간에는 함께 먹으면 안 되는 금기 조합이 발견되지 않았습니다.")
        
        # 2단계: 선택한 약물 전체 DB 대상 금기 정보 안내
        st.write("")
        st.subheader("🔍 각 약물별 전체 병용금기 상대 성분 안내")
        
        for ing in selected_ingredients:
            res_df = df_contra[(df_contra['성분명1'] == ing) | (df_contra['성분명2'] == ing)]
            
            with st.expander(f"📋 {ing} 성분의 전체 금기 리스트 보기 (총 {len(res_df)}건)"):
                if not res_df.empty:
                    display_data = []
                    for _, row in res_df.iterrows():
                        if row['성분명1'] == ing:
                            contra_ing = row['성분명2']
                            contra_prod = clean_product_name(row['제품명2'])
                        else:
                            contra_ing = row['성분명1']
                            contra_prod = clean_product_name(row['제품명1'])
                            
                        display_data.append({
                            "함께 먹으면 안 되는 성분": contra_ing,
                            "상대 약물 제품명 예시": contra_prod,
                            "위험 사유": row.get('금기사유', '이유 미기재')
                        })
                    
                    display_df = pd.DataFrame(display_data).drop_duplicates()
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.write("이 성분은 데이터베이스에 등록된 금기 조합이 없습니다.")
    else:
        st.info("💡 위의 검색창에 드시는 약 이름을 입력하여 선택해 주세요. 여러 개를 동시에 고를 수 있습니다.")
else:
    # 🛑 파일이 진짜 없거나 깨졌을 때만 출력되는 비상 안내문
    st.error("⚠️ 병용금기 약물 CSV 데이터를 성공적으로 불러오지 못했습니다.")
    st.markdown("""
    **🛠️ 조치 방법안내:**
    1. GitHub 저장소 최상위 경로(Root) 혹은 `data/` 폴더 안에 **`한국의약품안전관리원_병용금기약물_20240625_2.csv`** 파일이 실제로 존재하는지 다시 한번 확인해 주세요.
    2. 파일 이름에 숨겨진 공백이나 오타가 없는지(마우스로 파일명을 긁어 복사해서 확인) 대조해 보시기 바랍니다.
    """)
