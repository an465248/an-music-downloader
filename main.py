from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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

# Kisi bhi URL / path par aane wali request ko yeh handle karega
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, full_path: str):
    url = None
    format_type = "video"

    # 1. Form data check
    try:
        form_data = await request.form()
        url = form_data.get("url") or form_data.get("link") or form_data.get("video_url") or form_data.get("query")
        format_type = form_data.get("format_type", "video")
    except:
        pass

    # 2. JSON data check
    if not url:
        try:
            json_data = await request.json()
            url = json_data.get("url") or json_data.get("link") or json_data.get("video_url") or json_data.get("query")
            format_type = json_data.get("format_type", "video")
        except:
            pass

    # 3. URL Query Parameter check
    if not url:
        url = request.query_params.get("url") or request.query_params.get("link") or request.query_params.get("q")

    # Agar link nahi mila, toh home page wapas bhej do
    if not url:
        return RedirectResponse(url="/", status_code=303)

    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            download_url = info.get('url')

            if download_url:
                return RedirectResponse(url=download_url, status_code=303)
            else:
                return HTMLResponse(content="<h3>Direct link nahi mila. Dusra video try karein!</h3><p><a href='/'>Go Back</a></p>")

    except Exception as e:
        return HTMLResponse(content=f"<h3>Error: {str(e)}</h3><p><a href='/'>Go Back</a></p>")
