from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
import yt_dlp
import os

app = FastAPI(title="AnMusic Downloader")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home():
    # Yeh code aapke templates folder se index.html ko seedhe padh lega bina kisi Jinja2 error ke
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>index.html not found in templates folder!</h3>"

@app.post("/download")
async def download_file(url: str = Form(...), format_type: str = Form("video")):
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    }
    if format_type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
    else:
        ydl_opts['format'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        return FileResponse(filename, filename=os.path.basename(filename), media_type='application/octet-stream')
    except Exception as e:
        return HTMLResponse(content=f"<h3>Download Failed: {str(e)}</h3><p><a href='/'>Go Back</a></p>")
