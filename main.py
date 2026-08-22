import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import yt_dlp
from pydantic import BaseModel

app = FastAPI(title="AnMusic Downloader", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

active_downloads = {}


class DownloadRequest(BaseModel):
    url: str
    format_type: str = "video"  # video, audio
    quality: str = "best"  # best, 4k, 1080p, 720p, audio_only


def get_ydl_opts(format_type: str, quality: str, output_path: str):
    """Configure yt-dlp options based on format and quality."""
    base_opts = {
        'outtmpl': output_path,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    if format_type == "audio":
        base_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        })
    else:
        if quality == "4k":
            base_opts['format'] = 'bestvideo[height<=2160]+bestaudio/best[height<=2160]'
        elif quality == "1080p":
            base_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif quality == "720p":
            base_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        else:
            base_opts['format'] = 'bestvideo+bestaudio/best'
        
        base_opts['merge_output_format'] = 'mp4'
    
    return base_opts


async def download_video(download_id: str, url: str, format_type: str, quality: str):
    """Background task to download video."""
    try:
        active_downloads[download_id] = {"status": "downloading", "progress": 0, "filename": None}
        
        output_template = str(DOWNLOAD_DIR / f"{download_id}_%(title)s.%(ext)s")
        ydl_opts = get_ydl_opts(format_type, quality, output_template)
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    active_downloads[download_id]["progress"] = int((downloaded / total) * 100)
            elif d['status'] == 'finished':
                active_downloads[download_id]["progress"] = 100
                fname = d.get('filename')
                if fname:
                    active_downloads[download_id]["filename"] = Path(fname).name
        
        ydl_opts['progress_hooks'] = [progress_hook]
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: _download_sync(url, ydl_opts))
        
        files = list(DOWNLOAD_DIR.glob(f"{download_id}_*"))
        if files:
            active_downloads[download_id]["status"] = "completed"
            active_downloads[download_id]["progress"] = 100
            active_downloads[download_id]["filename"] = files[0].name
        else:
            active_downloads[download_id]["status"] = "failed"
            active_downloads[download_id]["error"] = "File not found after download"
            
    except Exception as e:
        active_downloads[download_id] = {"status": "failed", "error": str(e)}


def _download_sync(url: str, ydl_opts: dict):
    """Synchronous download function."""
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    from fastapi.responses import HTMLResponse
import os

@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.post("/api/download")
async def start_download(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    format_type: str = Form("video"),
    quality: str = Form("best")
):
    download_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(download_video, download_id, url, format_type, quality)
    return {"download_id": download_id, "status": "started"}


@app.get("/api/status/{download_id}")
async def get_status(download_id: str):
    if download_id not in active_downloads:
        raise HTTPException(status_code=404, detail="Download not found")
    return active_downloads[download_id]


@app.get("/api/download-file/{download_id}")
async def download_file(download_id: str):
    if download_id not in active_downloads:
        raise HTTPException(status_code=404, detail="Download not found")
    
    download = active_downloads[download_id]
    if download.get("status") != "completed" or not download.get("filename"):
        raise HTTPException(status_code=400, detail="Download not ready")
    
    file_path = DOWNLOAD_DIR / download["filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=download["filename"],
        media_type='application/octet-stream'
    )


def extract_video_qualities(formats):
    """Extract unique video qualities from formats."""
    qualities = {}
    for f in formats:
        height = f.get('height') or (f.get('resolution', '').split('x')[-1] if 'x' in str(f.get('resolution', '')) else None)
        if height and f.get('vcodec') != 'none':
            try:
                h = int(height)
                if h not in qualities:
                    qualities[h] = {
                        'height': h,
                        'label': f'{h}p',
                        'ext': f.get('ext', 'mp4'),
                        'vcodec': f.get('vcodec'),
                        'filesize': f.get('filesize'),
                    }
            except:
                pass
    return sorted(qualities.values(), key=lambda x: x['height'], reverse=True)


def extract_audio_qualities(formats):
    """Extract audio qualities from formats."""
    qualities = {}
    for f in formats:
        if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
            abr = f.get('abr') or f.get('tbr')
            if abr:
                try:
                    q = int(float(abr))
                    if q not in qualities:
                        qualities[q] = {
                            'abr': q,
                            'label': f'{q} kbps',
                            'ext': f.get('ext', 'mp3'),
                            'acodec': f.get('acodec'),
                            'filesize': f.get('filesize'),
                        }
                except:
                    pass
    return sorted(qualities.values(), key=lambda x: x['abr'], reverse=True)


@app.get("/api/info")
async def get_video_info(url: str):
    """Get video info without downloading."""
    try:
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True, 
            'extract_flat': False,
            'format': 'bestvideo+bestaudio/best',
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_qualities = extract_video_qualities(info.get("formats", []))
            audio_qualities = extract_audio_qualities(info.get("formats", []))
            
            return {
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "uploader": info.get("uploader"),
                "video_qualities": video_qualities,
                "audio_qualities": audio_qualities,
                "formats": [
                    {
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "resolution": f.get("resolution"),
                        "filesize": f.get("filesize"),
                        "vcodec": f.get("vcodec"),
                        "acodec": f.get("acodec"),
                        "height": f.get("height"),
                        "abr": f.get("abr"),
                    }
                    for f in info.get("formats", [])
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
