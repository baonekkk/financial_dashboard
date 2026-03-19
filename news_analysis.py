import feedparser
import replicate
from replicate.client import Client
import httpx
import os
import datetime
import time
import json

# --- CẤU HÌNH ---
REPLICATE_API_TOKEN = "r8_9wM7INcGBzJqFDDGgOqhWs8LLSRYsSy1IIaoA"
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
STORAGE_DIR = "news_storage"

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

custom_timeout = httpx.Timeout(600.0, connect=60.0, read=600.0, write=60.0)
replicate_client = Client(api_token=REPLICATE_API_TOKEN, timeout=custom_timeout)
MODEL_ID = "google/gemini-2.5-flash"

def get_file_path(date_obj, session="13h"):
    date_str = date_obj.strftime("%Y-%m-%d")
    return os.path.join(STORAGE_DIR, f"{date_str}_{session}.json")

def get_all_news_context_by_date(target_date):
    context = []
    sources = {
        "THẾ GIỚI": [
            "https://vnexpress.net/rss/the-gioi.rss", "https://dantri.com.vn/rss/the-gioi.rss",
            "https://tuoitre.vn/rss/the-gioi.rss", "https://cafef.vn/tai-chinh-quoc-te.rss",
            "https://vietstock.vn/rss/quoc-te.rss", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
            "https://www.scmp.com/rss/91/feed", "https://mainichi.jp/english/rss/release/business.xml",
            "https://en.yna.co.kr/RSS/news.xml", "https://www.aljazeera.com/xml/rss/all.xml",
            "https://rss.dw.com/rdf/rss-en-eu"
        ],
        "KINH DOANH": [
            "https://cafef.vn/thi-truong-chung-khoan.rss", "https://cafef.vn/doanh-nghiep.rss",
            "https://cafef.vn/tai-chinh-ngan-hang.rss", "https://cafef.vn/vi-mo-dau-tu.rss",
            "https://vietstock.vn/rss/thi-truong-chung-khoan.rss", "https://vietstock.vn/rss/kinh-te-vi-mo.rss",
            "https://vnexpress.net/rss/kinh-doanh.rss", "https://dantri.com.vn/rss/kinh-doanh.rss",
            "https://tuoitre.vn/rss/kinh-doanh.rss"
        ]
    }
    
    for category, urls in sources.items():
        context.append(f"\n--- TIN {category} ---")
        for url in urls:
            try:
                feed = feedparser.parse(url)
                s = "News"
                if "cafef" in url: s = "CafeF"
                elif "vietstock" in url: s = "Vietstock"
                elif "vnexpress" in url: s = "VNExpress"
                elif "dantri" in url: s = "Dân Trí"
                elif "tuoitre" in url: s = "Tuổi Trẻ"
                elif "nytimes" in url: s = "NYTimes"
                elif "scmp" in url: s = "SCMP"
                elif "mainichi" in url: s = "Mainichi"
                elif "yna.co.kr" in url: s = "Yonhap"
                elif "aljazeera" in url: s = "Al Jazeera"
                elif "dw.com" in url: s = "DW"
                
                for entry in feed.entries:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed)).date()
                        if pub_date == target_date:
                            context.append(f"[{s}] {entry.title.strip()} (Link: {entry.link})")
            except: continue
    return "\n".join(context)

def analyze_news(target_date, session="13h"):
    full_data = get_all_news_context_by_date(target_date)
    if not full_data.strip() or len(full_data.split('\n')) < 5:
        yield None
        return

    file_path = get_file_path(target_date, session)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("")

    prompt = f"""
    DỮ LIỆU TIN TỨC TỔNG HỢP NGÀY {target_date}:
    {full_data}

    NHIỆM VỤ:
    1. Phân tích toàn bộ dữ liệu để đưa ra đánh giá thị trường.
    2. Tách tin nóng vào world_news và business_news.
    3. GIỚI HẠN TRÍCH DẪN NGHIÊM NGẶT: Với mỗi nguồn báo, bạn chỉ được phép trích dẫn TỐI ĐA 3 liên kết tiêu biểu nhất. 
    4. Tách biệt hoàn toàn phần 'explanation' (chữ) và 'sources' (mảng link dạng "[Tên Báo](Link)").
    5. Tại trường 'general_sentiment', BẮT BUỘC ghi theo định dạng: **[Trạng thái]** | Điểm tác động: [X] | Độ chắc chắn: [Y]%.
       - [Trạng thái]: Chỉ dùng và bắt buộc in đậm 1 trong 3 cụm từ: **Tích Cực**, **Tiêu Cực**, **Trung Lập**.
       - [X]: Chấm điểm từ -100 đến +100 về mức độ ảnh hưởng tới TTCK Việt Nam (-100 = rất xấu, chắc chắn gây giảm sâu; +100 = rất tốt, chắc chắn gây hồi phục mạnh).
       - [Y]: Tự đánh giá tỷ lệ % độ chắc chắn của bạn về số điểm này.
    6. Tại phần `market_summary`, các trường `overall_impact`, `sector_impact`, `potential_sectors` BẮT BUỘC phải tự đánh giá và ghi thêm Điểm tác động (-100 đến +100) và Độ chắc chắn (%) ở cuối câu phân tích.
    7. Thêm trường `next_scenarios` vào trong `market_summary` để dự báo 3 kịch bản: `positive` (Tích cực), `negative` (Tiêu cực), `most_likely` (Khả năng cao). Mỗi kịch bản phải ghi rõ: Xác suất xảy ra (%), Giải thích chi tiết nguyên nhân, và Độ chắc chắn (%).

    CẤU TRÚC JSON:
    {{
        "market_summary": {{ 
            "overall_impact": "... | Điểm tác động: X | Độ chắc chắn: Y%", 
            "sector_impact": "... | Điểm tác động: X | Độ chắc chắn: Y%", 
            "potential_sectors": "... | Điểm tác động: X | Độ chắc chắn: Y%",
            "next_scenarios": {{
                "positive": "Xác suất: X% | Giải thích: ... | Độ chắc chắn: Y%",
                "negative": "Xác suất: X% | Giải thích: ... | Độ chắc chắn: Y%",
                "most_likely": "Xác suất: X% | Giải thích: ... | Độ chắc chắn: Y%"
            }}
        }},
        "world_news": [
            {{
                "title": "...",
                "explanation": "...",
                "sources": ["[Báo A](link1)", "[Báo B](link2)"],
                "general_sentiment": "**Tích Cực** | Điểm tác động: +80 | Độ chắc chắn: 90%",
                "vn_market_impact": "...",
                "sector_impact": "...",
                "ticker_impact": "..."
            }}
        ],
        "business_news": [...]
    }}
    """

    try:
        for event in replicate_client.stream(
            MODEL_ID,
            input={
                "prompt": prompt,
                "system_instruction": "Bạn là chuyên gia tài chính. Hãy lướt qua tất cả nguồn tin nhưng chỉ trích dẫn tối đa 3 link cho mỗi đầu báo. Chỉ trả về JSON.",
                "temperature": 0.1
            }
        ):
            chunk = ""
            if isinstance(event, str): chunk = event
            elif hasattr(event, "data") and event.data: chunk = str(event.data)
            elif hasattr(event, "text") and event.text: chunk = str(event.text)
            
            if chunk:
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(chunk)
                    f.flush()
                yield chunk
    except Exception as e:
        if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
            os.remove(file_path)
        yield f"LỖI_API: {str(e)}"
