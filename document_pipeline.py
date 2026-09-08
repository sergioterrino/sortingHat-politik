"""Extract candidate evidence from electoral programme PDFs.

This script deliberately does not assign ideology scores. It creates an auditable
review queue with page numbers and excerpts for a human or assisted review.
"""

import json
import re
from pathlib import Path

from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent
SOURCES_DIR = BASE_DIR / "sources"
EVIDENCE_PATH = SOURCES_DIR / "evidence_candidates.json"

TOPIC_TERMS = {
    "taxes": ["impuesto", "fiscal", "tribut", "IRPF", "renta"],
    "market": ["empresa", "autónom", "regulación", "libre mercado", "competencia"],
    "services": ["sanidad", "educación", "dependencia", "servicio público"],
    "housing": ["vivienda", "alquiler", "arrendamiento", "suelo"],
    "pensions": ["pension", "jubilación", "cotización"],
    "rights": ["libertad", "derechos", "LGTBI", "igualdad", "aborto", "eutanasia"],
    "security": ["seguridad", "policía", "penas", "delincuencia", "justicia"],
    "migration": ["inmigración", "inmigrante", "frontera", "asilo", "nacionalidad"],
    "climate": ["cambio climático", "transición energética", "renovable", "nuclear", "medio ambiente"],
    "tradition": ["familia", "tradición", "autoridad", "natalidad"],
    "territory": ["autonomía", "independencia", "territorial", "referéndum", "nación"],
    "centralization": ["Estado", "competencias", "centraliz", "unidad de España"],
    "europe": ["Unión Europea", "Bruselas", "europe", "soberanía"],
    "culture": ["lengua", "cultura", "lingüística", "identidad"],
    "democracy": ["democracia", "listas abiertas", "participación", "referéndum", "transparencia"],
    "monarchy": ["monarquía", "república", "jefatura del Estado", "Corona"],
}


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def extract_pdf(path):
    reader = PdfReader(str(path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = clean(page.extract_text())
        if text:
            pages.append({"page": page_number, "text": text})
    return pages


def find_candidates(party, source, source_url, pages):
    candidates = []
    for page in pages:
        lowered = page["text"].lower()
        for topic, terms in TOPIC_TERMS.items():
            hits = [term for term in terms if term.lower() in lowered]
            if not hits:
                continue
            first_hit = min(lowered.find(term.lower()) for term in hits)
            start = max(0, first_hit - 260)
            excerpt = page["text"][start:start + 900]
            candidates.append({
                "party": party,
                "topic": topic,
                "document": source,
                "source_url": source_url,
                "page": page["page"],
                "matched_terms": hits,
                "quote": excerpt,
                "position": None,
                "reviewed": False,
            })
    return candidates


def main():
    inventory = json.loads((SOURCES_DIR / "sources.json").read_text(encoding="utf-8"))
    output = []
    for item in inventory:
        local_file = item.get("local_file")
        if not local_file or not local_file.lower().endswith(".pdf"):
            continue
        path = SOURCES_DIR / local_file
        if not path.exists():
            continue
        pages = extract_pdf(path)
        output.extend(find_candidates(item["party"], local_file, item["url"], pages))
    EVIDENCE_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(output)} candidate passages from {len({item['document'] for item in output})} PDFs")


if __name__ == "__main__":
    main()
