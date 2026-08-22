from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import urllib.request
import urllib.parse
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
        "title": "Ready to Download!",
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

        # तरीका 1: Cobalt API (अब एकदम सही Headers के साथ)
        try:
            cobalt_url = "https://api.cobalt.tools/api/json"
            payload = json.dumps({
                "url": url,
                "isAudioOnly": True if format_type == 'audio' else False
            }).encode("utf-8")
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "https://cobalt.tools",
                "Referer": "https://cobalt.tools/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            
            req = urllib.request.Request(cobalt_url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                res = json.loads(response.read().decode("utf-8"))
                download_url = res.get("url") or (res.get("picker")[0].get("url") if res.get("picker") else None)
        except Exception as e:
            pass # अगर Cobalt फेल हुआ, तो तरीका 2 इस्तेमाल होगा

        # तरीका 2: Ryzen API (बिना किसी रुकावट वाला बैकअप)
        if not download_url:
            try:
                encoded_url = urllib.parse.quote(url)
                if format_type == 'audio':
                    alt_url = f"https://api.siputzx.my.id/api/d/ytmp3?url={encoded_url}"
                else:
                    alt_url = f"https://api.siputzx.my.id/api/d/ytmp4?url={encoded_url}"
                
                req2 = urllib.request.Request(alt_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=10) as response2:
                    res2 = json.loads(response2.read().decode("utf-8"))
                    if res2.get("status"):
                        download_url = res2.get("data", {}).get("dl")
            except Exception:
                pass

        if download_url:
            return JSONResponse(content={
                "success": True,
                "url": download_url,
                "download_url": download_url
            })
        else:
            return JSONResponse(status_code=400, content={"error": True, "message": "Failed! Server APIs change ho gaye hain."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": str(e)})
        
