from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import urllib.request
import json
import os

app = FastAPI(title="AnMusic Downloader")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>index.html not found!</h3>"

# 1. INFO API (यह वेबसाइट को क्रैश होने से बचाएगा)
@app.api_route("/api/info", methods=["GET", "POST", "OPTIONS"])
async def get_info(request: Request):
    if request.method == "OPTIONS":
        return JSONResponse(content={"status": "ok"})
        
    url = request.query_params.get("url") or request.query_params.get("link")
    
    if not url:
        return JSONResponse(status_code=400, content={"error": "URL missing"})

    # वेबसाइट के फ्रंटएंड को शांत रखने के लिए डमी डेटा
    return JSONResponse(content={
        "id": "video",
        "title": "Ready to Download - YouTube Video",
        "thumbnail": "https://www.youtube.com/img/desktop/yt_1200.png",
        "formats": [
            {"format_id": "mp4", "ext": "mp4", "format_note": "Video (HD)"},
            {"format_id": "mp3", "ext": "mp3", "format_note": "Audio"}
        ]
    })

# 2. DOWNLOAD API (यह बिना yt-dlp के डायरेक्ट वीडियो निकालेगा)
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

        # === Third-Party Bypass API (No YouTube Block) ===
        api_url = "https://api.cobalt.tools/api/json"
        
        payload = {
            "url": url,
            "isAudioOnly": True if format_type == 'audio' else False
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        
        req = urllib.request.Request(
            api_url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            download_url = result.get("url")
            
            if not download_url and result.get("picker"):
                download_url = result["picker"][0].get("url")

            if download_url:
                return JSONResponse(content={
                    "success": True,
                    "url": download_url,
                    "download_url": download_url,
                    "title": "AnMusic Download"
                })
            else:
                return JSONResponse(status_code=400, content={"error": True, "success": False, "message": "Direct link generate nahi ho saka"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "success": False, "message": f"Server Error: {str(e)}"})
