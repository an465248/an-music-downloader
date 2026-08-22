from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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

# Yeh sabhi possible paths ko ek saath pakad lega taaki Not Found na aaye
@app.api_route("/download", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/download", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/submit", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/", methods=["POST"])
async def catch_all_downloads(request: Request):
    url = None
    format_type = "video"
    
    try:
        form_data = await request.form()
        url = form_data.get("url") or form_data.get("link") or form_data.get("input")
        format_type = form_data.get("format_type", "video")
    except:
        pass

    if not url:
        try:
            json_data = await request.json()
            url = json_data.get("url") or json_data.get("link")
            format_type = json_data.get("format_type", "video")
        except:
            pass

    if not url:
        url = request.query_params.get("url") or request.query_params.get("link")

    if not url:
        return HTMLResponse(content="<h3>Kripya YouTube link dalein! <a href='/'>Wapas Jayein</a></h3>")

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
                return HTMLResponse(content="<h3>Link nahi mila. Dusra try karein!</h3><p><a href='/'>Go Back</a></p>")
                
    except Exception as e:
        return HTMLResponse(content=f"<h3>Error: {str(e)}</h3><p><a href='/'>Go Back</a></p>")
