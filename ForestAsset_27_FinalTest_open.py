import streamlit as st
import pandas as pd
import os
import math
import base64
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
import altair as alt

# 1. 페이지 설정 및 다크모드 대응 CSS 테마
st.set_page_config(page_title="산림문화자원 아카이브 시범 구축", page_icon="🌲", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
    
    .stApp {
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
    }
    
    h1 {
        color: var(--text-color) !important;
        font-weight: 800;
        letter-spacing: -0.5px;
        text-align: center;
        margin-bottom: 5px !important;
    }
    
    .stMarkdown p {
        text-align: center;
        color: var(--text-color);
        opacity: 0.8;
        font-size: 1.1em;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(128, 128, 128, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: var(--secondary-background-color);
        border-radius: 8px 8px 0px 0px;
        padding: 10px 24px;
        color: var(--text-color);
        opacity: 0.7;
        font-weight: 600;
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-bottom: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        background-color: #2ea043 !important;
        border-color: #2ea043 !important;
        opacity: 1;
    }
    
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    .stButton > button {
        border-radius: 6px;
        border: 1px solid #2ea043;
        color: #2ea043;
        background-color: transparent;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    
    .stButton > button:hover {
        background-color: #2ea043;
        color: #FFFFFF;
        border-color: #2ea043;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

def get_base64_of_image(image_path):
    if pd.notna(image_path) and os.path.exists(str(image_path)):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# ★ 이미지 슬라이더 전환 콜백 함수
def change_img_index(state_key, step, total_images):
    st.session_state[state_key] = (st.session_state[state_key] + step) % total_images

# ==========================================
# 2. 파이썬 전용 상세 팝업 모달창 (버튼식 슬라이더 적용)
# ==========================================
@st.dialog("자원 상세 정보", width="large")
def show_detail_modal(item):
    col_img, col_text = st.columns([1, 1.2]) 
    
    with col_img:
        img_paths_str = str(item.get('이미지경로', ''))
        valid_img_paths = [p.strip() for p in img_paths_str.split(',') if p.strip() and os.path.exists(p.strip())]
        
        # ★ 최신 버전 대응 (use_container_width -> width='stretch' 로 전면 교체)
        if not valid_img_paths:
            st.image('https://via.placeholder.com/800x600?text=No+Image', width='stretch')
            
        elif len(valid_img_paths) == 1:
            st.image(valid_img_paths[0], width='stretch')
            
        else:
            item_id = str(item.name) 
            state_key = f"img_idx_{item_id}"
            
            if state_key not in st.session_state:
                st.session_state[state_key] = 0
                
            current_idx = st.session_state[state_key]
            
            st.image(valid_img_paths[current_idx], width='stretch')
            
            col_prev, col_lbl, col_next = st.columns([1, 1, 1])
            with col_prev:
                st.button("◀ 이전", key=f"prev_{item_id}", on_click=change_img_index, args=(state_key, -1, len(valid_img_paths)), width='stretch')
            with col_lbl:
                st.markdown(f"<div style='text-align:center; padding-top:10px; font-weight:bold; color:var(--text-color);'>{current_idx + 1} / {len(valid_img_paths)}</div>", unsafe_allow_html=True)
            with col_next:
                st.button("다음 ▶", key=f"next_{item_id}", on_click=change_img_index, args=(state_key, 1, len(valid_img_paths)), width='stretch')
                
        vid_path = item.get('동영상경로', '') 
        if pd.notna(vid_path) and str(vid_path).strip() != '' and str(vid_path).strip() != 'nan':
            st.write("") 
            st.markdown("<div style='text-align:left; font-size:0.85rem; font-weight:bold; color:#2ea043; margin-bottom:5px;'>🎥 관련 영상</div>", unsafe_allow_html=True)
            st.video(str(vid_path).strip())
            
    with col_text:
        st.markdown(f"<h3 style='text-align:left; color:var(--text-color); margin-top:0;'>{str(item.get('명칭', '제목 없음'))}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:left; font-size:0.85rem; color:var(--text-color); opacity:0.7; margin-bottom:15px;'>📍 {item.get('주소', '주소 미상')}</p>", unsafe_allow_html=True)
        st.divider()
        
        st.markdown("<div style='text-align:left; font-size:0.85rem; font-weight:bold; color:#2ea043; margin-bottom:5px;'>📖 자원 설명</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:left; font-size:0.9rem; line-height:1.6; color:var(--text-color); opacity:0.9;'>{str(item.get('내용', '등록된 설명이 없습니다.'))}</div>", unsafe_allow_html=True)
        
        if pd.notna(item.get('대상지 현황')) and str(item.get('대상지 현황')).strip() != 'nan':
            st.write("")
            st.markdown("<div style='text-align:left; font-size:0.85rem; font-weight:bold; color:#2ea043; margin-bottom:5px;'>📋 대상지 현황</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:left; font-size:0.9rem; line-height:1.6; color:var(--text-color); opacity:0.9;'>{str(item.get('대상지 현황'))}</div>", unsafe_allow_html=True)
            
        if pd.notna(item.get('현장의견')) and str(item.get('현장의견')).strip() != 'nan':
            st.write("")
            st.markdown("<div style='text-align:left; font-size:0.85rem; font-weight:bold; color:#2ea043; margin-bottom:5px;'>💬 현장 의견</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:left; font-size:0.9rem; line-height:1.6; color:var(--text-color); opacity:0.9;'>{str(item.get('현장의견'))}</div>", unsafe_allow_html=True)
            
        st.divider()
        
        st.markdown("<div style='text-align:left; font-size:0.85rem; font-weight:bold; color:#2ea043; margin-bottom:10px;'>📊 상세 속성 정보</div>", unsafe_allow_html=True)
        col_meta1, col_meta2 = st.columns(2)
        
        exclude_cols = ['명칭', '내용', '대상지 현황', '현장의견', '이미지경로', '동영상경로', '주소', 'ID', 'Lat', 'Lon']
        
        count = 0
        for col_name in item.index:
            if col_name in exclude_cols: continue
                
            val = item[col_name]
            if pd.isna(val) or str(val).strip() == '' or str(val) == 'nan' or str(val) == '·':
                val = "-"
                
            meta_str = f"<div style='text-align:left; font-size:0.85rem; color:var(--text-color); opacity:0.8;'>• <b>{col_name}</b>: {val}</div>"
            if count % 2 == 0:
                with col_meta1: st.markdown(meta_str, unsafe_allow_html=True)
            else:
                with col_meta2: st.markdown(meta_str, unsafe_allow_html=True)
            count += 1

# 개발 중 캐시 방지
def load_data(csv_path):
    if os.path.exists(csv_path):
        try: return pd.read_csv(csv_path, encoding='utf-8-sig')
        except UnicodeDecodeError: return pd.read_csv(csv_path, encoding='cp949')
    else:
        st.error(f"'{csv_path}' 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

# ==========================================
# 4. 메인 화면 구성
# ==========================================
def main():
    st.markdown("<h1>🌲 디지털 산림문화자원 아카이브 시범 구축</h1>", unsafe_allow_html=True)
    st.markdown("<p>데이터 기반 산림문화 갤러리 및 공간 검색 플랫폼</p>", unsafe_allow_html=True)
    st.write("") 

    col_empty1, col_video, col_empty2 = st.columns([1, 6, 1])
    with col_video:
        video_html = """
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 12px; border: 1px solid rgba(128,128,128,0.2); box-shadow: 0 10px 20px rgba(0,0,0,0.05);">
            <iframe src="https://www.youtube.com/embed/kx3zWy-C9a4?autoplay=1&mute=1&loop=1&playlist=kx3zWy-C9a4&controls=0&showinfo=0&rel=0"
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
            </iframe>
        </div>
        """
        st.markdown(video_html, unsafe_allow_html=True)
        st.caption("▲ 담양 메타세쿼이아 가로수길 (국가산림문화자산 지정번호 : 2015-0001)")
    
    st.write("")
    st.write("")

    CSV_FILE = 'test_ForestAsset_27_modify.csv'
    df = load_data(CSV_FILE)

    if df.empty: return

    with st.sidebar:
        st.markdown("### 🔍 산림문화자원 키워드 검색 필터")
        st.write("▼ 현지조사 보완자료 일부 제공")
        st.divider()
        search_query = st.text_input("통합 검색", placeholder="명칭, 주소, 설명 등...")
        
        categories = ["전체"] + list(df['지역'].dropna().unique()) if '지역' in df.columns else ["전체"]
        selected_category = st.selectbox("권역 필터", categories)
            
        sub_categories = ["전체"] + list(df['중분류'].dropna().unique()) if '중분류' in df.columns else ["전체"]
        selected_sub = st.selectbox("유형 필터", sub_categories)

    filtered_df = df.copy()
    if selected_category != "전체": filtered_df = filtered_df[filtered_df['지역'] == selected_category]
    if selected_sub != "전체": filtered_df = filtered_df[filtered_df['중분류'] == selected_sub]
    if search_query:
        filtered_df = filtered_df[
            filtered_df['명칭'].astype(str).str.contains(search_query, case=False, na=False) |
            filtered_df['내용'].astype(str).str.contains(search_query, case=False, na=False) |
            filtered_df['주소'].astype(str).str.contains(search_query, case=False, na=False)
        ]

    tab1, tab2, tab3, tab4 = st.tabs(["🖼️ 전체 자원 갤러리", "📊 유사 자원 검색 및 분석", "🗺️ 공간 지도 (V-World)", "📚 출처 정보"])

# [탭 1] 전체 갤러리 (요약 대시보드 포함)
with tab1:
    st.subheader("🌲 전체 산림문화자원 요약")
    c1, c2, c3 = st.columns(3)
    c1.metric("총 자원 수", len(df))
    c2.metric("권역 수", df['지역'].nunique())
    c3.metric("유형 수", df['중분류'].nunique())
    
    st.markdown("### 전체 자원 갤러리")
    # 캐러셀 형태로 4개씩 행 배치
    cols = st.columns(4)
    for i, row in df.head(8).iterrows():
        with cols[i % 4]:
            st.image("https://via.placeholder.com/300x200?text=Forest+Asset", use_column_width=True)
            st.write(f"**{row['명칭']}**")

# [탭 2] 유사 자원 검색 결과
with tab2:
    st.subheader("📊 필터 분석 및 유사 자원 탐색")
    with st.sidebar:
        query = st.text_input("유사 자원 검색")
        cat = st.selectbox("권역 선택", ["전체"] + list(df['지역'].unique()))
    
    filtered = df.copy()
    if cat != "전체": filtered = filtered[filtered['지역'] == cat]
    if query: filtered = filtered[filtered['명칭'].str.contains(query, na=False)]
    
    c_chart1, c_chart2 = st.columns(2)
    # 원 모양 차트 (Altair Arc)
    chart_data = filtered['지역'].value_counts().reset_index()
    c_chart1.altair_chart(alt.Chart(chart_data).mark_arc().encode(theta='count', color='index'), use_container_width=True)
    c_chart2.bar_chart(filtered['중분류'].value_counts())
    
    for _, row in filtered.iterrows():
        with st.container(border=True):
            cols = st.columns([1, 4])
            cols[0].image("https://via.placeholder.com/150x100", width=150)
            cols[1].write(f"**{row['명칭']}** | {row['지역']} | {row['중분류']}")

# [탭 3] 공간 지도 (V-World 스타일 설정)
with tab3:
    st.subheader("🗺️ 공간 탐색 (V-World Base Map)")
    # V-World 타일 URL 적용
    vworld_url = "http://xdworld.vworld.kr:8080/2d/Base/202002/{z}/{x}/{y}.png"
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles=vworld_url, attr="V-World")
    
    for _, row in filtered.dropna(subset=['Lat', 'Lon']).iterrows():
        folium.Marker([row['Lat'], row['Lon']], tooltip=row['명칭']).add_to(m)
    st_folium(m, width=1200, height=600)

# [탭 4] 출처 정보
with tab4:
    st.subheader("📚 관련 자료 출처")
    if '출처' in df.columns:
        st.dataframe(df[['명칭', '출처', '관련링크']], use_container_width=True)
    else:
        st.write("출처 정보가 포함된 데이터 컬럼이 없습니다.")
