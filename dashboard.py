import streamlit as st
import concurrent.futures
import data
import widget
import os
import re
import time

# 1. Cấu hình trang
st.set_page_config(layout="wide", page_title="Financial Dashboard")

# 2. Khởi tạo Session State cho tính năng Load More
if 'display_limit' not in st.session_state:
    st.session_state.display_limit = 12

# --- HÀM TAB CÀI ĐẶT (POP-UP) ---
@st.dialog("Cài đặt", width="small")
def settings_dialog():
    st.markdown("### 🎨 Tùy chỉnh Giao diện")
    
    config_path = ".streamlit/config.toml"
    current_theme = "dark" # Mặc định
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
            if 'base="light"' in content or "base='light'" in content:
                current_theme = "light"
                
    theme_choice = st.radio(
        "Chọn chế độ hiển thị:", 
        options=["Sáng (Light)", "Tối (Dark)"], 
        index=0 if current_theme == "light" else 1
    )
    
    if st.button("Lưu và Áp dụng", use_container_width=True):
        new_theme = "light" if "Light" in theme_choice else "dark"
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_content = f.read()
        else:
            config_content = "[client]\nshowSidebarNavigation = false\ntoolbarMode = \"minimal\"\n"
            
        if "[theme]" in config_content:
            if re.search(r'base\s*=\s*["\'].*["\']', config_content):
                config_content = re.sub(r'base\s*=\s*["\'].*["\']', f'base="{new_theme}"', config_content)
            else:
                config_content = config_content.replace("[theme]", f"[theme]\nbase=\"{new_theme}\"")
        else:
            config_content += f"\n[theme]\nbase=\"{new_theme}\"\n"
            
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)
            
        time.sleep(0.2) 
        st.rerun()

# 3. CSS fix giao diện để các ô cân đối và style nút bấm
st.markdown("""
    <style>
        /* TRIỆT TIÊU HEADER VÀ BREADCRUMBS (LINK THỪA KẾ TIÊU ĐỀ) */
        header, [data-testid="stHeader"], .stAppHeader, [data-testid="stHeaderNav"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }
        
        /* Xóa khoảng trắng thừa ở đầu trang */
        .block-container {
            padding-top: 2rem !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            background-color: rgba(255, 255, 255, 0.02);
            padding: 15px;
            height: 100%;
        }
        
        div[data-testid="stPageLink"], 
        div[data-testid="stButton"] {
            margin: 0 !important;
            padding: 0 !important;
            height: 40px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        a[data-testid="stPageLink-NavLink"], 
        button[data-testid="baseButton-secondary"] {
            border: 1px solid rgba(33, 150, 243, 0.6) !important;
            background-color: rgba(33, 150, 243, 0.1) !important;
            border-radius: 8px !important;
            text-align: center !important;
            justify-content: center !important;
            align-items: center !important;
            font-weight: bold !important;
            transition: all 0.2s ease-in-out !important;
            color: inherit !important;
            padding: 0 !important;
            display: flex !important;
            width: 100% !important;
            box-sizing: border-box !important;
            height: 40px !important;       
            min-height: 40px !important; 
            max-height: 40px !important; 
        }
        
        button[data-testid="baseButton-secondary"] p,
        a[data-testid="stPageLink-NavLink"] p {
            margin: 0 !important;
            padding: 0 !important;
            font-size: 15px !important;
            line-height: 40px !important; 
            display: block !important;
        }

        a[data-testid="stPageLink-NavLink"]:hover, 
        button[data-testid="baseButton-secondary"]:hover {
            border: 1px solid rgba(33, 150, 243, 1) !important;
            background-color: rgba(33, 150, 243, 0.25) !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Financial Dashboard</h1>", unsafe_allow_html=True)

# --- ĐIỀU HƯỚNG TRANG (NÚT CHUYỂN TRANG & CÀI ĐẶT) ---
st.markdown("<br>", unsafe_allow_html=True)
# Chia lại 6 cột để thêm nút Tin Tức
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns([0.5, 1.5, 1.5, 1.5, 1.5, 0.5], vertical_alignment="center")

with nav_col2:
    if os.path.exists("pages/1_ai_recommendation.py"):
        st.page_link("pages/1_ai_recommendation.py", label="AI Recommendation", use_container_width=True)
    else:
        st.button("AI Recommendation", disabled=True, use_container_width=True)

with nav_col3:
    if os.path.exists("pages/2_backtest.py"):
        st.page_link("pages/2_backtest.py", label="Backtest", use_container_width=True)
    else:
        st.button("Backtest", disabled=True, use_container_width=True)

with nav_col4:
    if os.path.exists("pages/3_news.py"):
        st.page_link("pages/3_news.py", label="Tin Tức", use_container_width=True)
    else:
        st.button("Tin Tức", disabled=True, use_container_width=True)

with nav_col5:
    if st.button("Cài đặt", use_container_width=True):
        settings_dialog()
        
st.markdown("<br>", unsafe_allow_html=True)

# --- HÀM ĐỌC MÃ TỪ FILE ---
def load_full_config(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().replace('\n', ',').split(',')
    
    stock_info = {} 
    MACRO_LIST = ["DX-Y.NYB", "USDVND=X", "^GSPC", "^N225", "GC=F", "CL=F", "BZ=F", "NG=F", "HG=F", "HRC=F", "TIO=F"]
    FRIENDLY = {
        "DX-Y.NYB": "DXY", "USDVND=X": "USD/VND", "GC=F": "VÀNG", 
        "CL=F": "DẦU WTI", "BZ=F": "DẦU BRENT", "NG=F": "KHÍ TỰ NHIÊN", 
        "HG=F": "ĐỒNG", "HRC=F": "THÉP HRC", "TIO=F": "QUẶNG SẮT", 
        "^GSPC": "S&P 500", "^N225": "NIKKEI 225"
    }

    for item in lines:
        if not item.strip(): continue
        parts = item.split('|')
        symbol_raw = parts[0].strip().upper()
        sector = parts[1].strip() if len(parts) > 1 else "Khác"
        category = parts[2].strip() if len(parts) > 2 else "VN100"

        if symbol_raw in MACRO_LIST:
            full_symbol = symbol_raw
            display_name = FRIENDLY.get(symbol_raw, symbol_raw)
            sector = "Vĩ mô"
            category = "Vĩ mô"
        else:
            full_symbol = f"{symbol_raw}.VN"
            display_name = symbol_raw
            
        stock_info[full_symbol] = {"name": display_name, "sector": sector, "category": category}
    return stock_info

STOCKS_INFO = load_full_config("stocks.txt")

# --- THANH LỌC TRÊN DASHBOARD ---
ALL_SECTORS = sorted(list(set(info['sector'] for info in STOCKS_INFO.values())))
if "Vĩ mô" in ALL_SECTORS: ALL_SECTORS.remove("Vĩ mô")
ALL_SECTORS = ["Tất cả", "Vĩ mô"] + ALL_SECTORS

col_nav1, col_nav2, col_nav3 = st.columns([0.4, 0.4, 0.2], vertical_alignment="bottom")
with col_nav1:
    selected_sector = st.selectbox("Lọc theo Ngành", options=ALL_SECTORS)
with col_nav2:
    selected_category = st.selectbox("Danh mục hiển thị", options=["VN100", "VN30"])
with col_nav3:
    search_query = st.text_input("🔍 Tìm kiếm mã...", "")

if 'last_sector' not in st.session_state: st.session_state.last_sector = selected_sector
if 'last_category' not in st.session_state: st.session_state.last_category = selected_category
if 'last_search' not in st.session_state: st.session_state.last_search = search_query

if (selected_sector != st.session_state.last_sector or 
    selected_category != st.session_state.last_category or 
    search_query != st.session_state.last_search):
    st.session_state.display_limit = 12
    st.session_state.last_sector = selected_sector
    st.session_state.last_category = selected_category
    st.session_state.last_search = search_query

st.markdown("<hr>", unsafe_allow_html=True)

# --- TẢI DỮ LIỆU ĐA LUỒNG ---
@st.cache_data(ttl=1800)
def load_all_data(symbol_list):
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_symbol = {executor.submit(data.get_stock_data, sym): sym for sym in symbol_list}
        for future in concurrent.futures.as_completed(future_to_symbol):
            sym = future_to_symbol[future]
            df = future.result()
            if df is not None and not df.empty:
                results[sym] = df
    return results

with st.spinner("Đang tải dữ liệu..."):
    all_data = load_all_data(list(STOCKS_INFO.keys()))

# --- LOGIC LỌC DỮ LIỆU ---
filtered_symbols = []
for sym, info in STOCKS_INFO.items():
    if sym not in all_data: continue
    
    match_cat = False
    if selected_category == "VN100": match_cat = True
    elif selected_category == "VN30":
        if "VN30" in info['category']: match_cat = True

    match_sector = (selected_sector == "Tất cả") or (info['sector'] == selected_sector)
    if info['sector'] == "Vĩ mô" and selected_sector == "Vĩ mô": match_cat = True

    match_search = True
    if search_query:
        if search_query.upper() not in sym.upper() and search_query.upper() not in info['name'].upper():
            match_search = False

    if match_cat and match_sector and match_search:
        filtered_symbols.append(sym)

# --- HIỂN THỊ LƯỚI ---
if not filtered_symbols:
    st.info("Không tìm thấy mã nào phù hợp với bộ lọc hiện tại.")
else:
    display_symbols = filtered_symbols[:st.session_state.display_limit]
    for i in range(0, len(display_symbols), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(display_symbols):
                sym_key = display_symbols[i + j]
                display_name = STOCKS_INFO[sym_key]['name']
                df_stock = all_data[sym_key]
                with cols[j]:
                    with st.container(border=True):
                        widget.create_stock_widget(df_stock, display_name)

    if st.session_state.display_limit < len(filtered_symbols):
        st.markdown("<br>", unsafe_allow_html=True)
        cols_btn = st.columns([1, 2, 1])
        with cols_btn[1]:
            if st.button("👇 Tải thêm các mã khác", use_container_width=True):
                st.session_state.display_limit += 12
                st.rerun()
