import streamlit as st
import os
import news_analysis
import json
import re
import time
from datetime import date, datetime, timedelta
import json_processor
import news_widget

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

# 1. Cấu hình trang & CSS 
st.set_page_config(layout="wide", page_title="Tin Tức")
st.markdown("""
<style>
    header, [data-testid='stHeader'], .stAppHeader, .stSidebar {display: none !important;} 
    .main .block-container {padding-top: 0rem !important; margin-top: -3rem !important;} 
    div[data-testid='stVerticalBlockBorderWrapper'] {border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2) !important; background-color: rgba(255, 255, 255, 0.02); padding: 15px; height: 260px;} 
    
    /* Định dạng chung cho nút chuyển trang và nút Cài đặt */
    a[data-testid='stPageLink-NavLink'],
    button[data-testid="baseButton-secondary"] {
        border: 1px solid rgba(33, 150, 243, 0.6) !important; 
        background-color: rgba(33, 150, 243, 0.1) !important; 
        border-radius: 8px !important; 
        font-weight: bold !important; 
        height: 40px !important; 
        display: flex !important; 
        align-items: center !important; 
        justify-content: center !important;
        text-decoration: none !important;
        color: inherit !important;
        transition: all 0.2s ease-in-out !important;
        padding: 0 !important;
        width: 100% !important;
    }
    
    a[data-testid='stPageLink-NavLink']:hover, 
    button[data-testid="baseButton-secondary"]:hover {
        border: 1px solid rgba(33, 150, 243, 1) !important;
        background-color: rgba(33, 150, 243, 0.25) !important;
    }

    button[data-testid="baseButton-secondary"] p,
    a[data-testid="stPageLink-NavLink"] p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 40px !important; 
        display: block !important;
    }

    /* Ẩn các nút bên trong widget tin tức không bị dính CSS trên */
    div[data-testid="stVerticalBlockBorderWrapper"] button[data-testid="baseButton-secondary"] {
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        height: auto !important;
    }

    /* Đẩy toàn bộ cụm nút radio dịch xuống để cân bằng với tiêu đề */
    div[data-testid="stRadio"] {
        margin-top: 12px !important;
    }

    /* CSS Chuyên mục: HIỆU ỨNG ĐỔI MÀU XANH KHI CHỌN */
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        justify-content: flex-start !important;
        gap: 10px !important;
        align-items: center !important;
    }
    
    /* Xóa hoàn toàn nhãn trống và vùng chứa nhãn */
    div[data-testid="stRadio"] label[data-testid="stWidgetLabel"] {
        display: none !important;
    }

    /* Định dạng chung cho nút (Chưa chọn) */
    div[data-testid="stRadio"] label {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 6px 20px !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
        cursor: pointer !important;
        margin: 0 !important;
        display: flex !important;
        justify-content: center !important;
    }
    
    div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
        display: none !important; /* Ẩn dấu chấm tròn */
    }

    /* HIỆU ỨNG DI CHUỘT (HOVER) */
    div[data-testid="stRadio"] label:hover {
        border: 1px solid rgba(33, 150, 243, 1) !important;
        background-color: rgba(33, 150, 243, 0.25) !important;
    }

    /* TRẠNG THÁI KHI ĐƯỢC CHỌN (TRUE) */
    div[data-testid="stRadio"] label:has(div[aria-checked="true"]) {
        background-color: rgba(33, 150, 243, 0.1) !important; 
        border: 1px solid rgba(33, 150, 243, 0.6) !important;
    }
    
    div[data-testid="stRadio"] label:has(div[aria-checked="true"]) p {
        color: #2196f3 !important;
        font-weight: bold !important;
    }

    /* ĐƯA NHÃN SANG BÊN TRÁI Ô CHỌN NGÀY VÀ CĂN GIỮA */
    div[data-testid="stDateInput"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 10px !important;
        margin-top: 25px !important;
    }
    div[data-testid="stDateInput"] label {
        margin-bottom: 0 !important;
        white-space: nowrap !important;
        min-width: fit-content !important;
    }

    /* DỊCH DÒNG CHỮ ĐANG HIỆN TIN NGÀY XUỐNG ĐỂ CÂN BẰNG */
    div[data-testid="stCaptionContainer"] {
        margin-top: 25px !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. Tiêu đề và Nút Điều Hướng
st.markdown("<h1 style='text-align: center;'>Tin Tức</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1.5, 1.5, 1.5, 1], vertical_alignment="center")

with nav_col2: 
    st.page_link("dashboard.py", label="Trang Chủ", use_container_width=True)

with nav_col3:
    if os.path.exists("pages/2_backtest.py"):
        st.page_link("pages/2_backtest.py", label="Backtest", use_container_width=True)
    else:
        st.button("Backtest", disabled=True, use_container_width=True)

with nav_col4:
    if st.button("Cài đặt", use_container_width=True):
        settings_dialog()

st.markdown("<br>", unsafe_allow_html=True)

# 3. Logic ngày tháng
effective_date = date.today()
now = datetime.now()
if now.hour < 9:
    default_date = date.today() - timedelta(days=1)
else:
    default_date = date.today()

# 4. Hàng ngang: Tiêu đề Tổng quan + Chọn ngày + Thông báo
over_col1, over_col2, over_col3 = st.columns([0.36, 0.18, 0.53], vertical_alignment="center")
with over_col1:
    st.markdown("<h3 style='margin:0;'>Đánh Giá Thị Trường Tổng Quan</h3>", unsafe_allow_html=True)
with over_col2:
    selected_date = st.date_input("Chọn ngày:", default_date, max_value=date.today())

effective_date = selected_date
session = "13h" # Mặc định bản chiều cho những ngày cũ

if selected_date == date.today():
    if now.hour < 9:
        effective_date = selected_date - timedelta(days=1)
        session = "13h"
    elif now.hour < 13:
        session = "09h"
    else:
        session = "13h"

with over_col3:
    st.caption(f"Đang hiển thị tin ngày {effective_date.strftime('%d/%m/%Y')} (Cập nhật lúc {session})")

st.markdown("<hr>", unsafe_allow_html=True)

# 5. Phân tích AI
file_path = news_analysis.get_file_path(effective_date, session)
if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
    full_json_str = ""
    with st.status(f"Đang phân tích tin tức lúc {session}...", expanded=True) as status:
        for chunk in news_analysis.analyze_news(effective_date, session):
            if chunk: full_json_str += chunk
        status.update(label="Hoàn tất!", state="complete", expanded=False)
    if full_json_str: st.rerun()

# --- XỬ LÝ DỮ LIỆU JSON ---
market_summary, world_news, business_news = json_processor.parse_news_json(file_path)

# HIỂN THỊ ĐÁNH GIÁ THỊ TRƯỜNG
if market_summary:
    def render_summary_box(title, text):
        if not text: return
        parts = text.split(" | ")
        if len(parts) >= 3:
            main_text = parts[0].strip()
            scores = " | ".join(parts[1:]).strip()
            color = "gray"
            if "Điểm tác động: -" in scores: color = "red"
            elif "Điểm tác động: +" in scores: color = "green"
            
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.markdown(f":{color}[**{scores}**]")
                st.markdown(main_text)
        else:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.markdown(text)

    def render_scenario_box(title, text, default_color):
        if not text: return
        parts = text.split(" | ")
        if len(parts) >= 3:
            prob = parts[0].strip()
            explain = parts[1].replace("Giải thích:", "").strip()
            conf = parts[2].strip()
            scores = f"{prob} | {conf}"
            
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.markdown(f":{default_color}[**{scores}**]")
                st.markdown(explain)
        else:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.markdown(text)

    sum_col1, sum_col2, sum_col3 = st.columns(3)
    with sum_col1: render_summary_box("VN-Index", market_summary.get('overall_impact'))
    with sum_col2: render_summary_box("Nhóm ngành", market_summary.get('sector_impact'))
    with sum_col3: render_summary_box("Tiềm năng", market_summary.get('potential_sectors'))
    
    scenarios = market_summary.get('next_scenarios')
    if scenarios:
        st.markdown("<br><h4 style='margin: 0;'>🔮 Kịch Bản Tiếp Theo</h4><br>", unsafe_allow_html=True)
        sc_col1, sc_col2, sc_col3 = st.columns(3)
        with sc_col1: render_scenario_box("Tích cực", scenarios.get('positive'), "green")
        with sc_col2: render_scenario_box("Tiêu cực", scenarios.get('negative'), "red")
        with sc_col3: render_scenario_box("Khả năng cao", scenarios.get('most_likely'), "gray")
            
    st.markdown("<br><hr>", unsafe_allow_html=True)

# HIỂN THỊ TIN NÓNG + CHUYÊN MỤC
if world_news or business_news:
    header_col1, header_col2 = st.columns([1, 6], vertical_alignment="center")
    with header_col1:
        st.markdown("<h3 style='margin: 0;'>Tin Nóng</h3>", unsafe_allow_html=True)
    with header_col2:
        # Nhãn để trống "" và dùng options mảng đúng vị trí
        category = st.radio("", ["Thế giới", "Kinh doanh"], horizontal=True, label_visibility="collapsed")
        
    news_items = world_news if category == "Thế giới" else business_news
    st.markdown("<br>", unsafe_allow_html=True)

    for i in range(0, len(news_items), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(news_items):
                item = news_items[i + j]
                
                sentiment_str = item.get("general_sentiment", "")
                if isinstance(sentiment_str, str):
                    if "**Tiêu Cực**" in sentiment_str:
                        sentiment_str = f":red[{sentiment_str}]"
                    elif "**Tích Cực**" in sentiment_str:
                        sentiment_str = f":green[{sentiment_str}]"
                    elif "**Trung Lập**" in sentiment_str:
                        sentiment_str = f":gray[{sentiment_str}]"

                with cols[j]:
                    with st.container(border=True):
                        news_widget.create_news_widget(i+j, item.get("title"), item.get("explanation"), sentiment_str, item.get("vn_market_impact"), item.get("sector_impact"), item.get("ticker_impact"), item.get("sources", []))