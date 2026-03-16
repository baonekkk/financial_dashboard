import streamlit as st
import concurrent.futures
import data
import widget
import os

# 1. Cấu hình trang
st.set_page_config(layout="wide", page_title="Financial Dashboard")

# 2. Khởi tạo Session State cho tính năng Load More
if 'display_limit' not in st.session_state:
    st.session_state.display_limit = 12

# 3. CSS fix giao diện để các ô cân đối
st.markdown("""
    <style>
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            background-color: rgba(255, 255, 255, 0.02);
            padding: 15px;
            height: 100%;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Thị Trường Tài Chính VN</h1>", unsafe_allow_html=True)

# --- HÀM ĐỌC MÃ TỪ FILE ---
def load_full_config(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().replace('\n', ',').split(',')
    
    stock_info = {} 
    
    # Đã bổ sung HRC, Quặng sắt và các loại hàng hóa khác
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

col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    selected_sector = st.selectbox("Lọc theo Ngành", options=ALL_SECTORS)
with col_nav2:
    selected_category = st.selectbox("Danh mục hiển thị", options=["VN100", "VN30"])

# Reset lại số lượng hiển thị (về 12) nếu người dùng chọn bộ lọc khác
if 'last_sector' not in st.session_state: st.session_state.last_sector = selected_sector
if 'last_category' not in st.session_state: st.session_state.last_category = selected_category

if selected_sector != st.session_state.last_sector or selected_category != st.session_state.last_category:
    st.session_state.display_limit = 12
    st.session_state.last_sector = selected_sector
    st.session_state.last_category = selected_category

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
    if selected_category == "VN100":
        match_cat = True
    elif selected_category == "VN30":
        if "VN30" in info['category']: 
            match_cat = True

    match_sector = (selected_sector == "Tất cả") or (info['sector'] == selected_sector)
    
    if info['sector'] == "Vĩ mô" and selected_sector == "Vĩ mô":
        match_cat = True

    if match_cat and match_sector:
        filtered_symbols.append(sym)

# --- HIỂN THỊ LƯỚI 3 CỘT (CỘNG DỒN MƯỢT MÀ) ---
if not filtered_symbols:
    st.info("Không tìm thấy mã nào phù hợp với bộ lọc hiện tại.")
else:
    # Chỉ lấy danh sách mã theo giới hạn hiện tại
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

    # Nút Hiển thị thêm (Chỉ hiện nếu vẫn còn mã chưa hiển thị hết)
    if st.session_state.display_limit < len(filtered_symbols):
        st.markdown("<br>", unsafe_allow_html=True)
        cols_btn = st.columns([1, 2, 1]) # Ép nút vào giữa cho đẹp
        with cols_btn[1]:
            if st.button("👇 Tải thêm các mã khác", use_container_width=True):
                st.session_state.display_limit += 12 # Tăng giới hạn lên 12 mã
                st.rerun() # Load lại luồng chạy để hiển thị thêm
