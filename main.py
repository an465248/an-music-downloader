from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import urllib.request
import json
import os
import re

app = FastAPI(title="AnMusic Downloader")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>index.html not found!</h3>"

# YouTube Video ID निकालने का फंक्शन
def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|/|$)", url)
    if match:
        return match.group(1)
    return None

@app.api_route("/api/info", methods=["GET", "POST", "OPTIONS"])
async def get_info(request: Request):
    if request.method == "OPTIONS":
        return JSONResponse(content={"status": "ok"})
        
    url = request.query_params.get("url") or request.query_params.get("link")
    if not url:
        return JSONResponse(status_code=400, content={"error": "URL missing"})

    return JSONResponse(content={
        "id": "video",
        "title": "Ready to Download",
        "thumbnail": "https://www.youtube.com/img/desktop/yt_1200.png",
        "formats": [
            {"format_id": "mp4", "ext": "mp4", "format_note": "Video (HD)"},
            {"format_id": "mp3", "ext": "mp3", "format_note": "Audio"}
        ]
    })

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
                pass
        
        if not url:
            url = request.query_params.get("url") or request.query_params.get("link")

        if not url:
            return JSONResponse(status_code=400, content={"error": True, "success": False, "message": "Link nahi mila"})

        video_id = extract_video_id(url)
        if not video_id:
            return JSONResponse(status_code=400, content={"error": True, "success": False, "message": "YouTube Video ID nahi mila"})

        # === PIPED API MULTI-SERVER BYPASS (ब्लॉक नहीं होगा) ===
        instances = [
            "https://pipedapi.kavin.rocks", 
            "https://pipedapi.tokhmi.xyz", 
            "https://api.piped.projectsegfau.lt"
        ]
        
        download_url = None
        
        for instance in instances:
            try:
                api_url = f"{instance}/streams/{video_id}"
                req = urllib.request.Request(
                    api_url, 
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=8) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    
                    if format_type == 'audio' and result.get("audioStreams"):
                        download_url = result["audioStreams"][-1].get("url") 
                    elif result.get("videoStreams"):
                        download_url = result["videoStreams"][0].get("url")
                    
                    if download_url:
                        break # लिंक मिल गया, लूप से बाहर आओ!
            except Exception:
                continue # अगर यह सर्वर डाउन है, तो अगला ट्राई करो

        if download_url:
            return JSONResponse(content={
                "success": True,
                "url": download_url,
                "download_url": download_url,
                "title": "AnMusic Download"
            })
        else:
            return JSONResponse(status_code=400, content={"error": True, "success": False, "message": "Sare servers busy hain, thodi der baad try karein"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "success": False, "message": f"Server Error: {str(e)}"})
        
