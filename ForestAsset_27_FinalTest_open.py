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
    
    .stApp { font-family: 'Pretendard', 'Noto Sans KR', sans-serif; }
    
    h1 {
        color: var(--text-color) !important; font-weight: 800;
        letter-spacing: -0.5px; text-align: center; margin-bottom: 5px !important;
    }
    
    .stMarkdown p { text-align: center; color: var(--text-color); opacity: 0.8; font-size: 1.1em; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; padding-bottom: 10px; border-bottom: 2px solid rgba(128, 128, 128, 0.2); }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: var(--secondary-background-color);
        border-radius: 8px 8px 0px 0px; padding: 10px 24px; color: var(--text-color);
        opacity: 0.7; font-weight: 600; border: 1px solid rgba(128, 128, 128, 0.2);
        border-bottom: none; transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important; background-color: #2ea043 !important;
        border-color: #2ea043 !important; opacity: 1;
    }
    
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128, 128, 128, 0.2); }
    
    /* 2D 갤러리 카드 이미지 크기 강제 통일 및 고정 */
    .stImage img {
        height: 200px !important;
        object-fit: cover !important;
        border-radius: 8px;
        width: 100% !important;
    }
    
    .stButton > button {
        border-radius: 6px; border: 1px solid #2ea043; color: #2ea043;
        background-color: transparent; font-weight: 600; transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #2ea043; color: #FFFFFF; border-color: #2ea043; transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

def get_base64_of_image(image_path):
    if pd.notna(image_path) and os.path.exists(str(image_path)):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

def change_img_index(state_key, step, total_images):
    st.session_state[state_key] = (st.session_state[state_key] + step) % total_images

# ==========================================
# 2. 파이썬 전용 상세 팝업 모달창
# ==========================================
@st.dialog("자원 상세 정보", width="large")
def show_detail_modal(item):
    col_img, col_text = st.columns([1, 1.2]) 
    
    with col_img:
        img_paths_str = str(item.get('이미지경로', ''))
        valid_img_paths = [p.strip() for p in img_paths_str.split(',') if p.strip() and os.path.exists(p.strip())]
        
        if not valid_img_paths:
            st.image('https://via.placeholder.com/800x600?text=No+Image', use_container_width=True)
        elif len(valid_img_paths) == 1:
            st.image(valid_img_paths[0], use_container_width=True)
        else:
            item_id = str(item.name) 
            state_key = f"img_idx_{item_id}"
            if state_key not in st.session_state: st.session_state[state_key] = 0
            current_idx = st.session_state[state_key]
            
            st.image(valid_img_paths[current_idx], use_container_width=True)
            
            col_prev, col_lbl, col_next = st.columns([1, 1, 1])
            with col_prev: st.button("◀ 이전", key=f"prev_{item_id}", on_click=change_img_index, args=(state_key, -1, len(valid_img_paths)), use_container_width=True)
            with col_lbl: st.markdown(f"<div style='text-align:center; padding-top:10px; font-weight:bold;'>{current_idx + 1} / {len(valid_img_paths)}</div>", unsafe_allow_html=True)
            with col_next: st.button("다음 ▶", key=f"next_{item_id}", on_click=change_img_index, args=(state_key, 1, len(valid_img_paths)), use_container_width=True)
                
        vid_path = item.get('동영상경로', '') 
        if pd.notna(vid_path) and str(vid_path).strip() not in ['', 'nan']:
            st.write("") 
            st.markdown("<div style='text-align:left; font-size:0.85rem; font-weight:bold; color:#2ea043; margin-bottom:5px;'>🎥 관련 영상</div>", unsafe_allow_html=True)
            st.video(str(vid_path).strip())
            
    with col_text:
        st.markdown(f"<h3 style='margin-top:0;'>{str(item.get('명칭', '제목 없음'))}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:0.85rem; opacity:0.7; margin-bottom:15px;'>📍 {item.get('주소', '주소 미상')}</p>", unsafe_allow_html=True)
        st.divider()
        
        st.markdown("<div style='font-size:0.85rem; font-weight:bold; color:#2ea043; margin-bottom:5px;'>📖 자원 설명</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.9rem; line-height:1.6; opacity:0.9;'>{str(item.get('내용', '등록된 설명이 없습니다.'))}</div>", unsafe_allow_html=True)
        
        if pd.notna(item.get('대상지 현황')) and str(item.get('대상지 현황')).strip() != 'nan':
            st.write("")
            st.markdown("<div style='font-size:0.85rem; font-weight:bold; color:#2ea043; margin-bottom:5px;'>📋 대상지 현황</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.9rem; line-height:1.6; opacity:0.9;'>{str(item.get('대상지 현황'))}</div>", unsafe_allow_html=True)
            
        st.divider()
        
        st.markdown("<div style='font-size:0.85rem; font-weight:bold; color:#2ea043; margin-bottom:10px;'>📊 상세 속성 정보</div>", unsafe_allow_html=True)
        col_meta1, col_meta2 = st.columns(2)
        exclude_cols = ['명칭', '내용', '대상지 현황', '현장의견', '이미지경로', '동영상경로', '주소', 'ID', 'Lat', 'Lon', '출처', '문헌자료', '관련링크']
        
        count = 0
        for col_name in item.index:
            if col_name in exclude_cols: continue
            val = item[col_name]
            if pd.isna(val) or str(val).strip() in ['', 'nan', '·']: val = "-"
                
            meta_str = f"<div style='font-size:0.85rem; opacity:0.8;'>• <b>{col_name}</b>: {val}</div>"
            if count % 2 == 0:
                with col_meta1: st.markdown(meta_str, unsafe_allow_html=True)
            else:
                with col_meta2: st.markdown(meta_str, unsafe_allow_html=True)
            count += 1

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

    # 4개 탭 정의 (탭1 이름 업데이트)
    tab1, tab2, tab3, tab4 = st.tabs(["🧊 하이라이트 전시관", "📊 분석 및 유사 자원", "🗺️ 공간 탐색 (Map)", "📚 출처 정보"])

    item_to_show = None

    # [탭 1] 하이라이트 전시관 (검색 적용 안 됨, 상단 전체 요약 표기)
    with tab1:
        st.write("")
        st.markdown("### 🌲 하이라이트 전시관")
        
        # 상단 전체 요약 정보 표기 (필터링되지 않은 원본 df 기준)
        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric("총 자원 수", len(df))
        col_k2.metric("권역 분포", df['지역'].nunique() if '지역' in df.columns else 0)
        col_k3.metric("자원 유형", df['중분류'].nunique() if '중분류' in df.columns else 0)
        st.divider()
        
        # 검색 필터링의 영향을 받지 않도록 원본 df의 상위 10개 고정 표출
        display_df = df.head(10)
        image_tags = ""
        js_data = [] 
        num_items = len(display_df)
        angle_step = 360 / num_items if num_items > 0 else 0
        translate_z = 480 

        for i, row in display_df.iterrows():
            img_paths_str = str(row.get('이미지경로', ''))
            first_img = img_paths_str.split(',')[0].strip() if img_paths_str else ''
            base64_str = get_base64_of_image(first_img)
            img_src = f"data:image/jpeg;base64,{base64_str}" if base64_str else "https://via.placeholder.com/300x400?text=No+Image"
            
            title = str(row.get("명칭", "")).replace("'", "\\'").replace('"', '&quot;')
            addr = str(row.get("주소", "")).replace("'", "\\'").replace('"', '&quot;')
            desc = str(row.get("내용", "")).replace("'", "\\'").replace('"', '&quot;').replace("\n", "<br>")
            
            js_data.append(f"{{ title: '{title}', addr: '{addr}', desc: '{desc}', img: '{img_src}' }}")

            style = f"transform: rotateY({i * angle_step}deg) translateZ({translate_z}px);"
            image_tags += f'<div class="carousel-item" style="{style}" onclick="openModal({i})"><img src="{img_src}"><div class="title">{title}</div></div>'

        js_array_str = "[\n" + ",\n".join(js_data) + "\n]"

        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
            :root {{
                --bg-1: #ffffff; --bg-2: #f0f2f5; --card-bg: #ffffff; --text-main: #222222;
                --text-desc: #444444; --text-muted: #888888; --border-color: #eaeaea; --primary-green: #2ea043;
            }}
            @media (prefers-color-scheme: dark) {{
                :root {{
                    --bg-1: #0E1117; --bg-2: #1E1E1E; --card-bg: #262730; --text-main: #FAFAFA;
                    --text-desc: #DDDDDD; --text-muted: #AAAAAA; --border-color: #444444;
                }}
            }}
            body {{ 
                margin: 0; display: flex; flex-direction: column; align-items: center; 
                justify-content: center; height: 100vh; 
                background: radial-gradient(circle at center, var(--bg-1) 0%, var(--bg-2) 100%); 
                overflow: hidden; font-family: 'Noto Sans KR', sans-serif; color: var(--text-main);
            }}
            .scene {{ width: 300px; height: 400px; perspective: 1400px; margin-bottom: 80px; }}
            .carousel {{ width: 100%; height: 100%; position: absolute; transform-style: preserve-3d; transition: transform 0.8s cubic-bezier(0.25, 1, 0.5, 1); }}
            .carousel-item {{ 
                position: absolute; width: 280px; height: 380px; left: 10px; top: 10px; 
                border-radius: 12px; box-shadow: 0 15px 35px rgba(0,0,0,0.15); 
                background: var(--card-bg); text-align: center; backface-visibility: hidden; 
                border: 1px solid var(--border-color); cursor: pointer; transition: all 0.2s ease; 
            }}
            .carousel-item:hover {{ border: 2px solid var(--primary-green); transform: scale(1.02); }}
            .carousel-item img {{ width: 100%; height: 300px; object-fit: cover; border-top-left-radius: 12px; border-top-right-radius: 12px; }}
            .carousel-item .title {{ padding: 18px 15px; font-weight: 700; font-size: 16px; pointer-events: none; }}
            .controls-wrapper {{ position: absolute; bottom: 40px; display: flex; gap: 20px; z-index: 100; }}
            button {{ 
                padding: 14px 30px; font-size: 15px; cursor: pointer; border: none; border-radius: 50px; 
                background-color: var(--primary-green); color: white; font-weight: 700; 
                box-shadow: 0 8px 20px rgba(46, 160, 67, 0.3); transition: all 0.2s ease; display: flex; align-items: center; gap: 8px; 
            }}
            button:hover {{ background-color: #238636; transform: translateY(-3px); }}
            
            .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.6); backdrop-filter: blur(3px); }}
            .modal-content {{ background-color: var(--card-bg); margin: 3% auto; padding: 25px 35px; width: 85%; max-width: 600px; border-radius: 12px; box-shadow: 0 5px 30px rgba(0,0,0,0.3); max-height: 85vh; overflow-y: auto; position: relative; }}
            .close {{ color: var(--text-muted); position: absolute; top: 15px; right: 20px; font-size: 28px; font-weight: bold; cursor: pointer; }}
            .close:hover {{ color: var(--text-main); }}
            .modal-img {{ width: 100%; height: 260px; object-fit: cover; border-radius: 8px; margin-bottom: 20px; }}
            .modal-title {{ font-size: 22px; font-weight: bold; margin: 0 0 5px 0; }}
            .modal-addr {{ font-size: 13px; color: var(--text-muted); margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; }}
            .modal-desc-title {{ font-size: 13px; color: var(--primary-green); font-weight: bold; margin-bottom: 5px; }}
            .modal-desc {{ font-size: 14px; color: var(--text-desc); line-height: 1.6; }}
        </style>
        </head>
        <body>
        <div class="scene"><div class="carousel" id="carousel">{image_tags}</div></div>
        <div class="controls-wrapper">
            <button onclick="rotate(-1)">◀ PREV</button>
            <button onclick="rotate(1)">NEXT ▶</button>
        </div>
        <div id="modal" class="modal" onclick="if(event.target==this) closeModal()">
            <div class="modal-content">
                <span class="close" onclick="closeModal()">&times;</span>
                <img id="modal-img" class="modal-img" src="">
                <h2 id="modal-title" class="modal-title"></h2>
                <div id="modal-addr" class="modal-addr"></div>
                <div class="modal-desc-title">📖 자원 설명</div>
                <div id="modal-desc" class="modal-desc"></div>
            </div>
        </div>
        <script>
            let currentAngle = 0; const angleStep = {angle_step};
            function rotate(dir) {{ currentAngle += dir * angleStep; document.getElementById('carousel').style.transform = `rotateY(${{-currentAngle}}deg)`; }}
            const assetData = {js_array_str};
            function openModal(index) {{
                const data = assetData[index];
                document.getElementById('modal-img').src = data.img;
                document.getElementById('modal-title').innerText = data.title;
                document.getElementById('modal-addr').innerText = "📍 " + data.addr;
                document.getElementById('modal-desc').innerHTML = data.desc;
                document.getElementById('modal').style.display = "block";
            }}
            function closeModal() {{ document.getElementById('modal').style.display = "none"; }}
        </script>
        </body>
        </html>
        """
        components.html(html_code, height=750)

    # [탭 2] 분석 및 유사 자원 (컨트롤 상단 배치 및 2D 카드 이미지 균일화)
    with tab2:
        st.write("")
        st.subheader("📊 산림문화자원 분석 및 탐색 대시보드")
        
        if filtered_df.empty:
            st.info("검색 조건에 일치하는 자원이 없습니다.")
        else:
            # 깔끔하게 다듬어진 디자인 차트 (도넛 & 바 차트)
            c1, c2 = st.columns(2)
            if '지역' in filtered_df.columns:
                arc_data = filtered_df['지역'].value_counts().reset_index()
                arc_data.columns = ['Category', 'Count']
                
                arc_chart = alt.Chart(arc_data).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta('Count:Q'),
                    color=alt.Color('Category:N', legend=alt.Legend(title="권역")),
                    tooltip=['Category', 'Count']
                ).properties(width=300, height=300, title="권역 분포 (원형)")
                
                c1.altair_chart(arc_chart, use_container_width=True)
                
            if '중분류' in filtered_df.columns:
                bar_data = filtered_df['중분류'].value_counts().reset_index()
                bar_data.columns = ['Category', 'Count']
                
                bar_chart = alt.Chart(bar_data).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color='#2ea043').encode(
                    x=alt.X('Category:N', title="", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('Count:Q', title="자원 수"),
                    tooltip=['Category', 'Count']
                ).properties(width=300, height=300, title="유형 분포 (바형)")
                
                c2.altair_chart(bar_chart, use_container_width=True)

            st.divider()
            
            # ★ 조작 컨트롤을 타이틀 우측 옆으로 정렬하기 위한 컬럼 스플릿
            title_col, btn_prev_col, btn_next_col = st.columns([4, 1, 1])
            with title_col:
                st.markdown("### 🖼️ 유사 자원 탐색 갤러리")
            
            if 'carousel_t2_pos' not in st.session_state: st.session_state.carousel_t2_pos = 0
            start = st.session_state.carousel_t2_pos
            
            with btn_prev_col:
                if st.button("◀ 이전 리스트", key="prev_t2_top", use_container_width=True):
                    st.session_state.carousel_t2_pos = max(0, start - 4)
                    st.rerun()
            with btn_next_col:
                if st.button("다음 리스트 ▶", key="next_t2_top", use_container_width=True):
                    st.session_state.carousel_t2_pos = min(max(0, len(filtered_df) - 4), start + 4)
                    st.rerun()
            
            visible_items = filtered_df.iloc[start : start + 4] # 2D 형태로 한 행에 4개 배치
            
            cols = st.columns(4)
            for i, (idx, row) in enumerate(visible_items.iterrows()):
                with cols[i]:
                    with st.container():
                        img_paths_str = str(row.get('이미지경로', ''))
                        first_img = img_paths_str.split(',')[0].strip() if img_paths_str else ''
                        
                        # 스타일 시트 적용으로 높이(200px) 자동 균일화 적용됨
                        if first_img and os.path.exists(first_img): st.image(first_img, use_container_width=True)
                        else: st.image('https://via.placeholder.com/400x300?text=No+Image', use_container_width=True)
                        
                        st.markdown(f"**{str(row.get('명칭', ''))}**")
                        st.caption(f"📍 {row.get('지역', '')} | 🏷️ {row.get('중분류', '')}")
                        
                        if st.button("상세 정보 열람", key=f"btn_detail_t2_{row.name}", use_container_width=True):
                            item_to_show = row
                        st.write("")

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
                    zoom_start=7, tiles=vworld_tiles, attr="VWorld"
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

    # [탭 4] 출처 정보 (출처, 문헌자료, 관련링크 표기)
    with tab4:
        st.write("")
        st.subheader("📚 연관 자료 출처 및 문헌 정보")
        
        display_cols = ['명칭']
        for col in ['출처', '문헌자료', '관련링크']:
            if col in filtered_df.columns:
                display_cols.append(col)
                
        st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)

    # 2D 갤러리 및 지도 연동 상세 팝업 모달창 오픈
    if item_to_show is not None:
        show_detail_modal(item_to_show)

if __name__ == "__main__":
    main()
