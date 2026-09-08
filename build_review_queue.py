import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCES_DIR = BASE_DIR / "sources"
INPUT_PATH = SOURCES_DIR / "evidence_candidates.json"
OUTPUT_PATH = SOURCES_DIR / "review_queue.json"


def candidate_score(item):
    quote = item["quote"].lower()
    score = len(item.get("matched_terms", [])) * 10
    score += min(len(quote), 700) / 100
    if item["page"] <= 10:
        score -= 30
    if "índice" in quote or "contenido" in quote:
        score -= 25
    if any(marker in quote for marker in ("propondremos", "impulsaremos", "derogaremos", "garantizaremos", "aprobaremos", "defenderemos", "crearemos")):
        score += 20
    return score


def main():
    candidates = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    selected = {}
    for item in candidates:
        key = (item["party"], item["topic"])
        if key not in selected or candidate_score(item) > candidate_score(selected[key]):
            selected[key] = item
    queue = []
    for item in sorted(selected.values(), key=lambda value: (value["party"], value["topic"])):
        queue.append({
            **item,
            "position": None,
            "reviewed": False,
            "reviewer_note": "",
        })
    OUTPUT_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Review queue: {len(queue)} party/topic entries")


if __name__ == "__main__":
    main()
