# Flujo de revisión documental

## Dónde guardar documentos

Guarda los PDFs originales en esta carpeta: `backend/sources/`.
Conserva también la URL original en `sources.json`. No sustituyas el documento
original por una traducción; si el programa está en catalán o gallego, añade una
traducción de trabajo aparte durante la revisión.

## Extraer candidatos

Desde la raíz del proyecto:

```powershell
& .\backend\venv\Scripts\python.exe .\backend\document_pipeline.py
```

El script genera `evidence_candidates.json` con:

- partido y documento
- URL original
- página
- palabras encontradas
- cita de contexto
- posición todavía vacía
- estado de revisión

## Revisar una posición

La posición final de cada partido y tema usa esta escala:

- `-2`: oposición clara
- `-1`: posición moderadamente contraria
- `0`: no consta, ambigua o equilibrio
- `1`: posición moderadamente favorable
- `2`: defensa clara

Para marcar una entrada como utilizable por el matching hay que completar:

```json
{
  "position": 2,
  "reviewed": true,
  "reviewer_note": "La medida se defiende explícitamente en el texto citado."
}
```

Hasta que `reviewed` sea `true`, el motor conserva la matriz provisional y lo
muestra al usuario como `documentado, pendiente de revisión`. Nunca se debe
confundir una coincidencia de palabras con una posición política validada.
