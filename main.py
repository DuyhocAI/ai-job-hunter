from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import json
import shutil # THÊM THƯ VIỆN NÀY ĐỂ ĐỔI TÊN FILE
from pydantic import BaseModel

app = FastAPI(title="AI Job Hunter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

CV_PDF_PATH = os.path.join(DATA_DIR, "uploaded_cv.pdf")
CV_JSON_PATH = os.path.join(DATA_DIR, "my_experience.json")
JOBS_JSON_PATH = os.path.join(DATA_DIR, "scraped_jobs.json")
REPORT_JSON_PATH = os.path.join(DATA_DIR, "evaluation_report.json")
TEMP_REPORT_PATH = os.path.join(DATA_DIR, "temp_report.json") # ĐƯỜNG DẪN FILE TẠM

CKEY_BASE_URL = "https://ckey.vn/v1/chat/completions"
CKEY_MODEL_NAME = "gemini-2.5-flash" 

class JobSearchRequest(BaseModel):
    limit: int = 5
    api_key: str

@app.get("/")
def read_root():
    return {"message": "AI Job Hunter API is running!"}

@app.post("/api/v1/analyze-cv")
async def analyze_cv(file: UploadFile = File(...)):
    try:
        with open(CV_PDF_PATH, "wb") as buffer:
            buffer.write(await file.read())
        # Xóa SẠCH các file cũ của lần chạy trước (Kể cả file tạm)
        for p in [CV_JSON_PATH, JOBS_JSON_PATH, REPORT_JSON_PATH, TEMP_REPORT_PATH]:
            if os.path.exists(p):
                os.remove(p)
        return {"status": "success", "message": "Đã lưu CV"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/start-hunting")
async def start_hunting(request: JobSearchRequest, background_tasks: BackgroundTasks):
    limit = request.limit
    api_key = request.api_key
    
    def run_full_pipeline():
        print(f"\n{'='*50}\nBẮT ĐẦU CHUỖI TỰ ĐỘNG\n{'='*50}")
        try:
            # 1. Đọc CV
            print("1. Đang dùng AI phân tích CV và tìm chức danh phù hợp...")
            from core.read_cv import CVReader
            reader = CVReader(CV_PDF_PATH)
            reader.extract_text()
            reader.refine_cv_data(api_key, CKEY_BASE_URL, CKEY_MODEL_NAME, CV_JSON_PATH)
            
            if not os.path.exists(CV_JSON_PATH):
                raise Exception("Lỗi cổng API: Không thể trích xuất dữ liệu từ CV.")

            # Rút trích keyword
            with open(CV_JSON_PATH, "r", encoding="utf-8") as f:
                try:
                    cv_data = json.load(f)
                    dynamic_keyword = cv_data.get("target_job_title", "")
                    if not dynamic_keyword:
                        dynamic_keyword = "AI Engineer" 
                except Exception:
                    raise Exception("Lỗi định dạng: AI trả về kết quả không phải là JSON.")
            
            # 2. Cào dữ liệu
            print(f"\n2. Đang cào tối đa {limit} job cho chức danh: '{dynamic_keyword}'...")
            from core.topcv_scraper import crawl_topcv
            crawl_topcv(keyword=dynamic_keyword, limit=limit, output_path=JOBS_JSON_PATH)
            
            if not os.path.exists(JOBS_JSON_PATH):
                 raise Exception("Bot không cào được công việc nào từ TopCV.")

            # 3. Đánh giá (LƯU VÀO FILE TẠM)
            print("\n3. Đang dùng AI đối chiếu và chấm điểm...")
            from core.job_evaluator import JobEvaluator
            evaluator = JobEvaluator(CV_JSON_PATH, JOBS_JSON_PATH, api_key, CKEY_BASE_URL, CKEY_MODEL_NAME)
            
            # ĐÃ SỬA: Chạy và lưu vào file tạm thời
            evaluator.evaluate_jobs(TEMP_REPORT_PATH)
            
            # ĐÃ SỬA: Đổi tên file tạm thành file chính thức ĐỂ KÍCH HOẠT FRONTEND
            if os.path.exists(TEMP_REPORT_PATH):
                os.rename(TEMP_REPORT_PATH, REPORT_JSON_PATH)
            
            print(f"\n{'='*50}\nHOÀN THÀNH TOÀN BỘ!\n{'='*50}")

        except Exception as e:
            print(f"\n[X] QUÁ TRÌNH BỊ GIÁN ĐOẠN: {e}")
            error_result = [{
                "job_title": "⚠️ Hệ Thống Gặp Sự Cố",
                "match_score": 0,
                "pros": ["Phát hiện lỗi kịp thời."],
                "cons": [f"Lỗi hệ thống: {str(e)}"],
                "recommendation": "Vui lòng F5 lại trang và thử lại."
            }]
            with open(REPORT_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(error_result, f, ensure_ascii=False)

    background_tasks.add_task(run_full_pipeline)
    return {"status": "started", "message": "Đang xử lý..."}

@app.get("/api/v1/results")
def get_results():
    if not os.path.exists(REPORT_JSON_PATH):
        return {"status": "processing", "data": []}
    try:
        with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Sắp xếp điểm giảm dần (Job điểm cao nhất lên đầu)
        sorted_data = sorted(data, key=lambda x: int(x.get('match_score', 0)), reverse=True)
        return {"status": "done", "data": sorted_data}
    except Exception:
        return {"status": "processing", "data": []}