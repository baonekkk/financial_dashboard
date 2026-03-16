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
except Exception as e:
    st.error(f"Chưa cấu hình Secrets: {e}")

def get_stock_data(symbol: str):
    table_name = "stock_prices"
    df_final = pd.DataFrame()

    try:
        # 1. THỬ LẤY DỮ LIỆU CUỐI CÙNG TRONG SUPABASE
        response = supabase.table(table_name).select("time").eq("symbol", symbol).order("time", desc=True).limit(1).execute()
        data_db = response.data

        if not data_db:
            # Nếu DB trống -> Tải mới hoàn toàn
            df_new = yf.Ticker(symbol).history(period="max", interval="1d")
        else:
            last_ts = data_db[0]['time']
            last_date = datetime.fromtimestamp(last_ts)
            
            # Nếu dữ liệu cũ hơn 12h mới tải thêm
            if (datetime.now() - last_date) > timedelta(hours=12):
                start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                df_new = yf.Ticker(symbol).history(start=start_date, interval="1d")
            else:
                df_new = pd.DataFrame()

        # 2. XỬ LÝ DỮ LIỆU MỚI TẢI VỀ
        if not df_new.empty:
            df_new = df_new.reset_index()
            df_new = df_new.rename(columns={
                'Date': 'time', 'Datetime': 'time', 'Open': 'open',
                'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
            })
            df_new['time'] = pd.to_datetime(df_new['time'], utc=True).apply(lambda x: int(x.timestamp()))
            df_new['symbol'] = symbol
            
            # Lưu vào DB
            df_save = df_new[['symbol', 'time', 'open', 'high', 'low', 'close', 'volume']]
            records = df_save.to_dict('records')
            supabase.table(table_name).upsert(records).execute()

        # 3. LUÔN TRẢ VỀ DỮ LIỆU TỪ DB ĐỂ HIỂN THỊ
        res = supabase.table(table_name).select("*").eq("symbol", symbol).order("time", desc=False).execute()
        df_final = pd.DataFrame(res.data)

        # Nếu DB vẫn trống (do lỗi ghi), trả về chính df_new để biểu đồ vẫn hiện
        if df_final.empty and not df_new.empty:
            return df_new

    except Exception as e:
        # Nếu lỗi DB, tải trực tiếp từ Yahoo để không làm gián đoạn biểu đồ
        df_fallback = yf.Ticker(symbol).history(period="1mo", interval="1d")
        if not df_fallback.empty:
            df_fallback = df_fallback.reset_index().rename(columns={'Date': 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            df_fallback['time'] = pd.to_datetime(df_fallback['time'], utc=True).apply(lambda x: int(x.timestamp()))
            return df_fallback
            
    return df_final
