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

    # 1. JSON Request Check
    try:
        json_data = await request.json()
        if isinstance(json_data, dict):
            url = json_data.get("url") or json_data.get("link") or json_data.get("video_url")
            format_type = json_data.get("format_type", "video")
    except Exception:
        pass

    # 2. Form Data Check
    if not url:
        try:
            form_data = await request.form()
            url = form_data.get("url") or form_data.get("link") or form_data.get("video_url")
            format_type = form_data.get("format_type", "video")
        except Exception:
            pass

    # 3. Query Param Check
    if not url:
        url = request.query_params.get("url") or request.query_params.get("link")

    if not url:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Link nahi mila"})

    # Render IP block bypass settings
    ydl_opts = {
        'format': 'best[ext=mp4]/best' if format_type == 'video' else 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android_creator', 'web'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Formats list se valid direct URL nikalna
            download_url = None
            if 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('url') and f.get('acodec') != 'none':
                        download_url = f.get('url')
                        break
            
            if not download_url:
                download_url = info.get('url')

            title = info.get('title', 'Video')

            if download_url:
                return JSONResponse(content={
                    "status": "success",
                    "success": True,
                    "url": download_url,
                    "download_url": download_url,
                    "link": download_url,
                    "title": title
                })
            else:
                return JSONResponse(status_code=400, content={"status": "error", "message": "Link generate nahi ho saka"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Server Error: {str(e)}"})
