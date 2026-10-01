import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.services.gemini_service import create_comic
from app.services.image_service import generate_panel_image

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="ComicCraft AI")

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


class ComicRequest(BaseModel):
    idea: str
    genre: str = "Adventure"
    audience: str = "General"
    panels: int = 6


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.post("/api/generate")
async def generate_comic_api(request: ComicRequest):

    try:
        # Generate the comic story
        result = create_comic(
            idea=request.idea,
            genre=request.genre,
            audience=request.audience,
            number_of_panels=request.panels,
        )

        # Generate an AI image for each comic panel
        image_errors = []

        for panel in result.get("panels", []):

            try:
                image_url = generate_panel_image(
                    scene=panel.get("scene", ""),
                    dialogue=panel.get("dialogue", ""),
                    caption=panel.get("caption", ""),
                    characters=result.get("characters", []),
                )

                panel["image_url"] = image_url

            except Exception as image_error:

                panel["image_url"] = None
                panel["image_error"] = str(image_error)

                image_errors.append(str(image_error))

        result["image_errors"] = image_errors

        return {
            "success": True,
            "data": result
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


@app.get("/health")
async def health():
    return {
        "status": "running",
        "application": "ComicCraft AI"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )