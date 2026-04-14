AI Job Hunter (One-Click) - English Version
AI Job Hunter is an autonomous AI Agent that completely automates the job searching and matching process. With just one click and your resume (CV), the system analyzes your skills, searches for the most relevant jobs on TopCV, and uses AI to evaluate how well you match each Job Description (JD).

Key Features
🧠 Smart CV Parsing: Automatically reads PDF resumes to extract skills, calculate years of experience, and deduce the most suitable "Target Job Title".

🕷️ Stealth Web Scraping: Automatically scrapes the latest job postings from TopCV. Integrated with human-like behavior emulation (User-Agent, Slow-mo) to bypass Anti-Bot/Cloudflare systems.

📊 AI-Powered Evaluation: Uses the gemini-2.5-flash model to cross-reference your CV against scraped JDs, providing a match score (0-100), Pros, Cons, and actionable application advice.

🎮 Interactive UX: Features an integrated Mini-game (Flappy Bird) to keep users entertained while the AI processes data in the background, utilizing smooth asynchronous polling.

🏗️ Project Architecture (Core Structure)
Below is a visual representation of how files, classes, and methods interact within the system to execute the 'One-Click' workflow:

(This diagram illustrates the flow from CV upload and parsing, to job search, final AI evaluation, and result delivery.)

🛠️ Tech Stack
Backend: Python, FastAPI, Uvicorn

Web Scraping: Playwright

AI & NLP: Gemini 2.5 Flash (via ckey.vn API), PyMuPDF (PDF processing)

Frontend: HTML5, JavaScript (Vanilla), Tailwind CSS

⚙️ Installation & Setup
Prerequisites: Python 3.8+ installed on your machine.

Install dependencies:
Open your terminal and run:

Bash
pip install fastapi uvicorn playwright pymupdf requests python-multipart pydantic
Install Playwright browsers:

Bash
playwright install chromium
API Key: Obtain an API Key from ckey.vn (or OpenRouter) to power the core AI features.

🚀 How to Run
Start the Backend Server (from the root directory):

Bash
uvicorn main:app --reload
Open the index.html file in any modern web browser.

Upload your CV (PDF format), enter your API Key, select the desired job search limit, and click Start Hunting.
