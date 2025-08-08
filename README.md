# OpenCaption Studio (OSS)

An open‑source online video editor focused on viral‑style captions. It combines auto‑transcription (Whisper), trendy animated captions (ASS/libass via FFmpeg), and a simple web editor UI.

## Highlights
- Auto transcription with word‑level timings (Whisper)
- Viral caption styles (Hormozi Bold, MrBeast Pop, Clean Pro)
- Burn‑in animated captions to MP4 (FFmpeg + libass karaoke tags)
- Download SRT
- Minimal editor to tweak text before render
- 100% open‑source stack to minimize cost

## Tech Stack
- Backend: FastAPI, Whisper (openai‑whisper), PyTorch, ffmpeg‑python
- Media: FFmpeg (libass)
- Frontend: Next.js (App Router) + React + TypeScript + Tailwind CSS

## Requirements
- FFmpeg (with libass)
- Python 3.10+ (tested on 3.13)
- Node.js 18+ (18/20/22 OK)
- Linux/macOS (Windows WSL works)

Ubuntu/Debian FFmpeg:
```bash
sudo apt-get update -y && sudo apt-get install -y ffmpeg
```

## Quick Start

1) Backend (FastAPI + Whisper)
```bash
cd app/backend
python3 -m venv ../../venv
source ../../venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
- Health check: `curl http://127.0.0.1:8000/health`
- The server writes temp data to `app/backend/data/` (ignored by git):
  - `media/` uploaded videos
  - `captions/` generated `.srt/.json/.ass`
  - `renders/` exported MP4s

2) Frontend (Next.js UI)
```bash
cd app/frontend
npm install
# Point UI to backend (adjust if backend runs elsewhere):
export NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
npm run dev
```
Open http://localhost:3000

## Usage Flow
1. Upload a video (MP4 recommended)
2. Click “Upload & Transcribe”
3. Select a caption style
4. Optionally tweak captions in the editor
5. Render burn‑in MP4 or download SRT

## API (brief)
- GET `/health` → `{ status: "ok" }`
- GET `/styles` → `{ styles: [...] }`
- POST `/upload` (multipart `file`) → `{ media_id, path }`
- POST `/transcribe/{media_id}` (form `language?`) → transcript JSON + writes `SRT`
- POST `/render` (JSON `{ media_id, style_id, resolution?, srt_only? }`) → file response (MP4 or SRT)

Notes:
- Whisper model defaults to `small` (CPU‑friendly). Change in `get_model()` to `base`/`medium`/`large-v3` if you have GPU.
- Karaoke effect uses ASS `\k` timing per word when available.

## Fonts & Styles
- A sample font `Anton-Regular.ttf` is included at `app/backend/fonts/`.
- libass resolves fonts via system fontconfig. To use custom fonts:
  - Drop TTF/OTF files in `app/backend/fonts/`
  - Run `fc-cache -fv` (on the host) so FFmpeg/libass can find them
- Update style presets in `app/backend/main.py` (`VIRAL_STYLES`).

## Configuration
- Frontend: `NEXT_PUBLIC_API_BASE` (e.g. `http://127.0.0.1:8000`)
- Backend directories auto‑created under `app/backend/data/`

## Development Tips
- Keep videos short for quick iteration
- For higher quality, render with larger Whisper model (GPU recommended)
- If FFmpeg cannot find fonts, set explicit `ass` font fallback via style or install fonts system‑wide

## Known Limitations (MVP)
- Caption edits are local in the UI; not persisted back to backend JSON
- No timeline or per‑word color rules yet
- No reframing/auto layouts (can be added via OpenCV/mediapipe)

## Roadmap (next)
- Persist edited captions to backend & re‑render
- Emoji/emphasis word coloring
- Template/brand kits & custom font uploads via UI
- Reframe (9:16 / 1:1 / 16:9) and subject tracking
- Translation/dubbing via OSS models

## License
See `LICENSE`.