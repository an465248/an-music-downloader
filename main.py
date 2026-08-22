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

@app.api_route("/download", methods=["GET", "POST"])
@app.api_route("/api/download", methods=["GET", "POST"])
@app.api_route("/{full_path:path}", methods=["GET", "POST"])
async def handle_download(request: Request, full_path: str = ""):
    url = None
    format_type = "video"

    # 1. JSON body check
    try:
        json_data = await request.json()
        if isinstance(json_data, dict):
            url = json_data.get("url") or json_data.get("link") or json_data.get("video_url")
            format_type = json_data.get("format_type", "video")
    except Exception:
        pass

    # 2. Form body check
    if not url:
        try:
            form_data = await request.form()
            url = form_data.get("url") or form_data.get("link") or form_data.get("video_url")
            format_type = form_data.get("format_type", "video")
        except Exception:
            pass

    # 3. Query Parameter check
    if not url:
        url = request.query_params.get("url") or request.query_params.get("link")

    if not url:
        return JSONResponse(status_code=400, content={"status": "error", "message": "URL missing"})

    # yt-dlp configuration with client bypass
    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Direct media URL nikalna
            download_url = info.get('url')
            
            # Agar direct url na mile toh formats me se best URL uthana
            if not download_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('url'):
                        download_url = f['url']
                        break

            title = info.get('title', 'media_file')

            if download_url:
                return JSONResponse(content={
                    "status": "success",
                    "success": True,
                    "url": download_url,
                    "download_url": download_url,
                    "title": title
                })
            else:
                return JSONResponse(status_code=400, content={"status": "error", "message": "Direct link not found"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
