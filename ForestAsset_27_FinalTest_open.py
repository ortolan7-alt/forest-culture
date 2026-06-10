import streamlit as st
import pandas as pd
import os
import math
import base64
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

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
    st.markdown("<p>데이터 기반 2D/3D 시각화 및 공간 검색 플랫폼</p>", unsafe_allow_html=True)
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

    tab1, tab2, tab3 = st.tabs(["🖼️ 2D 자원 갤러리", "🧊 3D 하이라이트 전시", "🗺️ 공간 탐색 (Map)"])

    item_to_show = None

    # [탭 1] 2D 갤러리 검색
    with tab1:
        st.write("")
        ITEMS_PER_PAGE = 10
        total_items = len(filtered_df)
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

        col_info, _, col_page = st.columns([2, 5, 1])
        with col_info: st.markdown(f"<span style='color:var(--text-color); font-weight:bold;'>총 {total_items}건</span>의 자원 검색 완료", unsafe_allow_html=True)
        with col_page: current_page = st.selectbox("페이지", range(1, total_pages + 1), label_visibility="collapsed") if total_pages > 1 else 1
        st.divider()

        start_idx = (current_page - 1) * ITEMS_PER_PAGE
        paged_df = filtered_df.iloc[start_idx : start_idx + ITEMS_PER_PAGE]

        num_columns = 4 
        for i in range(0, len(paged_df), num_columns):
            cols = st.columns(num_columns)
            for j, col in enumerate(cols):
                if i + j < len(paged_df):
                    item = paged_df.iloc[i + j]
                    with col:
                        with st.container():
                            img_paths_str = str(item.get('이미지경로', ''))
                            first_img = img_paths_str.split(',')[0].strip() if img_paths_str else ''
                            
                            # ★ 2D 카드 이미지/버튼도 width='stretch' 로 적용
                            if first_img and os.path.exists(first_img): st.image(first_img, width='stretch')
                            else: st.image('https://via.placeholder.com/400x300?text=No+Image', width='stretch')
                            
                            st.markdown(f"**{str(item.get('명칭', ''))}**")
                            st.caption(f"📍 {item.get('지역', '')} | 🏷️ {item.get('중분류', '')}")
                            
                            if st.button("상세 정보 열람", key=f"btn_detail_{item.name}", width='stretch'):
                                item_to_show = item
                            st.write("")

    # [탭 2] 3D 전시 하이라이트 (최적화 버전)
    with tab2:
        st.write("")
        display_df = filtered_df.head(10)
        
        if display_df.empty:
            st.info("검색된 자원이 없습니다.")
        else:
            image_tags = ""
            js_data = [] 
            num_items = len(display_df)
            angle_step = 360 / num_items if num_items > 0 else 0
            
            for i, (idx, row) in enumerate(display_df.iterrows()):
                img_src = get_base64_of_image(str(row.get('이미지경로', '')).split(',')[0].strip())
                img_src = f"data:image/jpeg;base64,{img_src}" if img_src else "https://via.placeholder.com/300x400?text=No+Image"
                
                title = str(row.get("명칭", "")).replace("'", "\\'")
                
                # 클릭 시 ID를 쿼리 파라미터로 전달하여 파이썬과 통신
                style = f"transform: rotateY({i * angle_step}deg) translateZ(480px);"
                image_tags += f'''
                <div class="carousel-item" style="{style}" onclick="window.parent.location.href='?selected_id={idx}'">
                    <img src="{img_src}" style="width:100%; height:300px; object-fit:cover; border-radius:12px 12px 0 0;">
                    <div style="padding:15px; font-weight:700;">{title}</div>
                </div>'''

            st.components.v1.html(f'''
            <div style="height:500px; perspective:1400px; display:flex; flex-direction:column; align-items:center;">
                <div id="carousel" style="width:280px; height:380px; transform-style:preserve-3d; transition:0.8s;">{image_tags}</div>
                <div style="margin-top:100px;">
                    <button onclick="rotate(-1)">◀ 이전</button>
                    <button onclick="rotate(1)">다음 ▶</button>
                </div>
            </div>
            <script>
                let cur = 0;
                function rotate(dir) {{ cur += dir * {angle_step}; document.getElementById('carousel').style.transform = 'rotateY(' + (-cur) + 'deg)'; }}
            </script>
            ''', height=600)

    # 파이썬에서 ID 감지 및 팝업 호출 (탭 이동 시에도 항상 동작)
    if "selected_id" in st.query_params:
        target_idx = int(st.query_params["selected_id"])
        if target_idx in df.index:
            target_row = df.loc[target_idx]
            st.query_params.clear() # URL 초기화
            show_detail_modal(target_row)
            
    # [탭 3] Map 공간 탐색 (VWorld 맵)
    with tab3:
        st.write("")
        if 'Lat' in filtered_df.columns and 'Lon' in filtered_df.columns:
            map_data = filtered_df[['명칭', 'Lat', 'Lon']].copy()
            map_data['Lat'] = pd.to_numeric(map_data['Lat'], errors='coerce')
            map_data['Lon'] = pd.to_numeric(map_data['Lon'], errors='coerce')
            map_data = map_data.dropna()
            
            if not map_data.empty:
                map_data = map_data.rename(columns={'Lat': 'lat', 'Lon': 'lon'})
                
                vworld_tiles = "https://xdworld.vworld.kr/2d/Base/service/{z}/{x}/{y}.png"
                
                m = folium.Map(
                    location=[map_data['lat'].mean(), map_data['lon'].mean()],
                    zoom_start=7,
                    tiles=vworld_tiles,
                    attr="VWorld"
                )

                for idx, row in map_data.iterrows():
                    folium.Marker(
                        location=[row['lat'], row['lon']],
                        tooltip=row['명칭'],
                        icon=folium.Icon(color='green', icon='leaf')
                    ).add_to(m)

                map_event = st_folium(m, width=1200, height=600, returned_objects=["last_object_clicked"])

                if map_event and map_event.get("last_object_clicked"):
                    clicked_lat = map_event["last_object_clicked"]["lat"]
                    clicked_lon = map_event["last_object_clicked"]["lng"]

                    tolerance = 1e-4
                    matched = map_data[
                        (abs(map_data['lat'] - clicked_lat) < tolerance) &
                        (abs(map_data['lon'] - clicked_lon) < tolerance)
                    ]

                    if not matched.empty:
                        original_idx = matched.index[0]
                        if st.session_state.get('last_map_sel') != original_idx:
                            st.session_state['last_map_sel'] = original_idx
                            item_to_show = df.loc[original_idx]
                    else:
                        st.session_state['last_map_sel'] = None
            else:
                st.warning("현재 필터링된 결과에 유효한 좌표 데이터가 없습니다.")
        else:
            st.info("지도 표시를 위한 위경도 데이터가 없습니다.")

    if item_to_show is not None:
        show_detail_modal(item_to_show)

if __name__ == "__main__":
    main()
