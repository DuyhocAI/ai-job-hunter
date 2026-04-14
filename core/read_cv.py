import fitz
import json
import os
import re
import requests
import time
from datetime import datetime # THÊM THƯ VIỆN NÀY ĐỂ LẤY NGÀY GIỜ THỰC TẾ

class CVReader:
    def __init__(self, pdf_path):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Không tìm thấy file: {pdf_path}")
        self.pdf_path = pdf_path
        self.raw_text = ""

    def extract_text(self):
        doc = fitz.open(self.pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text")
        doc.close()
        
        max_chars = 3000
        if len(text) > max_chars:
            self.raw_text = text[:max_chars] + "\n...[Đã cắt bớt để tối ưu]"
        else:
            self.raw_text = text
            
        print(f"-> Đã trích xuất được {len(self.raw_text)} ký tự từ CV.")
        return self.raw_text

    def refine_cv_data(self, api_key, base_url, model_name, output_path, max_retries=3):
        print("Đang gửi dữ liệu CV cho AI phân tích...")
        
        # Lấy ngày tháng năm hiện tại (Ví dụ: April 2026)
        current_date = datetime.now().strftime("%B %Y")
        
        # ĐÃ SỬA PROMPT: Bơm current_date vào để AI tính toán chính xác
        prompt = f"""
        Hôm nay là {current_date}.
        Dựa vào text CV này: {self.raw_text}
        Hãy tạo một file JSON chứa:
        1. target_job_title: 1 Chức danh công việc phổ biến nhất phù hợp với CV này (VD: "AI Engineer"). Viết bằng Tiếng Anh, tối đa 3 từ.
        2. skills: Danh sách các framework/ngôn ngữ.
        3. projects: Các dự án chính.
        4. experience_years: Tổng số năm kinh nghiệm làm việc tính đến thời điểm hiện tại ({current_date}). Hãy tính toán từ các mốc thời gian trong CV so với {current_date}. Trả về một con số (float), ví dụ: 2.5
        
        Trả về JSON thuần túy, không có markdown.
        """
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "stream": False 
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(base_url, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    if not response.text.strip():
                        print("   [!] API trả về chuỗi rỗng hoàn toàn.")
                    else:
                        try:
                            data = response.json()
                            content = data["choices"][0]["message"]["content"]
                            clean_json = re.sub(r'```json|```', '', content).strip()
                            
                            with open(output_path, "w", encoding="utf-8") as f:
                                f.write(clean_json)
                            print("--- Thành công: Đã lưu CV ---")
                            return 
                        except Exception as json_err:
                            print(f"   [!] Lỗi bóc tách JSON từ AI (Lần {attempt+1}): {json_err}")
                else:
                    print(f"   [!] Lỗi API (Mã {response.status_code}): {response.text[:200]}")
                    
            except Exception as e:
                print(f"   [X] Lỗi kết nối mạng (Lần {attempt+1}): {e}")
            
            if attempt < max_retries - 1:
                print("   ⏳ Đang đợi 5s để thử lại...")
                time.sleep(5)
                
        raise Exception("Không thể kết nối với AI sau 3 lần thử. API có thể đang bảo trì.")