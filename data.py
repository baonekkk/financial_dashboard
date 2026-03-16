import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import streamlit as st
from datetime import datetime, timedelta

# Kết nối bảo mật từ Secrets
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Lỗi: Chưa cấu hình Supabase Secrets!")

def get_stock_data(symbol: str):
    table_name = "stock_prices"
    
    # 1. KIỂM TRA DỮ LIỆU CUỐI CÙNG TRONG SUPABASE
    try:
        response = supabase.table(table_name).select("time").eq("symbol", symbol).order("time", desc=True).limit(1).execute()
        data_db = response.data
    except Exception as e:
        st.error(f"Lỗi truy vấn DB: {e}")
        data_db = []

    # 2. XÁC ĐỊNH KHOẢNG THỜI GIAN CẦN TẢI
    if not data_db:
        # Nếu chưa có gì: Tải toàn bộ
        df = yf.Ticker(symbol).history(period="max", interval="1d")
    else:
        # Nếu có rồi: Tải từ ngày cuối + 1 ngày
        last_ts = data_db[0]['time']
        last_date = datetime.fromtimestamp(last_ts)
        
        # Nếu dữ liệu mới nhất trong DB chưa quá 12h, lấy luôn từ DB ra dùng
        if (datetime.now() - last_date) < timedelta(hours=12):
            full_data = supabase.table(table_name).select("*").eq("symbol", symbol).order("time", desc=False).execute()
            return pd.DataFrame(full_data.data)

        start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
        df = yf.Ticker(symbol).history(start=start_date, interval="1d")

    # 3. XỬ LÝ VÀ LƯU DỮ LIỆU MỚI (NẾU CÓ)
    if not df.empty:
        df = df.reset_index()
        # Chuẩn hóa tên cột
        df = df.rename(columns={
            'Date': 'time', 'Datetime': 'time', 'Open': 'open',
            'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
        })
        # Chuyển thời gian sang số nguyên
        df['time'] = pd.to_datetime(df['time'], utc=True).apply(lambda x: int(x.timestamp()))
        df['symbol'] = symbol
        
        # Chỉ giữ lại các cột khớp với bảng Database
        df_save = df[['symbol', 'time', 'open', 'high', 'low', 'close', 'volume']]
        
        # Đưa lên Supabase (Upsert giúp cập nhật nếu trùng ngày)
        records = df_save.to_dict('records')
        try:
            supabase.table(table_name).upsert(records).execute()
        except Exception:
            pass # Bỏ qua nếu có lỗi ghi đè nhỏ

    # 4. TRẢ VỀ KẾT QUẢ CUỐI CÙNG TỪ DATABASE
    res = supabase.table(table_name).select("*").eq("symbol", symbol).order("time", desc=False).execute()
    return pd.DataFrame(res.data)
