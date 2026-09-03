from math import sqrt
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from questions import POLITIC_QUESTIONS

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class SurveyResponse(BaseModel):
    results: List[int]


IDEOLOGY_PROFILES = {
    "comunismo": {"economic": 85, "social": 82, "identity": 18},
    "socialismo": {"economic": 72, "social": 68, "identity": 22},
    "socialdemocracia": {"economic": 58, "social": 56, "identity": 26},
    "liberalismo": {"economic": 18, "social": 32, "identity": 16},
    "conservadurismo": {"economic": 6, "social": -38, "identity": 48},
    "neoliberalismo": {"economic": -28, "social": -10, "identity": 36},
    "nacionalismo": {"economic": 12, "social": -18, "identity": 78},
    "libertarismo": {"economic": -70, "social": 72, "identity": 8},
}

PARTY_PROFILES = {
    "pcte": {"economic": 88, "social": 80, "identity": 18},
    "podemos": {"economic": 78, "social": 72, "identity": 26},
    "sumar": {"economic": 68, "social": 64, "identity": 32},
    "psoe": {"economic": 58, "social": 58, "identity": 32},
    "pp": {"economic": 15, "social": -18, "identity": 52},
    "vox": {"economic": -20, "social": -60, "identity": 84},
    "erc": {"economic": 42, "social": 32, "identity": 80},
    "junts": {"economic": 28, "social": 12, "identity": 78},
    "partido libertario": {"economic": -72, "social": 78, "identity": 8},
}


def calculate_profile(responses: List[int]):
    if len(responses) != len(POLITIC_QUESTIONS):
        raise HTTPException(status_code=400, detail=f"Se esperaban {len(POLITIC_QUESTIONS)} respuestas, pero recibiste {len(responses)}.")

    axis_scores = {"economic": 0, "social": 0, "identity": 0}
    axis_cap = {"economic": 0, "social": 0, "identity": 0}

    for answer, question in zip(responses, POLITIC_QUESTIONS):
        if answer < 1 or answer > 10:
            raise HTTPException(status_code=400, detail=f"La respuesta '{answer}' está fuera del rango 1-10.")
        delta = (answer - 5) * 10
        axis_scores[question["axis"]] += delta * question["direction"]
        axis_cap[question["axis"]] += 40

    profile = {}
    for axis in axis_scores:
        if axis_cap[axis] == 0:
            profile[axis] = 0
        else:
            profile[axis] = round((axis_scores[axis] / axis_cap[axis]) * 100)

    def distance(reference):
        return sqrt(
            (profile["economic"] - reference["economic"]) ** 2
            + (profile["social"] - reference["social"]) ** 2
            + (profile["identity"] - reference["identity"]) ** 2
        )

    ranked = sorted(IDEOLOGY_PROFILES.items(), key=lambda item: distance(item[1]))
    profile["closest_ideology"] = ranked[0][0]
    profile["top_matches"] = [name for name, _ in ranked[:3]]
    profile["distance_to_top"] = round(distance(ranked[0][1]), 2)
    return profile


def summarize_profile(profile):
    top = profile["top_matches"]
    if len(top) >= 2:
        first = top[0]
        second = top[1]
        if profile["distance_to_top"] < 45:
            return f"Tu perfil es mixto entre {first} y {second}. No encajas en un único bloque: tienes una mezcla de {first} y {second}."

    if profile["closest_ideology"] == "comunismo":
        return "Tu perfil está muy cerca del comunismo: priorizas mucho la igualdad económica y la intervención del Estado."
    if profile["closest_ideology"] == "socialismo":
        return "Tu perfil se acerca al socialismo: valoras la redistribución, la protección social y una intervención estatal fuerte."
    if profile["closest_ideology"] == "socialdemocracia":
        return "Tu perfil se acerca a la socialdemocracia: buscas equilibrio entre Estado de bienestar, mercado y justicia social."
    if profile["closest_ideology"] == "liberalismo":
        return "Tu perfil se acerca al liberalismo: priorizas la libertad individual y una economía más abierta, aunque con matices sociales."
    if profile["closest_ideology"] == "conservadurismo":
        return "Tu perfil se acerca al conservadurismo: valoras la tradición, la estabilidad y el orden social."
    if profile["closest_ideology"] == "neoliberalismo":
        return "Tu perfil se acerca al neoliberalismo: prefieres un mercado más libre, menos regulación y mayor autonomía individual."
    if profile["closest_ideology"] == "nacionalismo":
        return "Tu perfil se acerca al nacionalismo: das mucha importancia a la identidad nacional, la soberanía y la cultura propia."
    if profile["closest_ideology"] == "libertarismo":
        return "Tu perfil se acerca al libertarismo: valoras muchísimo la libertad individual y la mínima intervención estatal."
    return "Tu perfil combina varios ejes ideológicos y no encaja completamente en una sola etiqueta."


def axis_label(value, left, right):
    if value < -25:
        return right
    if value > 25:
        return left
    return "posición intermedia"


@app.get("/", response_class=HTMLResponse)
async def get_form():
    with open(BASE_DIR / "index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.post("/submit", response_class=HTMLResponse)
async def submit_survey(request: Request, survey_response: SurveyResponse):
    profile = calculate_profile(survey_response.results)
    summary = summarize_profile(profile)

    def close_party(profile_values):
        ranked = sorted(
            PARTY_PROFILES.items(),
            key=lambda item: sqrt(
                (profile_values["economic"] - item[1]["economic"]) ** 2
                + (profile_values["social"] - item[1]["social"]) ** 2
                + (profile_values["identity"] - item[1]["identity"]) ** 2
            ),
        )
        return ranked[0][0]

    closest_party = close_party(profile)
    axis_labels = {
        "economic_label": axis_label(profile["economic"], "más intervención pública", "más libertad de mercado"),
        "social_label": axis_label(profile["social"], "más libertad social", "más orden y tradición"),
        "identity_label": axis_label(profile["identity"], "más pluralidad territorial", "más identidad nacional"),
    }
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "closest_ideology": profile["closest_ideology"].upper(),
            "closest_party": closest_party.upper(),
            "closest_party_photo": closest_party,
            "summary": summary,
            "top_matches": profile["top_matches"],
            "economic": profile["economic"],
            "social": profile["social"],
            "identity": profile["identity"],
            **axis_labels,
        },
    )


@app.get("/result")
async def get_result():
    return {"result": "Success"}
