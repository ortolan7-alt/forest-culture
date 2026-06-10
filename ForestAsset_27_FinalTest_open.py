import streamlit as st
import pandas as pd
import os
import math
import base64
import folium
from streamlit_folium import st_folium
import altair as alt

# 1. 페이지 설정
st.set_page_config(page_title="산림문화자원 아카이브 시범 구축", page_icon="🌲", layout="wide")

# CSS 최적화
st.markdown("""
<style>
    .stApp { font-family: 'Pretendard', sans-serif; }
    h1 { color: #2ea043; text-align: center; }
    .stButton > button { border: 1px solid #2ea043; color: #2ea043; }
</style>
""", unsafe_allow_html=True)

# 2. 유틸리티 함수
def get_base64_of_image(image_path):
    if pd.notna(image_path) and os.path.exists(str(image_path)):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

def load_data(csv_path):
    return pd.read_csv(csv_path, encoding='utf-8-sig') if os.path.exists(csv_path) else pd.DataFrame()

# 3. 상세 정보 모달 (슬라이더, 비디오 포함)
@st.dialog("자원 상세 정보", width="large")
def show_detail_modal(item):
    col_img, col_text = st.columns([1, 1.2]) 
    with col_img:
        img_paths = [p.strip() for p in str(item.get('이미지경로', '')).split(',') if p.strip() and os.path.exists(p.strip())]
        if not img_paths:
            st.image('https://via.placeholder.com/800x600?text=No+Image', width='stretch')
        else:
            if 'img_idx' not in st.session_state: st.session_state.img_idx = 0
            st.image(img_paths[st.session_state.img_idx % len(img_paths)], width='stretch')
            if st.button("이미지 넘기기"): st.session_state.img_idx += 1
            
        vid = item.get('동영상경로', '')
        if pd.notna(vid) and str(vid).strip(): st.video(str(vid).strip())
            
    with col_text:
        st.subheader(item.get('명칭', ''))
        st.write(f"📍 {item.get('주소', '')}")
        st.markdown(f"**설명:** {item.get('내용', '')}")
        st.write("---")
        for col in item.index:
            if col not in ['명칭', '내용', '이미지경로', '동영상경로', '주소', 'ID', 'Lat', 'Lon']:
                st.markdown(f"• **{col}**: {item[col]}")

# 4. 차트 생성 함수
def create_fixed_chart(data, title, type='bar'):
    df_chart = data.reset_index().rename(columns={'index': 'Category', '지역': 'Count', '중분류': 'Count'})
    if type == 'bar':
        return alt.Chart(df_chart).mark_bar(color='#2ea043').encode(x='Category', y='Count').properties(width=300, height=200, title=title)
    return alt.Chart(df_chart).mark_arc().encode(theta='Count', color='Category').properties(width=300, height=200, title=title)

# 5. 메인 로직
df = load_data('test_ForestAsset_27_modify.csv')
if not df.empty:
    with st.sidebar:
        search_query = st.text_input("통합 검색")
        selected_cat = st.selectbox("권역 필터", ["전체"] + list(df['지역'].dropna().unique()))
        selected_sub = st.selectbox("유형 필터", ["전체"] + list(df['중분류'].dropna().unique()))

    filtered_df = df.copy()
    if selected_cat != "전체": filtered_df = filtered_df[filtered_df['지역'] == selected_cat]
    if selected_sub != "전체": filtered_df = filtered_df[filtered_df['중분류'] == selected_sub]
    if search_query:
        filtered_df = filtered_df[filtered_df['명칭'].str.contains(search_query, na=False)]

    tab1, tab2, tab3, tab4 = st.tabs(["🖼️ 전체 자원 갤러리", "📊 분석 및 탐색", "🗺️ 공간 탐색 (Map)", "📚 출처 정보"])

    with tab1:
        st.subheader("🌲 전체 산림문화자원 아카이브")
        c1, c2, c3 = st.columns(3)
        c1.metric("전체 자원", len(df)); c2.metric("권역", df['지역'].nunique()); c3.metric("유형", df['중분류'].nunique())
        st.divider()
        cols = st.columns(4)
        for i, (idx, row) in enumerate(df.head(12).iterrows()):
            with cols[i % 4]:
                st.image("https://via.placeholder.com/300x200?text=No+Image", width='stretch')
                st.markdown(f"**{row['명칭']}**")
                if st.button("상세보기", key=f"t1_{idx}"): show_detail_modal(row)

    with tab2:
        st.subheader("📊 필터링된 자원 분석")
        c1, c2 = st.columns(2)
        with c1: st.altair_chart(create_fixed_chart(filtered_df['지역'].value_counts(), "권역 분포", 'bar'))
        with c2: st.altair_chart(create_fixed_chart(filtered_df['중분류'].value_counts(), "유형 분포", 'arc'))
        for i, row in filtered_df.iterrows():
            with st.container(border=True):
                c_img, c_txt = st.columns([1, 4])
                c_img.image("https://via.placeholder.com/150x100?text=Img", width=150)
                c_txt.write(f"**{row['명칭']}**\n\n{row.get('주소', '')}")
                if c_txt.button("상세보기", key=f"t2_{i}"): show_detail_modal(row)

    with tab3:
        m = folium.Map(location=[36.5, 127.5], zoom_start=7)
        for _, row in filtered_df.iterrows():
            if pd.notna(row.get('Lat')): folium.Marker([row['Lat'], row['Lon']], tooltip=row['명칭']).add_to(m)
        st_folium(m, width=1200, height=600)

    with tab4:
        st.subheader("📚 데이터 출처 및 참고 문헌")
        if '출처' in df.columns: st.dataframe(df[['명칭', '출처', '관련링크']], use_container_width=True)
