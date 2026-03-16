import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts
import pandas as pd
import indicators as ind_calc # Import file tính toán mới

@st.dialog("Chi tiết biểu đồ", width="large")
def zoom_chart(df, symbol, color, title_markdown):
    # Sử dụng chính xác tiêu đề được truyền từ widget vào
    st.markdown(title_markdown, unsafe_allow_html=True)
    
    # Thêm lựa chọn nhiều chỉ số kỹ thuật hơn
    indicators = st.multiselect(
        "Thêm chỉ số kỹ thuật",
        options=["MA20", "MA50", "EMA20", "EMA50", "Bollinger Bands", "RSI (14)", "Volume"],
        default=["Volume"],
        key=f"ind_{symbol}"
    )
    
    # --- TÍNH TOÁN CÁC CHỈ SỐ BẰNG FILE INDICATORS.PY ---
    df = ind_calc.calculate_indicators(df, indicators)
    
    # Sử dụng chức năng của Streamlit để tạo thanh chọn khoảng thời gian
    timeframe = st.radio(
        "Khoảng thời gian", 
        ["1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "Tất cả"], 
        horizontal=True, 
        label_visibility="collapsed",
        key=f"tf_{symbol}"
    )
    
    # Dùng Pandas cắt dữ liệu dựa trên lựa chọn
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
    
    # Xử lý dữ liệu đã lọc cho biểu đồ nến
    full_data_list = []
    for _, row in plot_df.iterrows():
        full_data_list.append({
            "time": int(row['time']), 
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close'])
        })
    
    # --- CẤU HÌNH THANG ĐO CHO BIỂU ĐỒ ---
    zoom_options = {
        "height": 450, 
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
        "rightPriceScale": {
            "scaleMargins": {
                "top": 0.1,
                "bottom": 0.08 if "Volume" in indicators else 0.1, # Nới rộng không gian cho nến chính
            }
        },
        "leftPriceScale": {
            "visible": True if "RSI (14)" in indicators else False, 
            "borderColor": "rgba(128, 128, 128, 0.2)",
        }
    }
    
    # Khởi tạo mảng series với biểu đồ nến làm gốc
    series_list = [{
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
    
    # --- THÊM CÁC SERIES CHỈ SỐ VÀO BIỂU ĐỒ ---
    if "Volume" in indicators:
        vol_data = []
        for _, row in plot_df.iterrows():
            v_color = "rgba(38, 166, 154, 0.4)" if row['close'] >= row['open'] else "rgba(239, 83, 80, 0.4)"
            vol_data.append({"time": int(row['time']), "value": float(row['volume']), "color": v_color})
        
        series_list.append({
            "type": 'Histogram',
            "data": vol_data,
            "options": {
                "priceFormat": {"type": 'volume'},
                "priceScaleId": "", 
                "scaleMargins": {"top": 0.95, "bottom": 0}, # Ép Volume cực nhỏ (chỉ chiếm 5% chiều cao)
                "baseLineVisible": False, # Tắt vạch số 0
            }
        })

    if "MA20" in indicators:
        ma20_data = [{"time": int(row['time']), "value": float(row['MA20'])} for _, row in plot_df.dropna(subset=['MA20']).iterrows()]
        series_list.append({"type": 'Line', "data": ma20_data, "options": {"color": "#ffeb3b", "lineWidth": 1.5, "title": "MA20"}})

    if "MA50" in indicators:
        ma50_data = [{"time": int(row['time']), "value": float(row['MA50'])} for _, row in plot_df.dropna(subset=['MA50']).iterrows()]
        series_list.append({"type": 'Line', "data": ma50_data, "options": {"color": "#e91e63", "lineWidth": 1.5, "title": "MA50"}})

    if "EMA20" in indicators:
        ema20_data = [{"time": int(row['time']), "value": float(row['EMA20'])} for _, row in plot_df.dropna(subset=['EMA20']).iterrows()]
        series_list.append({"type": 'Line', "data": ema20_data, "options": {"color": "#29b6f6", "lineWidth": 1.5, "title": "EMA20"}})

    if "EMA50" in indicators:
        ema50_data = [{"time": int(row['time']), "value": float(row['EMA50'])} for _, row in plot_df.dropna(subset=['EMA50']).iterrows()]
        series_list.append({"type": 'Line', "data": ema50_data, "options": {"color": "#ab47bc", "lineWidth": 1.5, "title": "EMA50"}})

    if "Bollinger Bands" in indicators:
        upper_data = [{"time": int(row['time']), "value": float(row['BB_UPPER'])} for _, row in plot_df.dropna(subset=['BB_UPPER']).iterrows()]
        lower_data = [{"time": int(row['time']), "value": float(row['BB_LOWER'])} for _, row in plot_df.dropna(subset=['BB_LOWER']).iterrows()]
        
        series_list.append({"type": 'Line', "data": upper_data, "options": {"color": "rgba(255, 255, 255, 0.3)", "lineWidth": 1, "lineStyle": 2, "title": "Upper"}})
        series_list.append({"type": 'Line', "data": lower_data, "options": {"color": "rgba(255, 255, 255, 0.3)", "lineWidth": 1, "lineStyle": 2, "title": "Lower"}})

    if "RSI (14)" in indicators:
        rsi_data = [{"time": int(row['time']), "value": float(row['RSI'])} for _, row in plot_df.dropna(subset=['RSI']).iterrows()]
        series_list.append({
            "type": 'Line', 
            "data": rsi_data, 
            "options": {
                "color": "#ff9800", 
                "lineWidth": 1.5, 
                "title": "RSI(14)",
                "priceScaleId": "left" 
            }
        })
    
    renderLightweightCharts(
        charts=[{"chart": zoom_options, "series": series_list}],
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
