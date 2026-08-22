from fastapi import FastAPI, Request, Form
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

@app.post("/download")
async def download_file(url: str = Form(...), format_type: str = Form("video")):
    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False) # Server par download nahi karenge, direct stream/download link nikalenge
            download_url = info.get('url')
            
            if download_url:
                # Seedhe YouTube ki direct media file par redirect kar denge
                return RedirectResponse(url=download_url, status_code=303)
            else:
                return HTMLResponse(content="<h3>Could not fetch download link. Try another video!</h3><p><a href='/'>Go Back</a></p>")
                
    except Exception as e:
        return HTMLResponse(content=f"<h3>Error: {str(e)}</h3><p><a href='/'>Go Back</a></p>")
