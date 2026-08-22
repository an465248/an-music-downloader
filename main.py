from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import yt_dlp
import os
import json

app = FastAPI(title="AnMusic Downloader")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>index.html not found!</h3>"

@app.api_route("/download", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/api/download", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/{full_path:path}", methods=["GET", "POST", "OPTIONS"])
async def handle_download(request: Request, full_path: str = ""):
    if request.method == "OPTIONS":
        return JSONResponse(content={"status": "ok"})

    url = None
    format_type = "video"

    try:
        body = await request.body()
        
        if body:
            try:
                data = json.loads(body)
                url = data.get("url") or data.get("link")
                format_type = data.get("format_type", "video")
            except Exception:
                try:
                    form_data = await request.form()
                    url = form_data.get("url") or form_data.get("link")
                    format_type = form_data.get("format_type", "video")
                except Exception:
                    pass
        
        if not url:
            url = request.query_params.get("url") or request.query_params.get("link")

        if not url:
            return JSONResponse(status_code=400, content={"error": True, "success": False, "message": "Link nahi mila"})

        ydl_opts = {
            'format': 'bestaudio/best' if format_type == 'audio' else 'best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': os.path.join(BASE_DIR, 'cookies.txt'),
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            download_url = info.get('url')
            
            if not download_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('url'):
                        download_url = f['url']
                        break

            title = info.get('title', 'Video')

            if download_url:
                return JSONResponse(content={
                    "success": True,
                    "url": download_url,
                    "download_url": download_url,
                    "title": title
                })
            else:
                return JSONResponse(status_code=400, content={"error": True, "success": False, "message": "Direct link generate nahi ho saka"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "success": False, "message": f"Server Error: {str(e)}"})
