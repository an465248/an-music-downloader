from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
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

# Sabhi tarah ke download endpoints ko JSON format me handle karega
@app.api_route("/download", methods=["GET", "POST"])
@app.api_route("/api/download", methods=["GET", "POST"])
@app.api_route("/{full_path:path}", methods=["GET", "POST"])
async def handle_download(request: Request, full_path: str = ""):
    url = None
    format_type = "video"

    # 1. Check JSON body (agar JS fetch se aaya ho)
    try:
        json_data = await request.json()
        if isinstance(json_data, dict):
            url = json_data.get("url") or json_data.get("link") or json_data.get("video_url")
            format_type = json_data.get("format_type", "video")
    except:
        pass

    # 2. Check Form body
    if not url:
        try:
            form_data = await request.form()
            url = form_data.get("url") or form_data.get("link") or form_data.get("video_url")
            format_type = form_data.get("format_type", "video")
        except:
            pass

    # 3. Check Query Parameters (?url=...)
    if not url:
        url = request.query_params.get("url") or request.query_params.get("link")

    if not url:
        return JSONResponse(status_code=400, content={"status": "error", "message": "YouTube URL missing!"})

    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best',
        'noplaylist': True,
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            download_url = info.get('url')
            title = info.get('title', 'video')

            if download_url:
                # JavaScript ko valid JSON return karega
                return JSONResponse(content={
                    "status": "success",
                    "success": True,
                    "url": download_url,
                    "download_url": download_url,
                    "title": title
                })
            else:
                return JSONResponse(status_code=400, content={"status": "error", "message": "Could not extract link."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
