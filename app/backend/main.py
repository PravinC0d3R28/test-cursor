from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
import asyncio
import shutil
from typing import List, Optional

import whisper
import srt as srt_mod
from datetime import timedelta
import subprocess
import json

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_ROOT, "data")
MEDIA_DIR = os.path.join(DATA_DIR, "media")
CAPTION_DIR = os.path.join(DATA_DIR, "captions")
RENDERS_DIR = os.path.join(DATA_DIR, "renders")
FONTS_DIR = os.path.join(APP_ROOT, "fonts")

for d in [DATA_DIR, MEDIA_DIR, CAPTION_DIR, RENDERS_DIR, FONTS_DIR]:
    os.makedirs(d, exist_ok=True)

app = FastAPI(title="OpenCaption Studio API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy load model at first request to save cold start
_model = None

def get_model():
    global _model
    if _model is None:
        # small or base for CPU; switch to large-v3 for high quality
        _model = whisper.load_model("small")
    return _model

class Word(BaseModel):
    start: float
    end: float
    text: str

class Segment(BaseModel):
    start: float
    end: float
    text: str
    words: Optional[List[Word]] = None

class Transcript(BaseModel):
    language: str
    segments: List[Segment]

class RenderRequest(BaseModel):
    media_id: str
    style_id: str
    resolution: Optional[str] = None  # e.g., "1080x1920"
    burn_in: bool = True
    srt_only: bool = False

VIRAL_STYLES = [
    {
        "id": "hormozi-bold",
        "label": "Hormozi Bold",
        "font": "Anton",
        "primary_color": "#FFFFFF",
        "emphasis_color": "#FFD60A",
        "stroke_color": "#000000",
        "stroke_width": 2,
        "background_opacity": 0.0,
        "karaoke": True,
        "uppercase": True,
    },
    {
        "id": "mrbeast-pop",
        "label": "MrBeast Pop",
        "font": "Montserrat ExtraBold",
        "primary_color": "#FFFFFF",
        "emphasis_color": "#00E5FF",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "background_opacity": 0.15,
        "karaoke": True,
        "uppercase": False,
    },
    {
        "id": "clean-pro",
        "label": "Clean Pro",
        "font": "Inter SemiBold",
        "primary_color": "#FFFFFF",
        "emphasis_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 1,
        "background_opacity": 0.0,
        "karaoke": False,
        "uppercase": False,
    },
]

@app.get("/styles")
async def list_styles():
    return {"styles": VIRAL_STYLES}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    media_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    dest_path = os.path.join(MEDIA_DIR, f"{media_id}{ext}")
    with open(dest_path, "wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"media_id": media_id, "path": dest_path}

@app.post("/transcribe/{media_id}")
async def transcribe(media_id: str, language: Optional[str] = Form(default=None)):
    # locate media
    media_path = None
    for name in os.listdir(MEDIA_DIR):
        if name.startswith(media_id):
            media_path = os.path.join(MEDIA_DIR, name)
            break
    if not media_path:
        return JSONResponse(status_code=404, content={"error": "media not found"})

    model = get_model()
    result = await asyncio.to_thread(model.transcribe, media_path, language=language, word_timestamps=True)

    segments: List[Segment] = []
    for seg in result.get("segments", []):
        words = None
        if "words" in seg and seg["words"]:
            words = [Word(start=w["start"], end=w["end"], text=w["word"]) for w in seg["words"]]
        segments.append(
            Segment(
                start=float(seg["start"]),
                end=float(seg["end"]),
                text=seg["text"].strip(),
                words=words,
            )
        )

    transcript = Transcript(language=result.get("language", ""), segments=segments)

    # also persist SRT
    srt_path = os.path.join(CAPTION_DIR, f"{media_id}.srt")
    subs = []
    for idx, s in enumerate(transcript.segments, start=1):
        subs.append(
            srt_mod.Subtitle(
                index=idx,
                start=timedelta(seconds=s.start),
                end=timedelta(seconds=s.end),
                content=s.text,
            )
        )
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_mod.compose(subs))

    # also write a JSON with word timings
    json_path = os.path.join(CAPTION_DIR, f"{media_id}.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        jf.write(transcript.model_dump_json(indent=2))

    return {"media_id": media_id, "srt": srt_path, "json": json_path, "transcript": transcript.model_dump()} 


def build_ass_from_transcript(transcript: Transcript, style: dict, ass_path: str, video_w: int = 1080, video_h: int = 1920):
    # Create a simple ASS script with karaoke effect if word timings exist
    font = style.get("font", "Inter")
    primary = style.get("primary_color", "#FFFFFF")
    stroke = style.get("stroke_color", "#000000")
    stroke_w = style.get("stroke_width", 2)
    uppercase = style.get("uppercase", False)
    karaoke = style.get("karaoke", True)

    def hex_to_ass(color_hex: str) -> str:
        hexv = color_hex.lstrip('#')
        if len(hexv) == 6:
            bgr = hexv[4:6] + hexv[2:4] + hexv[0:2]
        else:
            bgr = 'FFFFFF'
        return f"&H00{bgr.upper()}&"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("[Script Info]\n")
        f.write(f"PlayResX: {video_w}\n")
        f.write(f"PlayResY: {video_h}\n")
        f.write("WrapStyle: 2\nScaledBorderAndShadow: yes\n\n")
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write(
            "Style: Default,{font},64,{p},{p},{out},{out},-1,0,0,0,100,100,0,0,1,{outline},0,2,50,50,120,1\n".format(
                font=font,
                p=hex_to_ass(primary),
                out=hex_to_ass(stroke),
                outline=stroke_w,
            )
        )
        f.write("\n[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for seg in transcript.segments:
            text = seg.text.upper() if uppercase else seg.text
            start = str(timedelta(seconds=seg.start))[:-3]
            end = str(timedelta(seconds=seg.end))[:-3]
            if karaoke and seg.words:
                # build karaoke k tags based on word durations in centiseconds
                k_parts = []
                for w in seg.words:
                    dur_cs = int(round((w.end - w.start) * 100))
                    wtext = w.text.upper() if uppercase else w.text
                    k_parts.append(f"{{\\k{dur_cs}}}{wtext}")
                line = "".join(k_parts)
            else:
                line = text
            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{line}\n")

@app.post("/render")
async def render(req: RenderRequest):
    # load transcript
    json_path = os.path.join(CAPTION_DIR, f"{req.media_id}.json")
    if not os.path.exists(json_path):
        return JSONResponse(status_code=404, content={"error": "transcript json not found"})
    with open(json_path, "r", encoding="utf-8") as jf:
        t_data = json.load(jf)
    transcript = Transcript.model_validate(t_data)

    # find media path
    media_path = None
    for name in os.listdir(MEDIA_DIR):
        if name.startswith(req.media_id):
            media_path = os.path.join(MEDIA_DIR, name)
            break
    if not media_path:
        return JSONResponse(status_code=404, content={"error": "media not found"})

    # style
    style = next((s for s in VIRAL_STYLES if s["id"] == req.style_id), VIRAL_STYLES[0])

    if req.srt_only:
        srt_path = os.path.join(CAPTION_DIR, f"{req.media_id}.srt")
        if not os.path.exists(srt_path):
            # write SRT now
            subs = []
            for idx, s in enumerate(transcript.segments, start=1):
                subs.append(
                    srt_mod.Subtitle(
                        index=idx,
                        start=timedelta(seconds=s.start),
                        end=timedelta(seconds=s.end),
                        content=s.text,
                    )
                )
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_mod.compose(subs))
        return FileResponse(srt_path, filename=f"{req.media_id}.srt")

    # Build ASS
    ass_path = os.path.join(CAPTION_DIR, f"{req.media_id}.ass")
    build_ass_from_transcript(transcript, style, ass_path)

    # Render with ffmpeg burn-in using libass
    out_path = os.path.join(RENDERS_DIR, f"{req.media_id}_{style['id']}.mp4")
    vf_filters = [f"ass='{ass_path}'"]
    if req.resolution:
        vf_filters.insert(0, f"scale={req.resolution}")
    vf = ",".join(vf_filters)

    cmd = [
        "ffmpeg", "-y", "-i", media_path,
        "-vf", vf,
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-c:a", "copy",
        out_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": "render failed", "detail": e.stderr.decode(errors='ignore')})

    return FileResponse(out_path, filename=os.path.basename(out_path))

@app.get("/health")
async def health():
    return {"status": "ok"}