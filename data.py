import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import streamlit as st
from datetime import datetime, timedelta

# --- API SUPABASE ĐÃ DÁN TRỰC TIẾP ---
SUPABASE_URL = "https://csgmhgvrycnckzbixdzs.supabase.co"
SUPABASE_KEY = "sb_secret_Y7-wh6RMl-UsWx7COUzbIw_taVMFfny"

# Khởi tạo client trực tiếp từ chuỗi ký tự trên
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_stock_data(symbol: str):
    table_name = "stock_prices"
    
    # 1. THỬ LẤY DỮ LIỆU HIỆN CÓ TRONG SUPABASE
    try:
        # Lấy dữ liệu sắp xếp theo thời gian tăng dần
        response = supabase.table(table_name).select("*").eq("symbol", symbol).order("time", desc=False).execute()
        df_db = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Lỗi kết nối Supabase: {e}")
        df_db = pd.DataFrame()

    # 2. KIỂM TRA XEM CÓ CẦN TẢI THÊM DỮ LIỆU TỪ YAHOO KHÔNG
    df_new = pd.DataFrame()
    
    if df_db.empty:
        # Nếu Database chưa có gì, tải 1 năm từ Yahoo
        with st.spinner(f"Đang khởi tạo dữ liệu cho {symbol}..."):
            df_new = yf.Ticker(symbol).history(period="1y", interval="1d")
    else:
        # Nếu đã có dữ liệu, kiểm tra ngày cuối cùng
        last_ts = df_db['time'].max()
        last_date = datetime.fromtimestamp(last_ts)
        
        # Nếu dữ liệu cũ hơn 1 ngày thì tải bù ngày mới
        if (datetime.now() - last_date) > timedelta(days=1):
            start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            df_new = yf.Ticker(symbol).history(start=start_date, interval="1d")

    # 3. NẾU CÓ DỮ LIỆU MỚI, LƯU VÀO SUPABASE VÀ CẬP NHẬT BIẾN HIỂN THỊ
    if not df_new.empty:
        df_new = df_new.reset_index().rename(columns={
            'Date': 'time', 'Datetime': 'time', 'Open': 'open',
            'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
        })
        # Chuyển thời gian sang Unix Timestamp (số nguyên)
        df_new['time'] = pd.to_datetime(df_new['time'], utc=True).apply(lambda x: int(x.timestamp()))
        df_new['symbol'] = symbol
        
        # Chỉ lấy các cột cần thiết để lưu vào bảng stock_prices
        df_save = df_new[['symbol', 'time', 'open', 'high', 'low', 'close', 'volume']]
        
        try:
            # Đẩy dữ liệu lên Supabase
            supabase.table(table_name).upsert(df_save.to_dict('records')).execute()
            # Gộp dữ liệu mới vào dữ liệu cũ để trả về hiển thị luôn
            df_db = pd.concat([df_db, df_save], ignore_index=True).drop_duplicates(subset=['time'])
        except Exception as e:
            st.warning(f"Không thể lưu dữ liệu mới của {symbol} vào DB: {e}")
            # Nếu lỗi DB thì vẫn trả về dữ liệu vừa tải để biểu đồ hiện được
            if df_db.empty: return df_new

    # 4. TRẢ VỀ DỮ LIỆU CUỐI CÙNG (Đã sắp xếp)
    if df_db.empty:
        return pd.DataFrame()
        
    return df_db.sort_values('time')
