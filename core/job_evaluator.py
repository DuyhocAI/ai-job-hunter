import json
import time
import re
import requests

class JobEvaluator:
    # Nhận các biến cấu hình từ bên ngoài truyền vào
    def __init__(self, cv_path, jobs_path, api_key, base_url, model_name):
        self.cv_data = self._load_json(cv_path)
        self.jobs_data = self._load_json(jobs_path)
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.results_file = "evaluation_report.json" # Giá trị mặc định

    def _load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _optimize_jd_text(self, raw_jd):
        max_chars = 2000
        if len(raw_jd) > max_chars:
            return raw_jd[:max_chars] + "\n...[Noi dung da duoc rut gon]"
        return raw_jd.strip()

    # Nhận thêm output_path để biết lưu file ở đâu
    def evaluate_jobs(self, output_path):
        self.results_file = output_path
        print(f"Bat dau danh gia {len(self.jobs_data)} cong viec...")
        print("-" * 50)
        
        evaluation_results = []
        minified_cv = json.dumps(self.cv_data, ensure_ascii=False, separators=(',', ':'))
        
        for index, job in enumerate(self.jobs_data):
            print(f"[{index + 1}/{len(self.jobs_data)}] Dang phan tich: {job['title']}")
            
            clean_jd = self._optimize_jd_text(job['jd_text'])
            
            prompt = f"""
            Vai tro: Chuyen gia tuyen dung AI.
            Nhiem vu: Danh gia do phu hop giua CV va JD.
            
            [CV cua toi]: {minified_cv}
            
            [JD cong ty]: {job['title']} - {clean_jd}
            
            Hay tra ve ket qua duy nhat duoi dang JSON voi cac truong:
            match_score (so tu 0-100), pros (mang cac diem manh), cons (mang cac diem yeu), recommendation (loi khuyen).
            Luu y: Chi tra ve JSON, khong kem loi dan giai hay ky tu markdown.
            """
            
            result = self._call_ckey_api(prompt)
            
            if result:
                result['job_title'] = job['title']
                result['url'] = job['url']
                
                evaluation_results.append(result)
                print(f"-> Diem phu hop: {result.get('match_score')}/100")
                self._save_results(evaluation_results)
            else:
                print("-> Loi: Khong the lay ket qua cho Job nay.")
            
            if index < len(self.jobs_data) - 1:
                time.sleep(5)

        print("-" * 50)
        print("Hoan thanh qua trinh danh gia.")

    def _call_ckey_api(self, prompt, max_retries=3):
        # Sử dụng các biến self đã được truyền từ main.py
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "stream": False # Đảm bảo vẫn giữ dòng tắt stream này nhé
        }
        
        for attempt in range(max_retries):
            try:
                # ĐÃ SỬA: Tăng timeout lên 120 giây (2 phút) để AI có đủ thời gian chấm điểm
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    clean_json = re.sub(r'```json|```', '', content).strip()
                    return json.loads(clean_json)
                else:
                    print(f"   [!] Loi API (Ma {response.status_code}). Dang thu lai...")
                    time.sleep(10)
            except Exception as e:
                print(f"   [X] Loi ket noi hoac phan tich (Lần {attempt+1}): {e}")
                time.sleep(5)
        return None

    def _save_results(self, data):
        with open(self.results_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)