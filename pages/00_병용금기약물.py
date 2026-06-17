import streamlit as st
import pandas as pd
import plotly.express as px

st.title("❓ 왜 약을 섞어 먹으면 위험할까?")
st.markdown("---")

st.markdown("""
### 🚨 의약품 오남용과 병용금기 복용의 위험성
우리가 흔히 접하는 감기약, 진통제, 영양제조차도 함께 분해되면서 서로의 성분에 영향을 미칠 수 있습니다. 
특히 **'병용금기 약물'**이란 두 가지 이상의 의약품을 함께 복용했을 때, **부작용 발생 위험이 현저히 높아지거나 치료 효과가 급격히 저하되어 동시에 투여해서는 안 되는 성분 조합**을 뜻합니다.

* **체내 독성 증가:** 한 약물이 다른 약물의 대사(분해)를 방해하여 몸속 약물 농도가 비정상적으로 높아지면 간, 신장 등에 치명적인 손상을 줄 수 있습니다.
* **심각한 부작용 초래:** 가벼운 구토나 두드러기부터 시작해 심한 경우 심부정맥, 호흡곤란, 종양용해증후군 등 위험한 상황에 직면할 수 있습니다.
""")

# 데이터 로드 함수 (경로 유연화 및 캐싱)
@st.cache_data
def load_incident_data():
    paths = ["한국의약품안전관리원_연도별증상별 이상사례보고현황_20241231.csv", "data/한국의약품안전관리원_연도별증상별 이상사례보고현황_20241231.csv"]
    for p in paths:
        try:
            return pd.read_csv(p, encoding="cp949")
        except:
            continue
    return None

df_incident = load_incident_data()

if df_incident is not None:
    st.write("")
    st.subheader("📊 국내 의약품 이상사례 보고 현황 (최근 5개년 TOP 5)")
    st.caption("출처: 한국의약품안전관리원 데이터 기반")
    
    try:
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
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning("시각화 데이터를 처리하는 중 일부 문제가 발생했습니다.")
else:
    st.warning("⚠️ 이상사례 보고현황 CSV 데이터를 찾을 수 없어 통계 그래프를 표시할 수 없습니다.")
