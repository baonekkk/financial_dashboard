import os
import json
import streamlit as st

def parse_news_json(file_path):
    world_news = []
    business_news = []
    market_summary = None

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                content = f.read().strip()
                start_idx = content.find('{')
                if start_idx != -1:
                    clean_content = content[start_idx:]
                    try:
                        decoder = json.JSONDecoder()
                        parsed_data, _ = decoder.raw_decode(clean_content)
                    except:
                        repair = clean_content.strip()
                        if (repair.count('"') - repair.count('\\"')) % 2 != 0: repair += '"'
                        m_brackets = repair.count('[') - repair.count(']')
                        m_braces = repair.count('{') - repair.count('}')
                        repair += ']' * max(0, m_brackets) + '}' * max(0, m_braces)
                        parsed_data = json.loads(repair)
                    
                    market_summary = parsed_data.get("market_summary")
                    world_news = parsed_data.get("world_news", [])
                    business_news = parsed_data.get("business_news", [])
            except Exception as e: 
                st.error(f"Lỗi xử lý dữ liệu: {str(e)}")
                
    return market_summary, world_news, business_news
