import streamlit as st
import pandas as pd
import re

st.title("🔍 알아두어야 할 주요 병용금기 성분 가이드")
st.markdown("데이터베이스에 등록된 **실제 약물 이름(제품명)** 또는 **성분명**을 선택하여 복용 중인 약을 여러 개 체크해 보세요.")
st.markdown("---")

@st.cache_data
def load_contra_data():
    paths = ["한국의약품안전관리원_병용금기약물_20240625_2.csv", "data/한국의약품안전관리원_병용금기약물_20240625_2.csv"]
    for p in paths:
        try:
            df = pd.read_csv(p, encoding="cp949")
            for col in ['성분명1', '성분명2', '제품명1', '제품명2']:
                df[col] = df[col].fillna('').astype(str).str.strip()
            return df
        except: continue
    return None

df_contra = load_contra_data()

if df_contra is not None:
    def clean_product_name(name):
        if not name: return ""
        name = re.sub(r'_\(.*?\)|\(.*?\)|_.*?밀리그램|_.*?mg|_.*?밀리그람', '', name)
        return name.strip()

    drug_dict = {}
    sample_placeholders = []
    
    for idx, row in df_contra.iterrows():
        ing1, ing2 = row['성분명1'], row['성분명2']
        prod1, prod2 = row['제품명1'], row['제품명2']
        c_prod1 = clean_product_name(prod1)
        c_prod2 = clean_product_name(prod2)
        
        if ing1: drug_dict[f"[성분] {ing1}"] = ing1
        if ing2: drug_dict[f"[성분] {ing2}"] = ing2
        if c_prod1 and ing1: 
            drug_dict[f"[제품] {c_prod1} ({ing1})"] = ing1
            if c_prod1 not in sample_placeholders: sample_placeholders.append(c_prod1)
        if c_prod2 and ing2: 
            drug_dict[f"[제품] {c_prod2} ({ing2})"] = ing2
            if c_prod2 not in sample_placeholders: sample_placeholders.append(c_prod2)

    sorted_display_names = sorted(list(drug_dict.keys()))
    
    if len(sample_placeholders) >= 2:
        placeholder_text = "예: " + sample_placeholders[0] + ", " + sample_placeholders[1] + " 등을 검색 또는 선택"
    else:
        placeholder_text = "검색할 의약품명을 입력하세요."

    # 다중 선택 박스
    selected_displays = st.multiselect(
        label="💊 복용 중이거나 확인할 약물들을 모두 선택하세요 (리스트 선택 및 검색 지원):",
        options=sorted_display_names,
        placeholder=placeholder_text
    )
    
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
        
        if len(selected_ingredients) >= 2:
            st.subheader("🚨 내 장바구니 약물 간 위험 조합 체크")
            for i in range(len(selected_ingredients)):
                for j in range(i + 1, len(selected_ingredients)):
                    ingA = selected_ingredients[i]
                    ingB = selected_ingredients[j]
                    
                    match_df = df_contra[
                        ((df_contra['성분명1'] == ingA) & (df_contra['성분mm2'] == ingB)) | # 데이터 매칭
                        ((df_contra['성분명1'] == ingB) & (df_contra['성분명2'] == ingA))
                    ] if '성분명2' in df_contra.columns else df_contra[
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
        
        st.write("")
        st.subheader("🔍 각 약물별 전체 병용금기 상대 성분 안내")
        
        for ing in selected_ingredients:
            res_df = df_contra[(df_contra['성분mm1' if '성분mm1' in df_contra.columns else '성분명1'] == ing) | (df_contra['성분명2'] == ing)]
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
                            "위험 사유": row['금기사유']
                        })
                    display_df = pd.DataFrame(display_data).drop_duplicates()
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.write("이 성분은 데이터베이스에 등록된 금기 조합이 없습니다.")
    else:
        st.info("💡 위의 검색창에 드시는 약 이름을 입력하여 선택해 주세요. 여러 개를 동시에 고를 수 있습니다.")
else:
    st.warning("⚠️ 병용금기 약물 CSV 데이터를 찾을 수 없습니다.")
