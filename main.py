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
 <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AnMusic Downloader - 4K Video & HD Audio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --bg: #0f0f1a;
            --card: #1a1a2e;
            --border: #2d2d44;
            --text: #e4e4e7;
            --text-muted: #71717a;
            --accent: #22d3ee;
            --success: #22c55e;
            --error: #ef4444;
        }
        * { box-sizing: border-box; }
        body {
            background: var(--bg);
            color: var(--text);
            font-family: 'Segoe UI', system-ui, sans-serif;
            min-height: 100vh;
            background-image: 
                radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.15), transparent),
                radial-gradient(circle at 20% 80%, rgba(34, 211, 238, 0.08), transparent);
        }
        .navbar { background: rgba(26, 26, 46, 0.9) !important; backdrop-filter: blur(20px); border-bottom: 1px solid var(--border); }
        .brand-text { background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; }
        .hero { padding: 4rem 0; }
        .hero h1 { font-size: clamp(2.5rem, 6vw, 4rem); font-weight: 800; line-height: 1.1; margin-bottom: 1rem; }
        .hero .highlight { background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .hero p { color: var(--text-muted); font-size: 1.25rem; max-width: 600px; }
        .card-custom { background: var(--card); border: 1px solid var(--border); border-radius: 16px; transition: all 0.3s ease; }
        .card-custom:hover { border-color: var(--primary); box-shadow: 0 20px 40px rgba(99, 102, 241, 0.1); transform: translateY(-2px); }
        .input-group-custom { position: relative; }
        .input-group-custom .form-control {
            background: var(--bg); border: 1px solid var(--border); color: var(--text);
            padding: 1rem 1rem 1rem 3rem; border-radius: 12px; font-size: 1rem;
            transition: all 0.3s ease;
        }
        .input-group-custom .form-control:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2); outline: none; }
        .input-group-custom .form-control::placeholder { color: var(--text-muted); }
        .input-group-custom .input-icon { position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); font-size: 1.25rem; pointer-events: none; }
        .btn-primary-custom {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            border: none; padding: 1rem 2rem; border-radius: 12px; font-weight: 600;
            font-size: 1rem; transition: all 0.3s ease;
        }
        .btn-primary-custom:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4); }
        .btn-primary-custom:disabled { opacity: 0.6; transform: none; }
        .option-card { background: var(--bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; cursor: pointer; transition: all 0.2s ease; }
        .option-card:hover, .option-card.selected { border-color: var(--primary); background: rgba(99, 102, 241, 0.05); }
        .option-card input { display: none; }
        .option-card .icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin-bottom: 0.75rem; }
        .option-card.video .icon { background: linear-gradient(135deg, var(--primary), #8b5cf6); color: white; }
        .option-card.audio .icon { background: linear-gradient(135deg, var(--accent), #06b6d4); color: var(--bg); }
        .quality-badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; margin-right: 0.5rem; margin-bottom: 0.5rem; cursor: pointer; transition: all 0.2s; }
        .quality-badge.video { background: rgba(99, 102, 241, 0.2); color: var(--primary); }
        .quality-badge.audio { background: rgba(34, 211, 238, 0.2); color: var(--accent); }
        .quality-badge:hover { transform: scale(1.05); }
        .quality-badge.selected { background: var(--primary) !important; color: white !important; }
        .quality-badge.audio.selected { background: var(--accent) !important; color: var(--bg) !important; }
        .quality-badge.disabled { opacity: 0.4; pointer-events: none; }
        .quality-container { min-height: 60px; }
        .quality-label { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem; display: block; }
        .progress-wrapper { display: none; }
        .progress-wrapper.active { display: block; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        .progress-custom { height: 8px; border-radius: 4px; background: var(--bg); overflow: hidden; }
        .progress-bar-custom { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--primary), var(--accent)); transition: width 0.3s ease; position: relative; }
        .progress-bar-custom::after { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); animation: shimmer 1.5s infinite; }
        @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
        .status-text { font-size: 0.875rem; color: var(--text-muted); margin-top: 0.5rem; }
        .status-text.success { color: var(--success); }
        .status-text.error { color: var(--error); }
        .video-preview { display: none; }
        .video-preview.active { display: block; animation: fadeIn 0.3s ease; }
        .video-preview img { border-radius: 12px; width: 100%; max-height: 200px; object-fit: cover; }
        .video-preview h5 { margin-top: 0.75rem; font-weight: 600; }
        .video-preview .meta { color: var(--text-muted); font-size: 0.875rem; }
        .download-btn { display: none; width: 100%; }
        .download-btn.active { display: block; animation: fadeIn 0.3s ease; }
        .footer { border-top: 1px solid var(--border); padding: 2rem 0; color: var(--text-muted); }
        .supported-sites { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem; }
        .site-badge { background: var(--bg); border: 1px solid var(--border); padding: 0.35rem 0.75rem; border-radius: 20px; font-size: 0.75rem; color: var(--text-muted); transition: all 0.2s; }
        .site-badge:hover { border-color: var(--primary); color: var(--primary); }
        .toast-container { position: fixed; top: 1.5rem; right: 1.5rem; z-index: 9999; }
        .toast-custom { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem 1.5rem; box-shadow: 0 10px 40px rgba(0,0,0,0.3); animation: slideIn 0.3s ease; }
        @keyframes slideIn { from { opacity: 0; transform: translateX(100%); } to { opacity: 1; transform: translateX(0); } }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @media (max-width: 576px) { .hero { padding: 2.5rem 0; } .option-card { padding: 1rem; } }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark px-4 px-md-5 py-3">
        <div class="container-fluid">
            <a class="navbar-brand d-flex align-items-center gap-2" href="#">
                <i class="bi bi-music-note-beamed" style="font-size: 1.75rem;"></i>
                <span class="brand-text fs-4">AnMusic Downloader</span>
            </a>
        </div>
    </nav>

    <main class="px-4 px-md-5 py-5">
        <div class="container">
            <section class="hero text-center mx-auto" style="max-width: 800px;">
                <h1>Download <span class="highlight">4K Videos</span> & <span class="highlight">HD Audio</span></h1>
                <p class="mx-auto">From YouTube, YouTube Music, Instagram, TikTok, Twitter, Vimeo, and 1000+ sites</p>
            </section>

            <div class="row justify-content-center">
                <div class="col-12 col-lg-10 col-xl-8">
                    <div class="card-custom p-4 p-md-5 mb-4">
                        <div class="input-group-custom mb-4">
                            <i class="bi bi-link-45deg input-icon"></i>
                            <input type="url" class="form-control" id="urlInput" placeholder="Paste video/music URL here (YouTube, YouTube Music, Instagram, TikTok, etc.)" autocomplete="off">
                        </div>

                        <div class="mb-4">
                            <label class="form-label fw-semibold mb-3">Download Type</label>
                            <div class="d-flex gap-3 flex-wrap">
                                <label class="option-card video selected flex-1 text-center" data-type="video" onclick="selectType('video')">
                                    <input type="radio" name="formatType" value="video" checked>
                                    <div class="icon"><i class="bi bi-play-circle-fill"></i></div>
                                    <strong>Video</strong>
                                    <div class="quality-container" id="videoQualities">
                                        <span class="quality-label">Loading qualities...</span>
                                    </div>
                                </label>
                                <label class="option-card audio flex-1 text-center" data-type="audio" onclick="selectType('audio')">
                                    <input type="radio" name="formatType" value="audio">
                                    <div class="icon"><i class="bi bi-music-note-beamed"></i></div>
                                    <strong>Audio (MP3)</strong>
                                    <div class="quality-container" id="audioQualities">
                                        <span class="quality-label">Loading qualities...</span>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <button class="btn btn-primary-custom w-100 btn-lg" id="downloadBtn" onclick="startDownload()" disabled>
                            <span id="btnText"><i class="bi bi-cloud-arrow-down-fill me-2"></i>Start Download</span>
                            <span id="btnLoading" class="d-none"><i class="bi bi-arrow-clockwise spin me-2"></i>Processing...</span>
                        </button>
                    </div>

                    <div class="progress-wrapper card-custom p-4" id="progressWrapper">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="fw-medium" id="progressTitle">Preparing download...</span>
                            <span class="fw-bold text-primary" id="progressPercent">0%</span>
                        </div>
                        <div class="progress-custom">
                            <div class="progress-bar-custom" id="progressBar" style="width: 0%"></div>
                        </div>
                        <div class="status-text" id="statusText">Initializing...</div>
                    </div>

                    <div class="video-preview card-custom p-4 mt-3" id="videoPreview">
                        <img id="previewThumb" src="" alt="Video thumbnail">
                        <h5 id="previewTitle"></h5>
                        <div class="meta" id="previewMeta"></div>
                    </div>

                    <button class="btn btn-success w-100 btn-lg mt-3 download-btn" id="downloadFileBtn" onclick="downloadFile()">
                        <i class="bi bi-download me-2"></i>Download File
                    </button>
                </div>
            </div>

            <footer class="footer mt-5">
                <div class="container text-center">
                    <p class="mb-2">AnMusic Downloader • Supports 1000+ sites via yt-dlp</p>
                    <div class="supported-sites justify-content-center">
                        <span class="site-badge"><i class="bi bi-youtube me-1"></i>YouTube</span>
                        <span class="site-badge"><i class="bi bi-music-note me-1"></i>YouTube Music</span>
                        <span class="site-badge"><i class="bi bi-instagram me-1"></i>Instagram</span>
                        <span class="site-badge"><i class="bi bi-tiktok me-1"></i>TikTok</span>
                        <span class="site-badge"><i class="bi bi-twitter-x me-1"></i>Twitter/X</span>
                        <span class="site-badge"><i class="bi bi-vimeo me-1"></i>Vimeo</span>
                        <span class="site-badge"><i class="bi bi-facebook me-1"></i>Facebook</span>
                        <span class="site-badge"><i class="bi bi-twitch me-1"></i>Twitch</span>
                        <span class="site-badge"><i class="bi bi-soundcloud me-1"></i>SoundCloud</span>
                        <span class="site-badge"><i class="bi bi-reddit me-1"></i>Reddit</span>
                        <span class="site-badge"><i class="bi bi-generic me-1"></i>1000+ more</span>
                    </div>
                </div>
            </footer>
        </div>
    </main>

    <div class="toast-container" id="toastContainer"></div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentDownloadId = null;
        let selectedFormat = 'video';
        let selectedQuality = 'best';
        let statusPollInterval = null;
        let availableVideoQualities = [];
        let availableAudioQualities = [];

        const urlInput = document.getElementById('urlInput');
        const downloadBtn = document.getElementById('downloadBtn');
        const progressWrapper = document.getElementById('progressWrapper');
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        const statusText = document.getElementById('statusText');
        const progressTitle = document.getElementById('progressTitle');
        const videoPreview = document.getElementById('videoPreview');
        const previewThumb = document.getElementById('previewThumb');
        const previewTitle = document.getElementById('previewTitle');
        const previewMeta = document.getElementById('previewMeta');
        const downloadFileBtn = document.getElementById('downloadFileBtn');
        const btnText = document.getElementById('btnText');
        const btnLoading = document.getElementById('btnLoading');
        const videoQualitiesContainer = document.getElementById('videoQualities');
        const audioQualitiesContainer = document.getElementById('audioQualities');

        urlInput.addEventListener('input', debounce(async () => {
            const url = urlInput.value.trim();
            downloadBtn.disabled = !isValidUrl(url);
            
            if (isValidUrl(url)) {
                await fetchVideoInfo(url);
            } else {
                hidePreview();
                resetQualities();
            }
        }, 500));

        function isValidUrl(string) {
            try {
                new URL(string);
                return true;
            } catch (_) {
                return false;
            }
        }

        async function fetchVideoInfo(url) {
            try {
                const res = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
                if (!res.ok) return;
                const data = await res.json();
                showPreview(data);
                renderQualities(data);
            } catch (e) {
                console.log('Info fetch failed:', e);
            }
        }

        function renderQualities(data) {
            availableVideoQualities = data.video_qualities || [];
            availableAudioQualities = data.audio_qualities || [];

            renderVideoQualities();
            renderAudioQualities();
        }

        function renderVideoQualities() {
            if (availableVideoQualities.length === 0) {
                videoQualitiesContainer.innerHTML = '<span class="quality-label">No video qualities available</span>';
                return;
            }

            const badges = availableVideoQualities.map(q => 
                `<span class="quality-badge video" data-quality="${q.height}" onclick="event.stopPropagation(); selectQuality('${q.height}')">${q.label}</span>`
            ).join('');

            videoQualitiesContainer.innerHTML = `<span class="quality-label">${availableVideoQualities.length} qualities available</span>${badges}`;
            
            if (selectedFormat === 'video') {
                const firstQuality = availableVideoQualities[0];
                if (firstQuality && !availableVideoQualities.some(q => q.height.toString() === selectedQuality)) {
                    selectQuality(firstQuality.height.toString());
                }
            }
        }

        function renderAudioQualities() {
            if (availableAudioQualities.length === 0) {
                audioQualitiesContainer.innerHTML = '<span class="quality-label">No audio qualities available</span>';
                return;
            }

            const badges = availableAudioQualities.map(q => 
                `<span class="quality-badge audio" data-quality="${q.abr}" onclick="event.stopPropagation(); selectQuality('${q.abr}')">${q.label}</span>`
            ).join('');

            audioQualitiesContainer.innerHTML = `<span class="quality-label">${availableAudioQualities.length} qualities available</span>${badges}`;
            
            if (selectedFormat === 'audio') {
                const firstQuality = availableAudioQualities[0];
                if (firstQuality && !availableAudioQualities.some(q => q.abr.toString() === selectedQuality)) {
                    selectQuality(firstQuality.abr.toString());
                }
            }
        }

        function resetQualities() {
            videoQualitiesContainer.innerHTML = '<span class="quality-label">Enter URL to load qualities</span>';
            audioQualitiesContainer.innerHTML = '<span class="quality-label">Enter URL to load qualities</span>';
            availableVideoQualities = [];
            availableAudioQualities = [];
        }

        function showPreview(data) {
            if (data.thumbnail) previewThumb.src = data.thumbnail;
            previewTitle.textContent = data.title || 'Unknown Title';
            
            const duration = data.duration ? formatDuration(data.duration) : 'Unknown duration';
            const uploader = data.uploader || 'Unknown uploader';
            previewMeta.innerHTML = `<i class="bi bi-clock me-1"></i>${duration} • <i class="bi bi-person me-1"></i>${uploader}`;
            
            videoPreview.classList.add('active');
        }

        function hidePreview() {
            videoPreview.classList.remove('active');
        }

        function formatDuration(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            return h > 0 ? `${h}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}` : `${m}:${s.toString().padStart(2,'0')}`;
        }

        function selectType(type) {
            selectedFormat = type;
            document.querySelectorAll('.option-card').forEach(card => {
                card.classList.toggle('selected', card.dataset.type === type);
                card.querySelector('input').checked = card.dataset.type === type;
            });
            
            updateQualityBadges(type);
        }

        function updateQualityBadges(type) {
            document.querySelectorAll('.quality-badge').forEach(badge => {
                badge.classList.toggle('disabled', false);
                if ((type === 'video' && badge.classList.contains('video')) || 
                    (type === 'audio' && badge.classList.contains('audio'))) {
                    badge.style.opacity = '1';
                    badge.style.pointerEvents = 'auto';
                } else {
                    badge.style.opacity = '0.4';
                    badge.style.pointerEvents = 'none';
                    badge.classList.add('disabled');
                }
            });

            if (type === 'video' && availableVideoQualities.length > 0) {
                const firstQuality = availableVideoQualities[0];
                if (firstQuality && !availableVideoQualities.some(q => q.height.toString() === selectedQuality)) {
                    selectQuality(firstQuality.height.toString());
                }
            } else if (type === 'audio' && availableAudioQualities.length > 0) {
                const firstQuality = availableAudioQualities[0];
                if (firstQuality && !availableAudioQualities.some(q => q.abr.toString() === selectedQuality)) {
                    selectQuality(firstQuality.abr.toString());
                }
            }
        }

        function selectQuality(quality) {
            selectedQuality = quality;
            document.querySelectorAll('.quality-badge').forEach(badge => {
                badge.classList.toggle('selected', badge.dataset.quality === quality);
            });
        }

        async function startDownload() {
            const url = urlInput.value.trim();
            if (!isValidUrl(url)) return showToast('Please enter a valid URL', 'error');

            downloadBtn.disabled = true;
            btnText.classList.add('d-none');
            btnLoading.classList.remove('d-none');
            hidePreview();
            downloadFileBtn.classList.remove('active');
            progressWrapper.classList.add('active');
            progressTitle.textContent = 'Starting download...';
            statusText.textContent = 'Connecting to server...';
            progressBar.style.width = '0%';
            progressPercent.textContent = '0%';
            statusText.className = 'status-text';

            try {
                const formData = new FormData();
                formData.append('url', url);
                formData.append('format_type', selectedFormat);
                formData.append('quality', selectedQuality);

                const res = await fetch('/api/download', {
                    method: 'POST',
                    body: formData
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Download failed');

                currentDownloadId = data.download_id;
                startStatusPolling();
            } catch (err) {
                showToast(err.message, 'error');
                resetDownloadButton();
                progressWrapper.classList.remove('active');
            }
        }

        function startStatusPolling() {
            statusPollInterval = setInterval(async () => {
                if (!currentDownloadId) return;
                
                try {
                    const res = await fetch(`/api/status/${currentDownloadId}`);
                    const data = await res.json();

                    progressBar.style.width = `${data.progress}%`;
                    progressPercent.textContent = `${data.progress}%`;

                    if (data.status === 'downloading') {
                        statusText.textContent = `Downloading... ${data.progress}%`;
                    } else if (data.status === 'completed') {
                        statusText.textContent = 'Download complete! Preparing file...';
                        statusText.className = 'status-text success';
                        progressTitle.textContent = 'Ready to download';
                        clearInterval(statusPollInterval);
                        downloadFileBtn.classList.add('active');
                        resetDownloadButton();
                    } else if (data.status === 'failed') {
                        statusText.textContent = `Failed: ${data.error || 'Unknown error'}`;
                        statusText.className = 'status-text error';
                        clearInterval(statusPollInterval);
                        showToast(data.error || 'Download failed', 'error');
                        resetDownloadButton();
                    }
                } catch (e) {
                    console.error('Status poll error:', e);
                }
            }, 1000);
        }

        async function downloadFile() {
            if (!currentDownloadId) return;
            
            try {
                const res = await fetch(`/api/download-file/${currentDownloadId}`);
                if (!res.ok) throw new Error('Download failed');
                
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = '';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                showToast('Download started!', 'success');
            } catch (err) {
                showToast(err.message, 'error');
            }
        }

        function resetDownloadButton() {
            downloadBtn.disabled = false;
            btnText.classList.remove('d-none');
            btnLoading.classList.add('d-none');
        }

        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast-custom';
            toast.innerHTML = `
                <div class="d-flex align-items-center gap-2">
                    <i class="bi ${type === 'success' ? 'bi-check-circle-fill text-success' : type === 'error' ? 'bi-x-circle-fill text-danger' : 'bi-info-circle-fill text-primary'}"></i>
                    <span>${message}</span>
                </div>
            `;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 4000);
        }

        function debounce(fn, delay) {
            let timeoutId;
            return (...args) => {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => fn.apply(this, args), delay);
            };
        }
    </script>
</body>
</html>
