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
        domain = url.lower()
        encoded_url = urllib.parse.quote(url)

        # 1. Instagram ke liye Smart APIs
        if "instagram.com" in domain:
            api_list = [
                f"https://api.siputzx.my.id/api/d/ig?url={encoded_url}",
                f"https://api.ryzendesu.vip/api/downloader/igdl?url={encoded_url}"
            ]
            for api in api_list:
                try:
                    req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as response:
                        res = json.loads(response.read().decode("utf-8"))
                        if res.get("data") and isinstance(res["data"], list) and len(res["data"]) > 0:
                            download_url = res["data"][0].get("url")
                        elif res.get("data") and isinstance(res["data"], dict):
                            download_url = res["data"].get("url")
                        if download_url: break
                except: continue

        # 2. YouTube ke liye Smart APIs
        elif "youtube.com" in domain or "youtu.be" in domain:
            t_type = "ytmp3" if format_type == 'audio' else "ytmp4"
            api_list = [
                f"https://api.siputzx.my.id/api/d/{t_type}?url={encoded_url}",
                f"https://api.ryzendesu.vip/api/downloader/{t_type}?url={encoded_url}"
            ]
            for api in api_list:
                try:
                    req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as response:
                        res = json.loads(response.read().decode("utf-8"))
                        download_url = res.get("data", {}).get("dl") or res.get("data", {}).get("url") or res.get("url")
                        if download_url: break
                except: continue

        # 3. Cobalt API (Facebook, Twitter aur baaki sabhi sites ke liye Universal Backup)
        if not download_url:
            try:
                cobalt_url = "https://api.cobalt.tools/api/json"
                payload = json.dumps({"url": url, "isAudioOnly": True if format_type == 'audio' else False}).encode("utf-8")
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Origin": "https://cobalt.tools",
                    "User-Agent": "Mozilla/5.0"
                }
                req = urllib.request.Request(cobalt_url, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=10) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    download_url = res.get("url") or (res.get("picker")[0].get("url") if res.get("picker") else None)
            except: pass

        # Final Result Return Karna
        if download_url:
            return JSONResponse(content={"success": True, "url": download_url, "download_url": download_url})
        else:
            return JSONResponse(status_code=400, content={"error": True, "message": "Link process nahi ho paya. Server busy hai."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": str(e)})
