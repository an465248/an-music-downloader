from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import yt_dlp
import os

app = FastAPI(title="AnMusic Downloader")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>index.html not found in templates folder!</h3>"

@app.api_route("/download", methods=["GET", "POST"])
async def download_file(request: Request):
    url = None
    format_type = "video"
    
    # 1. Check karein agar data Form se aaya hai
    try:
        form_data = await request.form()
        url = form_data.get("url")
        format_type = form_data.get("format_type", "video")
    except:
        pass

    # 2. Agar Form mein nahi mila, toh check karein agar JSON (JavaScript) se aaya hai
    if not url:
        try:
            json_data = await request.json()
            url = json_data.get("url")
            format_type = json_data.get("format_type", "video")
        except:
            pass

    # 3. Agar Query Parameters (?url=...) se aaya hai
    if not url:
        url = request.query_params.get("url")
        format_type = request.query_params.get("format_type", "video")

    if not url:
        return HTMLResponse(content="<h3>Error: YouTube Link nahi mila! <a href='/'>Wapas Jayein</a></h3>")

    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            download_url = info.get('url')
            
            if download_url:
                return RedirectResponse(url=download_url, status_code=303)
            else:
                return HTMLResponse(content="<h3>Download link nahi mila. Dusra video try karein!</h3><p><a href='/'>Go Back</a></p>")
                
    except Exception as e:
        return HTMLResponse(content=f"<h3>Error: {str(e)}</h3><p><a href='/'>Go Back</a></p>")
