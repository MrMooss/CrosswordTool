from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pathlib import Path
import os
import tempfile
import threading
import uuid

from .crossword import Crossword
from .svg_to_pdf import svg_to_pdf

app = FastAPI()

frontend_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs = {}


@app.get("/health")
def health():
    return {"status": "ok"}

class Job:
    def __init__(self):
        self.percent = 0
        self.message = "Initializing..."
        self.status = "pending"
        self.pdf_path = None
        self.error = None

def generate_pdf(job_id: str, url: str):
    job = jobs[job_id]

    try:
        # 10%
        job.percent = 10
        job.message = "Loading crossword..."

        crossword = Crossword(url)

        # 40%
        job.percent = 40
        job.message = "Processing crossword..."

        svg = crossword.render()

        # 70%
        job.percent = 70
        job.message = "Creating SVG..."

        # Ideiglenes PDF hely
        output_dir = Path(tempfile.gettempdir()) / "crossword_jobs"
        output_dir.mkdir(exist_ok=True)

        pdf_path = output_dir / f"{job_id}.pdf"

        # 85%
        job.percent = 85
        job.message = "Rendering PDF..."

        pdf = svg_to_pdf(svg)

        pdf_path.write_bytes(pdf)

        # 100%
        job.percent = 100
        job.message = "Done!"
        job.status = "finished"
        job.pdf_path = pdf_path

    except Exception as exc:
        job.status = "error"
        job.error = f"{type(exc).__name__}: {exc}"
        job.message = "Error occured."


@app.post("/api/generate")
def generate(url: str):

    job_id = str(uuid.uuid4())

    jobs[job_id] = Job()

    thread = threading.Thread(
        target=generate_pdf,
        args=(job_id, url),
        daemon=True,
    )

    thread.start()

    return {
        "job_id": job_id
    }


@app.get("/api/progress/{job_id}")
def progress(job_id: str):

    job = jobs.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    return {
        "percent": job.percent,
        "message": job.message,
        "status": job.status,
        "error": job.error,
    }


@app.get("/api/download/{job_id}")
def download(job_id: str):

    job = jobs.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    if job.status != "finished":
        raise HTTPException(
            status_code=400,
            detail="The PDF has not been generated yet."
        )

    return FileResponse(
        job.pdf_path,
        media_type="application/pdf",
        filename="crossword.pdf",
    )


frontend_dir = Path(__file__).resolve().parent.parent / "frontend_dist"
if frontend_dir.exists():
    app.mount(
        "/",
        StaticFiles(directory=frontend_dir, html=True),
        name="frontend",
    )