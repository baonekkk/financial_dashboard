import streamlit as st
import concurrent.futures
import data
import widget

# 1. Cấu hình trang hiển thị rộng
st.set_page_config(layout="wide")

# 2. Nhúng CSS để tạo style cho widget và khắc phục lỗi lệch chiều dọc
st.markdown("""
    <style>
        /* Tùy chỉnh các khối container có border của Streamlit */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px; /* Độ bo góc */
            border: 1px solid rgba(255, 255, 255, 0.2) !important; /* Độ đậm của biên giới */
            background-color: rgba(255, 255, 255, 0.02); /* Nền nhẹ để tách biệt ô */
            padding: 15px;
            height: 100%; /* Ép các ô tự động kéo dài bằng nhau */
        }
    </style>
""", unsafe_allow_html=True)

# Căn giữa tiêu đề bằng HTML
st.markdown("<h1 style='text-align: center;'>Dashboard Tài Chính</h1>", unsafe_allow_html=True)

# Căn giữa đường kẻ ngang
st.markdown("<hr style='width: 100%; margin: 10px auto;'>", unsafe_allow_html=True)

# Danh sách mã chứng khoán và thông tin hiển thị
STOCKS = {
    "DX-Y.NYB": ("Chỉ số DXY", "#546e7a", "Điểm"),
    "USDVND=X": ("Tỷ giá USD/VND", "#2e7d32", "VND"),
    "VNM": ("VN-Index Proxy (VNM ETF)", "#e65100", "USD"),
    "^GSPC": ("S&P 500", "#1b5e20", "USD"),
    "^N225": ("Nikkei 225", "#b71c1c", "JPY"),
    "GC=F": ("GIÁ VÀNG", "#6a0dad", "USD/Ounce"),
    "CL=F": ("GIÁ DẦU WTI", "#008080", "USD/Thùng"),
    "VCB.VN": ("VCB (Ngân hàng)", "#004d40", "VND"),
    "BID.VN": ("BID (Ngân hàng)", "#0d47a1", "VND"),
    "CTG.VN": ("CTG (Ngân hàng)", "#1565c0", "VND"),
    "MBB.VN": ("MBB (Ngân hàng)", "#1976d2", "VND"),
    "TCB.VN": ("TCB (Ngân hàng)", "#c62828", "VND"),
    "SSI.VN": ("SSI (Chứng khoán)", "#ef6c00", "VND"),
    "HPG.VN": ("HPG (Thép)", "#455a64", "VND"),
    "PLX.VN": ("PLX (Dầu khí)", "#0277bd", "VND"),
    "BSR.VN": ("BSR (Dầu khí)", "#01579b", "VND"),
    "PVT.VN": ("PVT (Vận tải & Dầu khí)", "#2e7d32", "VND"),
    "GMD.VN": ("GMD (Logistics)", "#37474f", "VND"),
    "GEX.VN": ("GEX (Đa ngành)", "#5d4037", "VND"),
    "CII.VN": ("CII (Hạ tầng)", "#283593", "VND"),
    "VCG.VN": ("VCG (Xây dựng)", "#4e342e", "VND"),
    "MWG.VN": ("MWG (Bán lẻ)", "#fbc02d", "VND"),
    "FPT.VN": ("FPT (Công nghệ)", "#303f9f", "VND"),
    "DXG.VN": ("DXG (Bất động sản)", "#7b1fa2", "VND"),
    "DIG.VN": ("DIG (Bất động sản)", "#8e24aa", "VND"),
    "VIC.VN": ("VIC (Bất động sản)", "#d81b60", "VND"),
    "VRE.VN": ("VRE (Bất động sản)", "#c2185b", "VND"),
    "GEL.VN": ("GEL (Thiết bị điện)", "#4caf50", "VND"),
    "TCX.VN": ("TCX (Chứng khoán)", "#ef6c00", "VND")
}

symbols = list(STOCKS.keys())

# --- HÀM TẢI DỮ LIỆU ĐA LUỒNG ---
@st.cache_data(ttl=3600)
def load_all_data_concurrently(symbol_list):
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_symbol = {executor.submit(data.get_stock_data, sym, period="max"): sym for sym in symbol_list}
        for future in concurrent.futures.as_completed(future_to_symbol):
            sym = future_to_symbol[future]
            try:
                df_res = future.result()
                # Chỉ đưa vào kết quả nếu DataFrame có dữ liệu
                if df_res is not None and not df_res.empty:
                    results[sym] = df_res
            except Exception:
                pass # Bỏ qua hoàn toàn mã lỗi
    return results

# Tải dữ liệu một lượt
with st.spinner("Đang tối ưu dữ liệu hiển thị..."):
    valid_stock_data = load_all_data_concurrently(symbols)

# Lọc lại danh sách mã hiển thị (Chỉ lấy những mã thực sự có dữ liệu)
active_symbols = [s for s in symbols if s in valid_stock_data]

# 3. Triển khai lưới tự động (Chỉ vẽ những mã hợp lệ)
for i in range(0, len(active_symbols), 3):
    cols = st.columns(3)
    for j in range(3):
        if i + j < len(active_symbols):
            symbol = active_symbols[i + j]
            display_name = STOCKS[symbol][0]
            df = valid_stock_data[symbol]
            
            with cols[j]:
                with st.container(border=True):
                    widget.create_stock_widget(df, display_name)