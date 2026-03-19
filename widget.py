import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts
import pandas as pd
import indicators as ind_calc # Import file tính toán mới

@st.dialog("Chi tiết biểu đồ", width="large")
def zoom_chart(df, symbol, color, title_markdown):
    # Sử dụng chính xác tiêu đề được truyền từ widget vào
    st.markdown(title_markdown, unsafe_allow_html=True)
    
    # --- PHÂN LOẠI & TÌM KIẾM CHỈ SỐ KỸ THUẬT ---
    with st.expander("🛠️ Chọn & Tìm kiếm Chỉ số kỹ thuật", expanded=False):
        col_t, col_m, col_v, col_vl = st.columns(4)
        with col_t:
            trend = st.multiselect("📈 Xu hướng", ["MA20", "MA50", "EMA20", "EMA50", "MACD", "ADX", "CCI"], key=f"ind_trend_{symbol}")
        with col_m:
            mom = st.multiselect("⚡ Động lượng", ["RSI (14)", "Stochastic"], key=f"ind_mom_{symbol}")
        with col_v:
            volat = st.multiselect("🌊 Biến động", ["Bollinger Bands", "ATR"], key=f"ind_volat_{symbol}")
        with col_vl:
            volum = st.multiselect("📊 Khối lượng", ["Volume", "OBV", "VWAP"], default=["Volume"], key=f"ind_volum_{symbol}")
            
        # Gộp tất cả lựa chọn từ các nhóm lại thành 1 list duy nhất
        indicators = trend + mom + volat + volum
        
        # Kiểm tra xem có biểu đồ phụ nào được chọn không
        subchart_indicators = ["RSI (14)", "Stochastic", "MACD", "ADX", "CCI", "ATR", "OBV"]
        has_subchart = any(ind in indicators for ind in subchart_indicators)
        
        # Khởi tạo kích thước mặc định
        main_height = 450
        sub_height = 150
        
        # Chỉ hiện thanh tùy chỉnh kích thước nếu có biểu đồ kỹ thuật (biểu đồ phụ)
        if has_subchart:
            st.divider()
            st.markdown("**📏 Tùy chỉnh kích thước biểu đồ**")
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                main_height = st.slider("Chiều cao biểu đồ chính (px)", min_value=300, max_value=800, value=450, step=50, key=f"h_main_{symbol}")
            with col_h2:
                sub_height = st.slider("Chiều cao biểu đồ phụ (px)", min_value=100, max_value=400, value=150, step=25, key=f"h_sub_{symbol}")
    
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
    
    # Danh sách chứa toàn bộ các khối biểu đồ (Biểu đồ chính + Biểu đồ phụ)
    charts_to_render = []

    # --- 1. CẤU HÌNH BIỂU ĐỒ CHÍNH (OVERLAY CHARTS) ---
    main_chart_options = {
        "height": main_height, # Sử dụng biến tùy chỉnh
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
            "minimumWidth": 80, # Ép độ rộng chuẩn để căn lề
            "scaleMargins": {
                "top": 0.1,
                "bottom": 0.15, 
            }
        },
        "crosshair": {
            "mode": 0 # Mode 0: Mượt mà không bắt nến, giúp đồng bộ dễ hơn
        }
    }
    
    main_series_list = [{
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
    
    # Thêm các chỉ số nằm trực tiếp trên biểu đồ nến
    if "Volume" in indicators:
        vol_data = []
        for _, row in plot_df.iterrows():
            v_color = "rgba(38, 166, 154, 0.4)" if row['close'] >= row['open'] else "rgba(239, 83, 80, 0.4)"
            vol_data.append({"time": int(row['time']), "value": float(row['volume']), "color": v_color})
        main_series_list.append({
            "type": 'Histogram',
            "data": vol_data,
            "options": {"priceFormat": {"type": 'volume'}, "priceScaleId": "", "baseLineVisible": False},
            "priceScale": {"scaleMargins": {"top": 0.9, "bottom": 0}}
        })

    if "MA20" in indicators:
        ma20_data = [{"time": int(row['time']), "value": float(row['MA20'])} for _, row in plot_df.dropna(subset=['MA20']).iterrows()]
        main_series_list.append({"type": 'Line', "data": ma20_data, "options": {"color": "#FFC107", "lineWidth": 1.5, "title": "MA20"}})

    if "MA50" in indicators:
        ma50_data = [{"time": int(row['time']), "value": float(row['MA50'])} for _, row in plot_df.dropna(subset=['MA50']).iterrows()]
        main_series_list.append({"type": 'Line', "data": ma50_data, "options": {"color": "#FF9800", "lineWidth": 1.5, "title": "MA50"}})

    if "EMA20" in indicators:
        ema20_data = [{"time": int(row['time']), "value": float(row['EMA20'])} for _, row in plot_df.dropna(subset=['EMA20']).iterrows()]
        main_series_list.append({"type": 'Line', "data": ema20_data, "options": {"color": "#03A9F4", "lineWidth": 1.5, "title": "EMA20"}})

    if "EMA50" in indicators:
        ema50_data = [{"time": int(row['time']), "value": float(row['EMA50'])} for _, row in plot_df.dropna(subset=['EMA50']).iterrows()]
        main_series_list.append({"type": 'Line', "data": ema50_data, "options": {"color": "#9C27B0", "lineWidth": 1.5, "title": "EMA50"}})

    if "VWAP" in indicators:
        vwap_data = [{"time": int(row['time']), "value": float(row['VWAP'])} for _, row in plot_df.dropna(subset=['VWAP']).iterrows()]
        main_series_list.append({"type": 'Line', "data": vwap_data, "options": {"color": "#E91E63", "lineWidth": 1.5, "lineStyle": 2, "title": "VWAP"}})

    if "Bollinger Bands" in indicators:
        upper_data = [{"time": int(row['time']), "value": float(row['BB_UPPER'])} for _, row in plot_df.dropna(subset=['BB_UPPER']).iterrows()]
        lower_data = [{"time": int(row['time']), "value": float(row['BB_LOWER'])} for _, row in plot_df.dropna(subset=['BB_LOWER']).iterrows()]
        
        # Tăng độ đậm của màu và độ dày nét vẽ để làm nổi bật không gian vùng giá ở giữa
        main_series_list.append({"type": 'Line', "data": upper_data, "options": {"color": "rgba(3, 169, 244, 0.9)", "lineWidth": 2, "title": "Upper"}})
        main_series_list.append({"type": 'Line', "data": lower_data, "options": {"color": "rgba(3, 169, 244, 0.9)", "lineWidth": 2, "title": "Lower"}})

    # Đưa biểu đồ chính vào danh sách render
    charts_to_render.append({"chart": main_chart_options, "series": main_series_list})

    # --- 2. CẤU HÌNH BIỂU ĐỒ PHỤ (SUBCHARTS DƯỚI ĐÁY) ---
    def get_subchart_options():
        return {
            "height": sub_height, # Sử dụng biến tùy chỉnh
            "layout": {"background": {"type": "solid", "color": "transparent"}, "textColor": "#808080"},
            "grid": {"vertLines": {"visible": False}, "horzLines": {"color": "rgba(128, 128, 128, 0.2)"}},
            "timeScale": {"borderVisible": False},
            "rightPriceScale": {
                "minimumWidth": 80 # Đảm bảo độ rộng trục Y bằng nhau với biểu đồ chính
            },
            "crosshair": {
                "mode": 0
            }
        }

    if "RSI (14)" in indicators:
        rsi_data = [{"time": int(row['time']), "value": float(row['RSI'])} for _, row in plot_df.dropna(subset=['RSI']).iterrows()]
        sub_series = [{"type": 'Line', "data": rsi_data, "options": {"color": "#ff9800", "lineWidth": 1.5, "title": "RSI(14)"}}]
        charts_to_render.append({"chart": get_subchart_options(), "series": sub_series})

    if "MACD" in indicators:
        macd_data = [{"time": int(row['time']), "value": float(row['MACD'])} for _, row in plot_df.dropna(subset=['MACD']).iterrows()]
        macd_signal_data = [{"time": int(row['time']), "value": float(row['MACD_SIGNAL'])} for _, row in plot_df.dropna(subset=['MACD_SIGNAL']).iterrows()]
        macd_hist_data = []
        for _, row in plot_df.dropna(subset=['MACD_HIST']).iterrows():
            h_color = "rgba(38, 166, 154, 0.6)" if row['MACD_HIST'] >= 0 else "rgba(239, 83, 80, 0.6)"
            macd_hist_data.append({"time": int(row['time']), "value": float(row['MACD_HIST']), "color": h_color})
            
        sub_series = [
            {"type": 'Line', "data": macd_data, "options": {"color": "#2196f3", "lineWidth": 1.5, "title": "MACD"}},
            {"type": 'Line', "data": macd_signal_data, "options": {"color": "#ff9800", "lineWidth": 1.5, "title": "Signal"}},
            {"type": 'Histogram', "data": macd_hist_data, "options": {"title": "Hist"}}
        ]
        charts_to_render.append({"chart": get_subchart_options(), "series": sub_series})

    if "Stochastic" in indicators:
        stoch_k_data = [{"time": int(row['time']), "value": float(row['STOCH_K'])} for _, row in plot_df.dropna(subset=['STOCH_K']).iterrows()]
        stoch_d_data = [{"time": int(row['time']), "value": float(row['STOCH_D'])} for _, row in plot_df.dropna(subset=['STOCH_D']).iterrows()]
        sub_series = [
            {"type": 'Line', "data": stoch_k_data, "options": {"color": "#4caf50", "lineWidth": 1.5, "title": "Stoch %K"}},
            {"type": 'Line', "data": stoch_d_data, "options": {"color": "#f44336", "lineWidth": 1, "lineStyle": 2, "title": "Stoch %D"}}
        ]
        charts_to_render.append({"chart": get_subchart_options(), "series": sub_series})

    if "ADX" in indicators:
        adx_data = [{"time": int(row['time']), "value": float(row['ADX'])} for _, row in plot_df.dropna(subset=['ADX']).iterrows()]
        adx_pos_data = [{"time": int(row['time']), "value": float(row['ADX_POS'])} for _, row in plot_df.dropna(subset=['ADX_POS']).iterrows()]
        adx_neg_data = [{"time": int(row['time']), "value": float(row['ADX_NEG'])} for _, row in plot_df.dropna(subset=['ADX_NEG']).iterrows()]
        sub_series = [
            {"type": 'Line', "data": adx_data, "options": {"color": "#ffeb3b", "lineWidth": 2, "title": "ADX"}},
            {"type": 'Line', "data": adx_pos_data, "options": {"color": "#26a69a", "lineWidth": 1, "title": "+DI"}},
            {"type": 'Line', "data": adx_neg_data, "options": {"color": "#ef5350", "lineWidth": 1, "title": "-DI"}}
        ]
        charts_to_render.append({"chart": get_subchart_options(), "series": sub_series})

    if "CCI" in indicators:
        cci_data = [{"time": int(row['time']), "value": float(row['CCI'])} for _, row in plot_df.dropna(subset=['CCI']).iterrows()]
        sub_series = [{"type": 'Line', "data": cci_data, "options": {"color": "#9c27b0", "lineWidth": 1.5, "title": "CCI"}}]
        charts_to_render.append({"chart": get_subchart_options(), "series": sub_series})

    if "ATR" in indicators:
        atr_data = [{"time": int(row['time']), "value": float(row['ATR'])} for _, row in plot_df.dropna(subset=['ATR']).iterrows()]
        sub_series = [{"type": 'Line', "data": atr_data, "options": {"color": "#795548", "lineWidth": 1.5, "title": "ATR"}}]
        charts_to_render.append({"chart": get_subchart_options(), "series": sub_series})
        
    if "OBV" in indicators:
        obv_data = [{"time": int(row['time']), "value": float(row['OBV'])} for _, row in plot_df.dropna(subset=['OBV']).iterrows()]
        sub_series = [{"type": 'Line', "data": obv_data, "options": {"color": "#8d6e63", "lineWidth": 1.5, "title": "OBV"}}]
        charts_to_render.append({"chart": get_subchart_options(), "series": sub_series})
    
    # Render tất cả biểu đồ (tự động đồng bộ crosshair). Key thay đổi linh hoạt theo danh sách indicators để tránh lỗi crash React DOM.
    dynamic_key = f"zoom_{symbol}_{'_'.join(indicators)}"
    renderLightweightCharts(charts=charts_to_render, key=dynamic_key)

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
