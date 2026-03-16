import streamlit as st
import concurrent.futures
import data
import widget
import os

# 1. Cấu hình trang
st.set_page_config(layout="wide")

# 2. CSS (Giữ nguyên cấu trúc cũ)
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

st.markdown("<h1 style='text-align: center;'>Financial Dashboard</h1>", unsafe_allow_html=True)

# --- HÀM ĐỌC DANH SÁCH MÃ TỪ FILE TXT ---
def load_symbols_from_txt(file_path):
    if not os.path.exists(file_path):
        st.error(f"Không tìm thấy file {file_path}")
        return {}
    
    # Danh sách các mã vĩ mô/quốc tế cần giữ nguyên (không thêm .VN)
    MACRO_SYMBOLS = ["DX-Y.NYB", "USDVND=X", "^GSPC", "^N225", "GC=F", "CL=F", "VNM"]
    # Tên hiển thị thân thiện cho các mã vĩ mô
    FRIENDLY_NAMES = {
        "DX-Y.NYB": "Chỉ số DXY",
        "USDVND=X": "Tỷ giá USD/VND",
        "VNM": "VNM ETF (Proxy VN)",
        "^GSPC": "S&P 500 (Mỹ)",
        "^N225": "Nikkei 225 (Nhật)",
        "GC=F": "GIÁ VÀNG",
        "CL=F": "GIÁ DẦU WTI"
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\n', ',')
        raw_list = [s.strip().upper() for s in content.split(',') if s.strip()]
        
    stock_dict = {}
    for s in raw_list:
        # Nếu là mã vĩ mô
        if s in MACRO_SYMBOLS:
            display_name = FRIENDLY_NAMES.get(s, s)
            stock_dict[s] = (display_name, "#546e7a")
        # Nếu là cổ phiếu Việt Nam
        else:
            stock_dict[f"{s}.VN"] = (s, "#2e7d32")
            
    return stock_dict

# Tải danh sách từ file stocks.txt
STOCKS = load_symbols_from_txt("stocks.txt")
symbols = list(STOCKS.keys())

# --- THANH ĐIỀU KHIỂN ---
col_nav1, col_nav2 = st.columns([1, 1])
with col_nav1:
    st.selectbox("Ngành", ["Tất cả ngành", "Vĩ mô", "Ngân hàng", "Bất động sản", "Thép"], index=0)
with col_nav2:
    st.selectbox("Danh mục theo dõi", ["VN100 + Macro", "Ưu tiên"], index=0)

st.markdown("<hr style='width: 100%; margin: 10px auto;'>", unsafe_allow_html=True)

# --- TẢI DỮ LIỆU ĐA LUỒNG ---
@st.cache_data(ttl=600)
def load_all_data_concurrently(symbol_list):
    results = {}
    # Tăng workers lên 20 để tải 100+ mã nhanh nhất
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_symbol = {executor.submit(data.get_stock_data, sym, period="max"): sym for sym in symbol_list}
        for future in concurrent.futures.as_completed(future_to_symbol):
            sym = future_to_symbol[future]
            try:
                df_res = future.result()
                if df_res is not None and not df_res.empty:
                    results[sym] = df_res
            except Exception:
                pass
    return results

with st.spinner(f"Đang tải dữ liệu {len(symbols)} chỉ số & cổ phiếu..."):
    valid_stock_data = load_all_data_concurrently(symbols)

active_symbols = [s for s in symbols if s in valid_stock_data]

# --- HIỂN THỊ LƯỚI ---
for i in range(0, len(active_symbols), 3):
    cols = st.columns(3)
    for j in range(3):
        if i + j < len(active_symbols):
            symbol_key = active_symbols[i + j]
            display_name = STOCKS[symbol_key][0]
            df = valid_stock_data[symbol_key]
            
            with cols[j]:
                with st.container(border=True):
                    widget.create_stock_widget(df, display_name)
