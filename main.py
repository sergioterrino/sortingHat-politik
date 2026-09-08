from math import sqrt
import json
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from party_data import PARTIES, PARTY_POSITIONS
from questions import POLITIC_QUESTIONS

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class SurveyResponse(BaseModel):
    results: List[int]
    importance: List[int] = Field(default_factory=list)
    territory: str = "todos"


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


def validate_responses(responses: List[int], importance: List[int]):
    if len(responses) != len(POLITIC_QUESTIONS):
        raise HTTPException(status_code=400, detail=f"Se esperaban {len(POLITIC_QUESTIONS)} respuestas, pero recibiste {len(responses)}.")
    if importance and len(importance) != len(responses):
        raise HTTPException(status_code=400, detail="La importancia debe tener una valoración por cada respuesta.")
    for answer in responses:
        if answer < 1 or answer > 5:
            raise HTTPException(status_code=400, detail="Las respuestas deben estar entre 1 y 5.")
    for value in importance:
        if value < 1 or value > 5:
            raise HTTPException(status_code=400, detail="La importancia debe estar entre 1 y 5.")


def calculate_profile(responses: List[int], importance: List[int] | None = None):
    importance = importance or [3] * len(responses)
    validate_responses(responses, importance)
    axis_scores = {"economic": 0.0, "social": 0.0, "identity": 0.0}
    axis_weight = {"economic": 0.0, "social": 0.0, "identity": 0.0}
    for answer, weight, question in zip(responses, importance, POLITIC_QUESTIONS):
        signed_answer = (answer - 3) * question["direction"]
        axis = "economic" if question["axis"] == "economy" else question["axis"]
        axis_scores[axis] += signed_answer * weight
        axis_weight[axis] += 2 * weight
    profile = {
        axis: round((axis_scores[axis] / axis_weight[axis]) * 100) if axis_weight[axis] else 0
        for axis in axis_scores
    }
    ranked = sorted(
        IDEOLOGY_PROFILES.items(),
        key=lambda item: sqrt(sum((profile[axis] - item[1][axis]) ** 2 for axis in profile)),
    )
    profile["closest_ideology"] = ranked[0][0]
    profile["top_matches"] = [name for name, _ in ranked[:3]]
    profile["distance_to_top"] = round(sqrt(sum((profile[axis] - ranked[0][1][axis]) ** 2 for axis in ("economic", "social", "identity"))), 2)
    return profile


def match_parties(responses: List[int], importance: List[int], territory: str = "todos"):
    answer_values = [answer - 3 for answer in responses]
    allowed_scopes = {"nacional", territory}
    if territory in {"euskadi", "navarra"}:
        allowed_scopes.add("euskadi_navarra")
    requested = {party["id"] for party in PARTIES if territory == "todos" or party["scope"] in allowed_scopes}
    evidence = load_evidence()
    matches = []
    for party in PARTIES:
        if party["id"] not in requested or party["id"] not in PARTY_POSITIONS:
            continue
        positions = get_party_positions(party["id"])
        documented_topics = sorted({item["topic"] for item in evidence if item["party"] == party["id"]})
        reviewed_topics = sorted({item["topic"] for item in evidence if item["party"] == party["id"] and item.get("reviewed") and item.get("position") is not None})
        weighted_similarity = 0.0
        total_weight = 0.0
        agreements = []
        disagreements = []
        for answer, weight, question, position in zip(answer_values, importance, POLITIC_QUESTIONS, positions):
            similarity = 1 - (abs(answer - position) / 4)
            weighted_similarity += similarity * weight
            total_weight += weight
            if similarity >= 0.75:
                agreements.append(question["id"])
            elif similarity <= 0.25:
                disagreements.append(question["id"])
        score = round((weighted_similarity / total_weight) * 100) if total_weight else 0
        matches.append({**party, "score": score, "agreements": agreements[:3], "disagreements": disagreements[:3], "documented_topics": documented_topics, "reviewed_topics": reviewed_topics, "data_quality": "revisado" if reviewed_topics else ("documentado, pendiente de revisión" if documented_topics else "sin evidencia cargada")})
    return sorted(matches, key=lambda item: item["score"], reverse=True)


def load_evidence():
    evidence_path = BASE_DIR / "sources" / "review_queue.json"
    if not evidence_path.exists():
        evidence_path = BASE_DIR / "sources" / "evidence_candidates.json"
    if not evidence_path.exists():
        return []
    with open(evidence_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_party_positions(party_id):
    evidence = load_evidence()
    positions = list(PARTY_POSITIONS[party_id])
    reviewed = {item["topic"]: item["position"] for item in evidence if item["party"] == party_id and item.get("reviewed") and item.get("position") is not None}
    question_ids = [question["id"] for question in POLITIC_QUESTIONS]
    for index, question_id in enumerate(question_ids):
        if question_id in reviewed:
            positions[index] = reviewed[question_id]
    return positions


def summarize_profile(profile):
    first, second = profile["top_matches"][:2]
    if profile["distance_to_top"] < 45:
        return f"Tu perfil mezcla rasgos de {first} y {second}. Ninguna etiqueta resume por completo tus prioridades."
    descriptions = {
        "comunismo": "priorizas mucho la igualdad económica y la intervención del Estado",
        "socialismo": "valoras la redistribución, la protección social y una intervención estatal fuerte",
        "socialdemocracia": "buscas equilibrio entre Estado de bienestar, mercado y justicia social",
        "liberalismo": "priorizas la libertad individual y una economía más abierta",
        "conservadurismo": "valoras la tradición, la estabilidad y el orden social",
        "neoliberalismo": "prefieres un mercado más libre y menos regulación",
        "nacionalismo": "das importancia a la identidad nacional y la soberanía",
        "libertarismo": "valoras mucho la autonomía individual y la mínima intervención estatal",
    }
    return f"Tu perfil se acerca al {profile['closest_ideology']}: {descriptions[profile['closest_ideology']]} ."


def axis_label(value, left, right):
    if value < -25:
        return right
    if value > 25:
        return left
    return "posición intermedia"


@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    with open(BASE_DIR / "index.html", "r", encoding="utf-8") as file:
        content = file.read().replace(
            "{{ questions_json | safe }}",
            json.dumps(POLITIC_QUESTIONS, ensure_ascii=False),
        )
    return HTMLResponse(content=content, status_code=200)


@app.get("/api/questions")
async def get_questions():
    return {"questions": POLITIC_QUESTIONS, "count": len(POLITIC_QUESTIONS)}


@app.get("/api/parties")
async def get_parties():
    return {"parties": PARTIES, "data_status": "provisional"}


@app.get("/api/sources")
async def get_sources():
    with open(BASE_DIR / "sources" / "sources.json", "r", encoding="utf-8") as file:
        return {"sources": json.load(file)}


@app.get("/api/review-queue")
async def get_review_queue():
    queue_path = BASE_DIR / "sources" / "review_queue.json"
    if not queue_path.exists():
        return {"queue": [], "count": 0}
    with open(queue_path, "r", encoding="utf-8") as file:
        queue = json.load(file)
    return {"queue": queue, "count": len(queue)}


@app.post("/submit", response_class=HTMLResponse)
async def submit_survey(request: Request, survey_response: SurveyResponse):
    importance = survey_response.importance or [3] * len(survey_response.results)
    profile = calculate_profile(survey_response.results, importance)
    party_matches = match_parties(survey_response.results, importance, survey_response.territory)
    if not party_matches:
        raise HTTPException(status_code=400, detail="No hay partidos disponibles para ese territorio.")
    closest_party = party_matches[0]
    axis_labels = {
        "economic_label": axis_label(profile["economic"], "más intervención pública", "más libertad de mercado"),
        "social_label": axis_label(profile["social"], "más libertad social", "más orden y tradición"),
        "identity_label": axis_label(profile["identity"], "más pluralidad territorial", "más identidad nacional"),
    }
    return templates.TemplateResponse("result.html", {
        "request": request,
        "closest_ideology": profile["closest_ideology"].upper(),
        "closest_party": closest_party["name"],
        "closest_party_photo": closest_party["photo"],
        "summary": summarize_profile(profile),
        "top_matches": profile["top_matches"],
        "party_matches": party_matches[:5],
        "economic": profile["economic"],
        "social": profile["social"],
        "identity": profile["identity"],
        "data_notice": "Las posiciones de partidos son una matriz provisional pendiente de revisión documental con programas oficiales.",
        **axis_labels,
    })


@app.get("/result")
async def get_result():
    return JSONResponse({"result": "Success"})
