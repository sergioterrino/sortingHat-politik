from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from typing import List
from questions import POLITIC_QUESTIONS

app = FastAPI()
# Monta el directorio de archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class SurveyResponse(BaseModel):
  results: List[int]

weights = [0.4, 0.35, 0.35, 0.2, 0.35, 0.35, 0.35, 0.35, 0.35, 0.4, 0.35, 0.4, 0.35, 0.35, 0.35, 0.4]

# grupos ideológicos  
comunismo = [10, 1, 10, 1, 10, 10, 10, 5, 5, 10, 1, 10, 10, 1, 9, 10]
socialismo = [9, 3, 9, 3, 9, 9, 2, 9, 6, 9, 3, 2, 2, 3, 10, 10]
socialdemocracia = [8, 4, 8, 4, 8, 7, 3, 8, 6, 8, 3, 8, 8, 4, 9, 9]
liberalismo = [4, 8, 4, 7, 3, 6, 8, 5, 6, 2, 5, 6, 3, 5, 5, 4]
conservadurismo = [3, 8, 2, 9, 2, 2, 8, 2, 3, 2, 8, 2, 2, 8, 2, 2]
neoliberalismo = [1, 10, 1, 9, 1, 3, 10, 3, 4, 1, 6, 3, 1, 6, 3, 3]
nacionalismo = [4, 7, 3, 6, 4, 1, 7, 7, 10, 3, 9, 3, 3, 10, 5, 5]
libertarismo = [2, 10, 1, 9, 2, 7, 10, 4, 4, 1, 5, 5, 1, 4, 1, 1]

weights_parties = [0.45, 0.35, 0.4, 0.3, 0.35, 0.4, 0.35, 0.35, 0.4, 0.35, 0.45, 0.4, 0.25, 0.4, 0.4, 0.35]

pcte = [10, 1, 10, 1, 10, 10, 1, 5, 5, 10, 1, 10, 10, 1, 8, 10] # Comunista
podemos = [9, 1, 9, 3, 9, 9, 2, 9, 6, 10, 2, 10, 9, 3, 10, 10]
sumar = [9, 2, 9, 4, 9, 8, 3, 8, 7, 10, 2, 9, 8, 3, 9, 9]
psoe = [8, 2, 8, 3, 8, 7, 3, 8, 6, 9, 3, 6, 7, 3, 8, 9] # Socialdemocracia moderada
pp = [3, 8, 4, 9, 3, 4, 8, 5, 3, 4, 8, 2, 2, 8, 5, 4] # Conservadurismo liberal
vox = [1, 9, 2, 10, 1, 2, 9, 2, 2, 1, 9, 9, 1, 9, 2, 2] # Conservadurismo con nacionalismo
erc = [8, 3, 3, 10, 7, 2, 8, 8, 10, 8, 3, 3, 2, 8, 8, 7] # Nacionalismo con socialdemocracia
junts = [3, 7, 3, 6, 4, 1, 7, 7, 10, 3, 9, 3, 3, 10, 6, 5] # Nacionalismo
p_lib = [1, 10, 1, 9, 2, 7, 10, 4, 4, 1, 5, 5, 1, 4, 1, 1] # Libertarismo


def calculate_weighted_euclidean_distance(user_responses, reference_vector, weights):
    distance = 0
    for i in range(len(user_responses)):
        distance += weights[i] * (user_responses[i] - reference_vector[i]) ** 2
    return distance ** 0.5

@app.get('/', response_class=HTMLResponse)
async def get_form():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)
  
@app.post('/submit', response_class=HTMLResponse)
async def submit_survey(request: Request, survey_response: SurveyResponse):
    user_responses = survey_response.results
    print('user_responses->', user_responses)
    dis_a = calculate_weighted_euclidean_distance(user_responses, comunismo, weights)
    dis_b = calculate_weighted_euclidean_distance(user_responses, socialismo, weights)
    dis_c = calculate_weighted_euclidean_distance(user_responses, socialdemocracia, weights)
    dis_d = calculate_weighted_euclidean_distance(user_responses, liberalismo, weights)
    dis_e = calculate_weighted_euclidean_distance(user_responses, neoliberalismo, weights)
    dis_f = calculate_weighted_euclidean_distance(user_responses, conservadurismo, weights)
    dis_g = calculate_weighted_euclidean_distance(user_responses, nacionalismo, weights)
    dis_h = calculate_weighted_euclidean_distance(user_responses, libertarismo, weights)
    
    distances_ideologies = {
        "comunismo": dis_a,
        "socialismo": dis_b,
        "socialdemocracia": dis_c,
        "liberalismo": dis_d,
        "neoliberalismo": dis_e,
        "conservadurismo": dis_f,
        "nacionalismo": dis_g,
        "libertarismo": dis_h
    }
    
    # se coge el diccionario de distancias y devuelve la key del valor(distancia) más pequeño
    closest_ideology = min(distances_ideologies, key=distances_ideologies.get)
    if closest_ideology == "comunismo":
        closest_party = "pcte"
        notes = ['No a la propiedad privada', 'Eliminar las clases sociales', 'El Estado controla la economía']
    elif closest_ideology == "socialismo":
            dis_podemos = calculate_weighted_euclidean_distance(user_responses, podemos, weights_parties)
            dis_sumar = calculate_weighted_euclidean_distance(user_responses, sumar, weights_parties)
            if dis_podemos < dis_sumar:
                closest_party = "podemos"
            else:
                closest_party = "sumar"
            notes = ['Redistribución de la riqueza', 'Políticas feministas y ecológicas', 'Intervección del Estado']
    elif closest_ideology == "socialdemocracia":
        dis_psoe = calculate_weighted_euclidean_distance(user_responses, psoe, weights_parties)
        dis_sumar = calculate_weighted_euclidean_distance(user_responses, sumar, weights_parties)
        if dis_psoe < dis_sumar:
            closest_party = "psoe"
        else:
            closest_party = "sumar"
        notes = ['Estado del bienestar', 'Economía mixta regulada', 'Igualdad de oportunidades']
    elif closest_ideology == "liberalismo":
        closest_party = "pp"
        notes = ['Libertad individual', 'Economía de mercado', 'Estado mínimo']
        notes = ['Libre mercado mínima regulación', 'Reducción de impuestos', 'Defensa de la iniciativa privada']
    elif closest_ideology == "neoliberalismo":
        dis_pp = calculate_weighted_euclidean_distance(user_responses, pp, weights_parties)
        dis_vox = calculate_weighted_euclidean_distance(user_responses, vox, weights_parties)
        if dis_pp < dis_vox:
            closest_party = "pp"
            notes = ['Reducción del papel del Estado en la economía', 'Privatización de sectores clave', 'Defensa del mercado libre']
        else:
            closest_party = "vox"
            notes = ['Economía ultraliberal', 'Privatización masiva', 'Desregulación del mercado y del trabajo']
        notes = ['Libre mercado', 'Reducir gasto público', 'Privatización']
    elif closest_ideology == "conservadurismo":
        closest_party = "vox"
        notes = ['Tradicion y estabilidad', 'Orden social', 'Libertad individual']
        notes = ['Defensa unidad nacional', 'Protección valores tradicionales', 'Control estricto inmigración']
    elif closest_ideology == "nacionalismo":
        dis_erc = calculate_weighted_euclidean_distance(user_responses, erc, weights_parties)
        dis_junts = calculate_weighted_euclidean_distance(user_responses, junts, weights_parties)
        if dis_erc < dis_junts:
            closest_party = "erc"
            notes = ['Independencia de Cataluña', 'Políticas de izquierda y sociales', 'Progresismo en derechos civiles']
        else:
            closest_party = "junts"
            notes = ['Independencia de Cataluña', 'Enfoque liberal en economía', 'Identidad cultural catalana']
    elif closest_ideology == "libertarismo":
        closest_party = "partido libertario"
        notes = ['Máxima libertad individual', 'Estado mínimo', 'Libre mercado']    
    
    print('distances_ideologies->', distances_ideologies)
    print('closest_ideology->', closest_ideology)
    print('closest_party->', closest_party)
    notes = ",".join(notes)
    print('notes->', notes)
    
    # with open("result.html", encoding="utf-8") as f:
    #     result_html = f.read()
        
    # result_html = result_html.replace("{{ closest_ideology }}", closest_ideology.upper())
    # result_html = result_html.replace("{{ closest_party }}", closest_party.upper())
    # result_html = result_html.replace("{{ notes }}", notes)
    # return HTMLResponse(content=result_html, status_code=200)
    return templates.TemplateResponse("result.html", {"request": request, "closest_ideology": closest_ideology.upper(), "closest_party": closest_party.upper(), "closest_party_photo": closest_party, "notes": notes})
  
@app.get('/result')
async def get_result():
  return {"result": "Success"}