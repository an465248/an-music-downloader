@app.post("/download")
async def download_file(url: str = Form(...), format_type: str = Form("video")):
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'), # File name ko simple ID rakhne se error nahi aayega
    }
    if format_type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
    else:
        ydl_opts['format'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        if os.path.exists(filename):
            return FileResponse(filename, filename=os.path.basename(filename), media_type='application/octet-stream')
        else:
            return HTMLResponse(content="<h3>Error: Downloaded file not found on server!</h3><p><a href='/'>Go Back</a></p>")
            
    except Exception as e:
        return HTMLResponse(content=f"<h3>Download Failed: {str(e)}</h3><p><a href='/'>Go Back</a></p>")
