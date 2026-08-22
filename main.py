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

@app.api_route("/api/info", methods=["GET", "POST", "OPTIONS"])
async def get_info(request: Request):
    if request.method == "OPTIONS": return JSONResponse(content={"status": "ok"})
    return JSONResponse(content={
        "id": "video",
        "title": "AnMusic Download Ready",
        "thumbnail": "https://www.youtube.com/img/desktop/yt_1200.png",
        "formats": [
            {"format_id": "mp4", "ext": "mp4", "format_note": "Video"},
            {"format_id": "mp3", "ext": "mp3", "format_note": "Audio"}
        ]
    })

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
            data = json.loads(body)
            url = data.get("url") or data.get("link")
            format_type = data.get("format_type", "video")
        
        if not url:
            url = request.query_params.get("url") or request.query_params.get("link")

        # === X-RAY LOGS START ===
        print(f"==> DOWNLOADING: {url} | FORMAT: {format_type}")

        cobalt_instances = [
            "https://co.wuk.sh/api/json",
            "https://api.cobalt.tools/api/json",
            "https://cobalt.owo.vc/api/json"
        ]
        
        payload = json.dumps({
            "url": url,
            "isAudioOnly": True if format_type == 'audio' else False
        }).encode("utf-8")
        
        for instance in cobalt_instances:
            print(f"==> TRYING SERVER: {instance}")
            try:
                req = urllib.request.Request(
                    instance,
                    data=payload,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    d_url = res.get("url") or (res.get("picker")[0].get("url") if res.get("picker") else None)
                    
                    if d_url:
                        print(f"==> SUCCESS WITH {instance} 🎉")
                        return JSONResponse(content={"success": True, "url": d_url, "download_url": d_url})
            except Exception as ex:
                print(f"==> SERVER FAILED ({instance}): {str(ex)}")
                continue
        
        print("==> 🚨 ALL SERVERS BLOCKED RENDER IP!")
        return JSONResponse(status_code=400, content={"error": True, "success": False, "message": "All servers blocked."})

    except Exception as e:
        print(f"==> 🚨 CRITICAL ERROR: {str(e)}")
        return JSONResponse(status_code=500, content={"error": True, "success": False, "message": str(e)})
        
