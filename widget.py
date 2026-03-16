import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts

@st.dialog("Chi tiết biểu đồ", width="large")
def zoom_chart(df, symbol, color, title_markdown):
    # Sử dụng chính xác tiêu đề được truyền từ widget vào
    st.markdown(title_markdown, unsafe_allow_html=True)
    
    # Sử dụng chức năng của Streamlit để tạo thanh chọn khoảng thời gian (cắt dữ liệu tĩnh, không gọi API)
    timeframe = st.radio(
        "Khoảng thời gian", 
        ["1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "Tất cả"], 
        horizontal=True, 
        label_visibility="collapsed",
        key=f"tf_{symbol}"
    )
    
    # Dùng Pandas cắt dữ liệu dựa trên lựa chọn (Mặc định 1 tháng ~ 22 ngày giao dịch)
    if timeframe == "1 Tháng":
        plot_df = df.tail(22)
    elif timeframe == "3 Tháng":
        plot_df = df.tail(66)
    elif timeframe == "6 Tháng":
        plot_df = df.tail(130)
    elif timeframe == "1 Năm":
        plot_df = df.tail(252)
    else:
        plot_df = df
    
    # Xử lý dữ liệu đã lọc cho biểu đồ nến (Ép kiểu int cho thời gian)
    full_data_list = []
    for _, row in plot_df.iterrows():
        full_data_list.append({
            "time": int(row['time']), 
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close'])
        })
    
    zoom_options = {
        "height": 410, 
        "layout": {
            "background": {"type": "solid", "color": "transparent"}, 
            "textColor": "#808080"
        },
        "grid": {
            "vertLines": {"visible": False}, 
            "horzLines": {"color": "rgba(128, 128, 128, 0.2)"}
        },
        "timeScale": {
            "borderVisible": False,
        },
    }
    
    series_candle = [{
        "type": 'Candlestick', 
        "data": full_data_list, 
        "options": {
            "upColor": "#26a69a", 
            "downColor": "#ef5350", 
            "borderVisible": False, 
            "wickUpColor": "#26a69a", 
            "wickDownColor": "#ef5350"
        }
    }]
    
    renderLightweightCharts(
        charts=[{"chart": zoom_options, "series": series_candle}],
        key=f"zoom_{symbol}"
    )

def create_stock_widget(df, symbol):
    # --- XỬ LÝ DỮ LIỆU CHO WIDGET NHỎ (Giữ nguyên 22 ngày) ---
    chart_data = df.tail(22).copy()
    chart_data = chart_data.reset_index()
    
    last_close = chart_data['close'].iloc[-1]
    first_close = chart_data['close'].iloc[0]
    change = last_close - first_close
    pct_change = (change / first_close) * 100
    
    color = "#26a69a" if change >= 0 else "#ef5350"
    symbol_display = "+" if change >= 0 else ""

    # Lưu định dạng tiêu đề vào một biến để dùng chung cho cả 2 biểu đồ
    title_markdown = f"**{symbol} | <span style='color:{color}'>{symbol_display}{change:.2f}</span> | <span style='color:{color}'>{symbol_display}{pct_change:.2f}%</span>**"

    data_list = []
    for _, row in chart_data.iterrows():
        data_list.append({
            "time": int(row['time']), 
            "value": float(row['close'])
        })

    # --- GIAO DIỆN HEADER ---
    col_info, col_btn = st.columns([0.85, 0.15], vertical_alignment="center")
    
    with col_info:
        # In tiêu đề cho widget nhỏ
        st.markdown(title_markdown, unsafe_allow_html=True)
    
    with col_btn:
        # Truyền thêm biến title_markdown vào hàm zoom_chart
        if st.button("⛶", key=f"btn_{symbol}"):
            zoom_chart(df, symbol, color, title_markdown)

    # --- CẤU HÌNH BIỂU ĐỒ NHỎ ---
    chart_options = {
        "height": 180,
        "handleScroll": False,
        "handleScale": False,
        "layout": {
            "background": {"type": "solid", "color": "transparent"},
            "textColor": "#808080",
            "fontSize": 11,
        },
        "grid": {
            "vertLines": {"visible": False},
            "horzLines": {"color": "rgba(128, 128, 128, 0.2)"},
        },
        "rightPriceScale": {
            "borderVisible": False,
            "scaleMargins": {"top": 0.2, "bottom": 0.2},
        },
        "timeScale": {
            "borderVisible": False,
            "fixLeftEdge": True,
            "fixRightEdge": True,
        },
        "crosshair": {
            "mode": 0,
            "vertLine": {"color": color, "width": 1, "style": 3},
            "horzLine": {"color": color, "width": 1, "style": 3},
        }
    }

    series_line = [{
        "type": 'Line',
        "data": data_list,
        "options": {
            "color": color,
            "lineWidth": 2,
            "crosshairMarkerVisible": True,
            "crosshairMarkerRadius": 4,
            "priceFormat": {"type": 'price', "precision": 2, "minMove": 0.01},
        }
    }]

    renderLightweightCharts(
        charts=[{
            "chart": chart_options,
            "series": series_line
        }],
        key=f"chart_{symbol}"
    )