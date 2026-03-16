import yfinance as yf
import pandas as pd

def get_stock_data(symbol: str, period: str = "1mo", interval: str = "1d"):
    """
    Lấy dữ liệu lịch sử từ Yahoo Finance.
    - symbol: Mã chứng khoán (VD: 'AAPL', 'BTC-USD')
    - period: Khoảng thời gian (1d, 5d, 1mo, 3mo, 6mo, 1y, max)
    - interval: Tần suất nến (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    """
    # Tải dữ liệu
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    
    # Reset index để đưa cột 'Date' thành một cột dữ liệu
    df = df.reset_index()
    
    # Chuẩn hóa tên cột để tương thích với lightweight_charts
    # lightweight_charts yêu cầu các cột: 'time', 'open', 'high', 'low', 'close'
    df = df.rename(columns={
        'Date': 'time',
        'Datetime': 'time',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })
    
    # Xóa các dòng bị thiếu dữ liệu giá (do khác biệt tần suất/ngày nghỉ)
    if 'close' in df.columns:
        df = df.dropna(subset=['close'])
    
    # Xử lý thời gian sang Unix timestamp
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], utc=True).apply(lambda x: int(x.timestamp()))
        
    # Chỉ trả về các cột thực sự có trong dữ liệu
    cols_to_keep = [col for col in ['time', 'open', 'high', 'low', 'close', 'volume'] if col in df.columns]
    return df[cols_to_keep]