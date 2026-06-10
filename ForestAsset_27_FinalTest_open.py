import streamlit as st
import pandas as pd
import os
import math
import base64
import folium
from streamlit_folium import st_folium
import altair as alt

# 페이지 설정
st.set_page_config(page_title="산림문화자원 아카이브 시범 구축", page_icon="🌲", layout="wide")

# CSS 테마
st.markdown("""
<style>
    .stApp { font-family: 'Pretendard', 'Noto Sans KR', sans-serif; }
    h1 { color: #2ea043; text-align: center; }
    .stButton > button { border: 1px solid #2ea043; color: #2ea043; }
</style>
""", unsafe_allow_html=True)

# 1. 팝업 상세 정보 함수 (기존 슬라이더/비디오/속성 로직 포함)
@st.dialog("자원 상세 정보", width="large")
def show_detail_modal(item):
    col_img, col_text = st.columns([1, 1.2]) 
    with col_img:
        # 이미지 슬라이더 로직
        img_paths_str = str(item.get('이미지경로', ''))
        valid_img_paths = [p.strip() for p in img_paths_str.split(',') if p.strip() and os.path.exists(p.strip())]
        
        if not valid_img_paths:
            st.image('https://via.placeholder.com/800x600?text=No+Image', width='stretch')
        else:
            if 'img_idx' not in st.session_state: st.session_state.img_idx = 0
            st.image(valid_img_paths[st.session_state.img_idx % len(valid_img_paths)], width='stretch')
            if st.button("다음 이미지"): st.session_state.img_idx += 1
            
        # 비디오 렌더링
        vid = item.get('동영상경로', '')
        if pd.notna(vid) and str(vid).strip(): st.video(str(vid).strip())
            
    with col_text:
        st.subheader(item.get('명칭', ''))
        st.write(f"📍 {item.get('주소', '')}")
        st.divider()
        st.markdown(f"**설명:** {item.get('내용', '')}")
        
        # 상세 속성 표기 로직
        st.write("---")
        exclude = ['명칭', '내용', '이미지경로', '동영상경로', '주소', 'ID', 'Lat', 'Lon']
        for col in item.index:
            if col not in exclude:
                st.markdown(f"• **{col}**: {item[col]}")

# 2. 고정 차트 함수
def create_fixed_chart(data, title):
    df_chart = data.reset_index().rename(columns={'index': 'Category', '지역': 'Count', '중분류': 'Count'})
    return alt.Chart(df_chart).mark_bar(color='#2ea043').encode(
        x='Category', y='Count'
    ).properties(width=300, height=200, title=title)

# 3. 메인 로직
df = pd.read_csv('test_ForestAsset_27_modify.csv', encoding='utf-8-sig')
with st.sidebar:
    search_query = st.text_input("통합 검색")
    selected_category = st.selectbox("권역 필터", ["전체"] + list(df['지역'].dropna().unique()))
    selected_sub = st.selectbox("유형 필터", ["전체"] + list(df['중분류'].dropna().unique()))

filtered_df = df.copy()
if selected_category != "전체": filtered_df = filtered_df[filtered_df['지역'] == selected_category]
if selected_sub != "전체": filtered_df = filtered_df[filtered_df['중분류'] == selected_sub]
if search_query:
    filtered_df = filtered_df[filtered_df['명칭'].str.contains(search_query, na=False)]

tab1, tab2, tab3, tab4 = st.tabs(["🖼️ 전체 자원 갤러리", "📊 분석 및 탐색", "🗺️ 공간 탐색 (Map)", "📚 출처 정보"])

# 탭 구현
with tab1:
    st.subheader("🌲 전체 자원 아카이브")
    cols = st.columns(4)
    for i, (idx, row) in enumerate(df.head(12).iterrows()):
        with cols[i % 4]:
            st.image("https://via.placeholder.com/300x200?text=No+Image", width='stretch')
            st.markdown(f"**{row['명칭']}**")
            if st.button("상세보기", key=f"t1_{idx}"): show_detail_modal(row)

with tab2:
    st.subheader("📊 분석 및 유사 자원 탐색")
    c1, c2 = st.columns(2)
    with c1: st.altair_chart(create_fixed_chart(filtered_df['지역'].value_counts(), "권역 분포"))
    with c2: st.altair_chart(create_fixed_chart(filtered_df['중분류'].value_counts(), "유형 분포"))
    
    for i, row in filtered_df.iterrows():
        with st.container(border=True):
            if st.button(f"🔍 {row['명칭']} 상세 정보 열람", key=f"t2_{i}"): show_detail_modal(row)

with tab3:
    m = folium.Map(location=[36.5, 127.5], zoom_start=7)
    for _, row in filtered_df.iterrows():
        folium.Marker([row['Lat'], row['Lon']], tooltip=row['명칭']).add_to(m)
    st_folium(m, width=1200, height=600)

with tab4:
    st.subheader("📚 데이터 출처")
    if '출처' in df.columns: st.dataframe(df[['명칭', '출처', '관련링크']], use_container_width=True)
