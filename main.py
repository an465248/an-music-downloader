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

@app.api_route("/api/info", methods=["GET", "POST", "OPTIONS"])
async def get_info(request: Request):
    if request.method == "OPTIONS": return JSONResponse(content={"status": "ok"})
    return JSONResponse(content={
        "id": "video",
        "title": "Ready to Download!",
        "thumbnail": "https://www.youtube.com/img/desktop/yt_1200.png",
        "formats": [
            {"format_id": "mp4", "ext": "mp4", "format_note": "Video"},
            {"format_id": "mp3", "ext": "mp3", "format_note": "Audio"}
        ]
    })

# YouTube Video ID निकालने का फंक्शन
def get_yt_id(url):
    m = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|/|$)", url)
    return m.group(1) if m else None

@app.api_route("/download", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/api/download", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/{full_path:path}", methods=["GET", "POST", "OPTIONS"])
async def handle_download(request: Request, full_path: str = ""):
    if request.method == "OPTIONS": return JSONResponse(content={"status": "ok"})
    
    try:
        url = None
        format_type = "video"
        
        body = await request.body()
        if body:
            try:
                data = json.loads(body)
                url = data.get("url") or data.get("link")
                format_type = data.get("format_type", "video")
            except: pass
        
        if not url:
            url = request.query_params.get("url") or request.query_params.get("link")

        if not url:
            return JSONResponse(status_code=400, content={"error": True, "message": "Link nahi mila"})

        download_url = None
        domain = url.lower()
        
        # === 1. YOUTUBE BYPASS (Invidious Network - कभी ब्लॉक नहीं होगा) ===
        if "youtube.com" in domain or "youtu.be" in domain:
            vid = get_yt_id(url)
            if vid:
                # ये 4 अलग-अलग देशों के सर्वर्स हैं
                instances = [
                    "https://vid.puffyan.us",
                    "https://invidious.nerdvpn.de",
                    "https://inv.tux.pizza",
                    "https://invidious.jing.rocks"
                ]
                for inst in instances:
                    try:
                        api = f"{inst}/api/v1/videos/{vid}"
                        req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req, timeout=8) as res:
                            data = json.loads(res.read().decode("utf-8"))
                            
                            if format_type == 'audio':
                                for f in data.get("adaptiveFormats", []):
                                    if "audio" in f.get("type", ""):
                                        download_url = f.get("url")
                                        break
                            else:
                                for f in data.get("formatStreams", []):
                                    if f.get("url"):
                                        download_url = f.get("url")
                                        break
                            
                            if download_url: break # लिंक मिल गया तो बाहर आ जाओ
                    except: continue # अगर एक देश का सर्वर बंद है, तो दूसरे पर जाओ

        # === 2. INSTAGRAM / OTHERS (Cobalt Backup) ===
        if not download_url:
            try:
                payload = json.dumps({"url": url, "isAudioOnly": True if format_type == 'audio' else False}).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.cobalt.tools/api/json", 
                    data=payload, 
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Origin": "https://cobalt.tools",
                        "User-Agent": "Mozilla/5.0"
                    }, 
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    download_url = res.get("url") or (res.get("picker")[0].get("url") if res.get("picker") else None)
            except: pass

        if download_url:
            return JSONResponse(content={"success": True, "url": download_url, "download_url": download_url})
        else:
            return JSONResponse(status_code=400, content={"error": True, "message": "सारे सर्वर्स ने ब्लॉक कर दिया है।"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": str(e)})
        
