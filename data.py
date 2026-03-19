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
    Lấy dữ liệu với cơ chế lưu local (Parquet) và cập nhật ngày mới nhất.
    Đã chuẩn hóa để luôn có đủ các cột: time, open, high, low, close, volume.
    """
    file_path = os.path.join(STORAGE_DIR, f"{symbol.replace('^', 'INDEX')}.parquet")
    
    # 1. KIỂM TRA XEM ĐÃ CÓ DỮ LIỆU CŨ CHƯA
    if os.path.exists(file_path):
        df_old = pd.read_parquet(file_path)
        # Chuyển cột time về datetime để so sánh
        df_old['time_dt'] = pd.to_datetime(df_old['time'], unit='s', utc=True)
        last_date = df_old['time_dt'].max()
        
        # GIẢI QUYẾT YÊU CẦU: Trả ra file data mỗi 15 phút
        if datetime.now(last_date.tzinfo) - last_date < timedelta(minutes=15):
            return df_old.drop(columns=['time_dt'])

        try:
            # 2. TẢI BÙ DỮ LIỆU MỚI
            ticker = yf.Ticker(symbol)
            # GIẢI QUYẾT YÊU CẦU: Dùng period="1mo" để lấy luôn dữ liệu real-time mới nhất, chống lỗi thiếu ngày do lệch múi giờ
            df_new = ticker.history(period="1mo", interval=interval)
            
            if df_new.empty:
                return df_old.drop(columns=['time_dt'])
            
            # Chuẩn hóa df_new
            df_new = df_new.reset_index()
            df_new = df_new.rename(columns={
                'Date': 'time', 'Datetime': 'time', 'Open': 'open',
                'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
            })
            
            # Xử lý trường hợp thiếu cột volume (thường gặp ở các chỉ số)
            if 'volume' not in df_new.columns:
                df_new['volume'] = 0
                
            df_new = df_new.dropna(subset=['close'])
            df_new['time'] = pd.to_datetime(df_new['time'], utc=True).apply(lambda x: int(x.timestamp()))
            
            # Chỉ giữ lại đúng các cột cần thiết trước khi gộp
            cols_to_keep = ['time', 'open', 'high', 'low', 'close', 'volume']
            df_new = df_new[[c for c in cols_to_keep if c in df_new.columns]]
            
            # 3. GỘP DỮ LIỆU
            df_combined = pd.concat([df_old.drop(columns=['time_dt']), df_new], ignore_index=True)
            # Xóa trùng lặp nếu có
            df_combined = df_combined.drop_duplicates(subset=['time'], keep='last').sort_values('time')
            
            # Lưu lại file mới đè lên file cũ
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
        
        if 'volume' not in df.columns:
            df['volume'] = 0
            
        df = df.dropna(subset=['close'])
        df['time'] = pd.to_datetime(df['time'], utc=True).apply(lambda x: int(x.timestamp()))
        
        # Lưu lần đầu
        cols_to_keep = ['time', 'open', 'high', 'low', 'close', 'volume']
        df_save = df[[col for col in cols_to_keep if col in df.columns]]
        df_save.to_parquet(file_path)
        
        return df_save
    except Exception:
        return pd.DataFrame()
