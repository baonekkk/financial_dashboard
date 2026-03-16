import pandas as pd

def calculate_indicators(df, indicators_list):
    """
    Tính toán các chỉ số kỹ thuật dựa trên danh sách người dùng chọn.
    """
    # Tránh cảnh báo SettingWithCopyWarning của Pandas
    df = df.copy()
    
    if "MA20" in indicators_list: 
        df['MA20'] = df['close'].rolling(20).mean()
        
    if "MA50" in indicators_list: 
        df['MA50'] = df['close'].rolling(50).mean()
    
    if "EMA20" in indicators_list: 
        df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
        
    if "EMA50" in indicators_list: 
        df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    if "Bollinger Bands" in indicators_list:
        df['BB_MA'] = df['close'].rolling(20).mean()
        df['BB_STD'] = df['close'].rolling(20).std()
        df['BB_UPPER'] = df['BB_MA'] + 2 * df['BB_STD']
        df['BB_LOWER'] = df['BB_MA'] - 2 * df['BB_STD']
        
    if "RSI (14)" in indicators_list:
        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
    return df
