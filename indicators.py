import pandas as pd
import ta

def calculate_indicators(df, indicators_list):
    """
    Tính toán các chỉ số kỹ thuật dựa trên danh sách người dùng chọn.
    Phân loại theo nhóm: Xu hướng, Động lượng, Biến động và Khối lượng.
    """
    # Tránh cảnh báo SettingWithCopyWarning của Pandas
    df = df.copy()
        
    # --- 1. NHÓM XU HƯỚNG (TREND INDICATORS) ---
    if "MA20" in indicators_list: 
        df['MA20'] = ta.trend.sma_indicator(close=df['close'], window=20)
        
    if "MA50" in indicators_list: 
        df['MA50'] = ta.trend.sma_indicator(close=df['close'], window=50)
    
    if "EMA20" in indicators_list: 
        df['EMA20'] = ta.trend.ema_indicator(close=df['close'], window=20)
        
    if "EMA50" in indicators_list: 
        df['EMA50'] = ta.trend.ema_indicator(close=df['close'], window=50)

    if "MACD" in indicators_list:
        indicator_macd = ta.trend.MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
        df['MACD'] = indicator_macd.macd()
        df['MACD_SIGNAL'] = indicator_macd.macd_signal()
        df['MACD_HIST'] = indicator_macd.macd_diff()

    if "ADX" in indicators_list:
        indicator_adx = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14)
        df['ADX'] = indicator_adx.adx()
        df['ADX_POS'] = indicator_adx.adx_pos()
        df['ADX_NEG'] = indicator_adx.adx_neg()

    if "CCI" in indicators_list:
        df['CCI'] = ta.trend.cci(high=df['high'], low=df['low'], close=df['close'], window=20)

    # --- 2. NHÓM ĐỘNG LƯỢNG (MOMENTUM INDICATORS) ---
    if "RSI (14)" in indicators_list:
        df['RSI'] = ta.momentum.rsi(close=df['close'], window=14)

    if "Stochastic" in indicators_list:
        indicator_stoch = ta.momentum.StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3)
        df['STOCH_K'] = indicator_stoch.stoch()
        df['STOCH_D'] = indicator_stoch.stoch_signal()

    # --- 3. NHÓM BIẾN ĐỘNG (VOLATILITY INDICATORS) ---
    if "Bollinger Bands" in indicators_list:
        indicator_bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
        df['BB_MA'] = indicator_bb.bollinger_mavg()
        df['BB_UPPER'] = indicator_bb.bollinger_hband()
        df['BB_LOWER'] = indicator_bb.bollinger_lband()
        df['BB_STD'] = (df['BB_UPPER'] - df['BB_MA']) / 2

    if "ATR" in indicators_list:
        df['ATR'] = ta.volatility.average_true_range(high=df['high'], low=df['low'], close=df['close'], window=14)

    # --- 4. NHÓM KHỐI LƯỢNG (VOLUME INDICATORS) ---
    if "OBV" in indicators_list:
        df['OBV'] = ta.volume.on_balance_volume(close=df['close'], volume=df['volume'])

    if "VWAP" in indicators_list:
        df['VWAP'] = ta.volume.volume_weighted_average_price(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])
        
    return df
