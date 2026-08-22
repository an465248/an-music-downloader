from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>AnMusic Downloader</title>
    </head>
    <body style="font-family: Arial; text-align: center; margin-top: 50px;">
        <h1>AnMusic Downloader is Live!</h1>
        <p>App successfully running on Render.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
