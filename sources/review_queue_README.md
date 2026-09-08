# Cola de revisión activa

El archivo `review_queue.json` contiene una entrada por partido y tema. Es la
interfaz intermedia entre los programas electorales y el motor de matching.

Para activar una posición hay que editar la entrada correspondiente:

```json
{
  "party": "pp",
  "topic": "housing",
  "page": 31,
  "quote": "...",
  "position": 1,
  "reviewed": true,
  "reviewer_note": "La propuesta apoya ampliar vivienda pública, pero rechaza el control general de alquileres."
}
```

La posición solo se usa en el cálculo cuando `reviewed` es `true` y `position`
es un número entre `-2` y `2`.

La cola se regenera con:

```powershell
& .\backend\venv\Scripts\python.exe .\backend\build_review_queue.py
```

No marques una entrada como revisada basándote solo en una palabra coincidente.
La cita debe describir una medida o posición concreta, no un índice o una
mención genérica.
