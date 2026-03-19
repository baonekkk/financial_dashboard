import streamlit as st

@st.dialog("Chi tiết tin tức", width="large")
def zoom_news(title, explanation, sentiment, vn_market_impact, sector_impact, ticker_impact, sources=[]):
    color = "#26a69a" if "Tốt" in sentiment else "#ef5350" if "Xấu" in sentiment else "#808080"
    st.markdown(f"### {title}")
    st.markdown(f"**Đánh giá:** <span style='color:{color}; font-weight:bold;'>{sentiment}</span>", unsafe_allow_html=True)
    st.divider()
    st.write(explanation)
    st.markdown("#### Phân tích Tác động chuyên sâu")
    st.info(f"Thị trường chứng khoán VN:\n\n{vn_market_impact}")
    st.warning(f"Nhóm ngành ảnh hưởng:\n\n{sector_impact}")
    st.success(f"Mã cổ phiếu tác động:\n\n{ticker_impact}")
    
    if sources:
        st.divider()
        st.markdown("#### Nguồn tin trích dẫn")
        src_cols = st.columns(2)
        for idx, src in enumerate(sources):
            display_src = src if src.startswith("[") else f"[{src}"
            with src_cols[idx % 2]:
                st.caption(display_src)

def create_news_widget(widget_id, title, explanation, sentiment, vn_market_impact, sector_impact, ticker_impact, sources=[]):
    limit = 110
    display_text = explanation[:limit] + "..." if len(explanation) > limit else explanation
    col_info, col_btn = st.columns([0.85, 0.15], vertical_alignment="top")
    color = "#26a69a" if "Tốt" in sentiment else "#ef5350" if "Xấu" in sentiment else "#808080"
    with col_info:
        st.markdown(f"**{title}** &nbsp;<code style='color: {color}; font-size: 0.7rem;'>{sentiment}</code>", unsafe_allow_html=True)
    with col_btn:
        if st.button("⛶", key=f"btn_zoom_{widget_id}"):
            zoom_news(title, explanation, sentiment, vn_market_impact, sector_impact, ticker_impact, sources)
    st.markdown(f"<div style='height: 85px; overflow: hidden; font-size: 0.85rem; color: #d0d0d0; margin-top: 5px;'>{display_text}</div>", unsafe_allow_html=True)
    if len(explanation) > limit:
        if st.button("Xem thêm", key=f"btn_more_{widget_id}"):
            zoom_news(title, explanation, sentiment, vn_market_impact, sector_impact, ticker_impact, sources)
