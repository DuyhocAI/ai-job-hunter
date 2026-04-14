from playwright.sync_api import sync_playwright
import time
import json

def crawl_topcv(keyword="AI Engineer", limit=3, output_path="data/scraped_jobs.json"):
    print(f"Đang khởi động Bot quét TopCV cho từ khóa: '{keyword}'...")
    jobs = []

    with sync_playwright() as p:
        # 1. Khởi tạo trình duyệt: Có giao diện, thao tác chậm lại (slow_mo) để giống người
        browser = p.chromium.launch(headless=False, slow_mo=500)
        
        # 2. Ngụy trang (User-Agent): Giả lập người dùng Windows 11 dùng Chrome
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        search_url = f"https://www.topcv.vn/tim-viec-lam-{keyword.replace(' ', '-')}"
        print(f"Truy cập: {search_url}")
        
        try:
            # 3. Chờ load trang. NẾU BỊ CLOUDFLARE CHẶN (HIỆN CAPTCHA), HÃY TỰ LẤY CHUỘT CLICK XÁC NHẬN!
            page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000) # Nghỉ 3s chờ trang ổn định
        except Exception as e:
            print(f"Lỗi khi load trang tìm kiếm: {e}")
            browser.close()
            return

        # 4. Tìm các thẻ chứa link công việc
        print("Đang tìm kiếm các Job...")
        job_elements = page.locator('h3.title a').all()

        urls = []
        for element in job_elements:
            href = element.get_attribute('href')
            if href and "viec-lam" in href:
                urls.append(href)
                if len(urls) >= limit: 
                    break

        print(f"-> Tìm thấy {len(urls)} job. Bắt đầu vào từng Job để đọc JD...")

        # 5. Vào từng Job để trích xuất dữ liệu
        for url in urls:
            print(f"Đang đọc: {url}")
            
            try:
                # Bọc trong try-except để nếu 1 Job bị lỗi thì không chết toàn bộ tiến trình
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000) 

                # Lấy Tiêu đề
                title_locator = page.locator('h1.job-detail__info--title')
                title = title_locator.inner_text() if title_locator.count() > 0 else "Không lấy được tiêu đề"

                # Lấy Nội dung chi tiết (JD)
                jd_locator = page.locator('.job-detail__information-detail')
                jd_text = jd_locator.inner_text() if jd_locator.count() > 0 else "Không lấy được JD"

                jobs.append({
                    "title": title,
                    "url": url,
                    "jd_text": jd_text
                })
            except Exception as e:
                print(f"  [!] Bỏ qua Job này do lỗi load trang hoặc bị chặn: {e}")
                continue

        # Đóng trình duyệt
        browser.close()

    # 6. Lưu file JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=4)
    print(f"--- HOÀN THÀNH: Đã lưu {len(jobs)} Job cào được vào file {output_path} ---")

if __name__ == "__main__":
    # Mã chạy thử nghiệm độc lập
    crawl_topcv(keyword="AI Engineer", limit=2, output_path="scraped_jobs.json")