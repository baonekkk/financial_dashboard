import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# Thư mục lưu trữ dữ liệu
STORAGE_DIR = "data_storage"
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def get_stock_data(symbol: str, period: str = "max", interval: str = "1d"):
    """
    Lấy dữ liệu với cơ chế lưu local và cập nhật ngày mới nhất.
    """
    file_path = os.path.join(STORAGE_DIR, f"{symbol.replace('^', 'INDEX')}.parquet")
    
    # 1. KIỂM TRA XEM ĐÃ CÓ DỮ LIỆU CŨ CHƯA
    if os.path.exists(file_path):
        df_old = pd.read_parquet(file_path)
        # Chuyển cột time về datetime để so sánh
        df_old['time_dt'] = pd.to_datetime(df_old['time'], unit='s', utc=True)
        last_date = df_old['time_dt'].max()
        
        # Nếu dữ liệu mới nhất chưa quá 1 ngày (tránh gọi API quá nhiều trong ngày)
        if datetime.now(last_date.tzinfo) - last_date < timedelta(hours=12):
            return df_old.drop(columns=['time_dt'])

        try:
            # 2. TẢI BÙ DỮ LIỆU MỚI
            ticker = yf.Ticker(symbol)
            # Tải từ ngày cuối cùng của dữ liệu cũ + 1 ngày
            start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            df_new = ticker.history(start=start_date, interval=interval)
            
            if df_new.empty:
                return df_old.drop(columns=['time_dt'])
            
            # Chuẩn hóa df_new
            df_new = df_new.reset_index()
            df_new = df_new.rename(columns={
                'Date': 'time', 'Datetime': 'time', 'Open': 'open',
                'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
            })
            df_new = df_new.dropna(subset=['close'])
            df_new['time'] = pd.to_datetime(df_new['time'], utc=True).apply(lambda x: int(x.timestamp()))
            
            # 3. GỘP DỮ LIỆU
            df_combined = pd.concat([df_old.drop(columns=['time_dt']), df_new], ignore_index=True)
            # Xóa trùng lặp nếu có
            df_combined = df_combined.drop_duplicates(subset=['time'], keep='last').sort_values('time')
            
            # Lưu lại file mới
            df_combined.to_parquet(file_path)
            return df_combined
            
        except Exception:
            return df_old.drop(columns=['time_dt'])

    # 4. NẾU CHƯA CÓ FILE (LẦN ĐẦU CHẠY)
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty: return pd.DataFrame()
        
        df = df.reset_index()
        df = df.rename(columns={
            'Date': 'time', 'Datetime': 'time', 'Open': 'open',
            'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
        })
        df = df.dropna(subset=['close'])
        df['time'] = pd.to_datetime(df['time'], utc=True).apply(lambda x: int(x.timestamp()))
        
        # Lưu lần đầu
        cols_to_keep = [col for col in ['time', 'open', 'high', 'low', 'close', 'volume'] if col in df.columns]
        df_save = df[cols_to_keep]
        df_save.to_parquet(file_path)
        
        return df_save
    except Exception:
        return pd.DataFrame()
