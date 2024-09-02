from fastapi import FastAPI, HTTPException
import httpx
import pandas as pd
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import csv
import uvicorn
import numpy as np
import sys
#sys.path.append('/home/indira/eDiplomaProyect')

# Importar tu biblioteca local

#import sys
#sys.path.append('C:\\Users\\indir\\Documents\\eDiploma_IA_Server\\eDiplomaProyect\\learning_object_path_recommender')
sys.path.append('C:\\Users\\indir\\Documents\\eDiploma_IA_Server\\LOPathRecomenderProject\\learning_object_path_recommender')


#from learning_object_path_recommender import *  # o cualquier otro import necesario
#from learning_object_path_recommender.recommend import get_recs_for
#from learning_object_path_recommender.recommend import *

import os

from recommend import Recommender



app = FastAPI()

script_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.abspath(os.path.join(script_dir, '..', 'learning_object_path_recommender'))

los_csv = os.path.join(base_dir, 'outputs', 'Lo_data.csv')
ratings_csv = os.path.join(base_dir, 'outputs', 'Lo_ratings_seq.csv')
user_weights_csv= os.path.join(base_dir, 'outputs', 'pesos_usuarios.csv')
lo_weights_csv= os.path.join(base_dir, 'outputs', 'pesos_lo.csv')
grade_weights_csv= os.path.join(base_dir, 'data', 'user_weight_grades.csv')

recommender = Recommender(los_csv, ratings_csv, user_weights_csv, lo_weights_csv, grade_weights_csv)#By default the parameters are "los_csv, ratings_csv, limit=5, interval=21600" and can be changed if needed
                                                                                                    #recommender = Recommender(los_csv, ratings_csv, user_weights_csv, lo_weights_csv, grade_weights_csv)



# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir acceso desde cualquier origen
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Permitir los métodos HTTP especificados
    allow_headers=["*"],  # Permitir todos los encabezados
)



@app.get("/")
async def read_root():
    return {"message": "¡Hola, Mundo!"}


# Configuración de la API de Moodle
#MOODLE_URL = "http://localhost/moodle/webservice/rest/server.php"
MOODLE_URL = "http://150.128.97.41/moodle/webservice/rest/server.php" 
MOODLE_TOKEN = "7f87b5854c9b6723b3ad0082e3d0ef1b" #Indira Token 


class ModuleData(BaseModel):
    module_id: int
    action: str
   
    
class MessageData(BaseModel):
    touserid: int
    text: str
    textformat: int

class CourseData(BaseModel):
    id: int
    fullname: str
    shortname: str
    categoryid: int
    visible: int
    format: str

class MoodleLogLine(BaseModel):
    userid:int
    cmid: int #id del modulo o recurso visto
    time: int


class LogEntry(BaseModel):
    timecreated: int
    userid: int
   
    contextid: int
    contextinstanceid: int
    contextlevel: int
    component: str
    eventname: str
    other: str
    


@app.post("/append_log/")
async def append_log(logLine: MoodleLogLine):
    try:
        file_logs = open('../moodle_logs/user_resource_view_log.txt', 'a')
        file_logs.write(str(logLine.userid) + "," + str(logLine.cmid) + "," + str(logLine.time) + "\n")
        file_logs.close()
        return {"message": "Log appended successfully"}
    except Exception as e:
        return {"error": str(e)}
    


@app.post("/logs/")
async def receive_logs(logs: list[LogEntry]):
    # Guardar los logs en un archivo CSV
    #csv_file = '../moodle_logs/student_logs.csv'
    csv_file = os.path.join(script_dir,'../moodle_logs/student_logs.csv')
    #with open(csv_file, mode='a', newline='') as file:
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=LogEntry.model_fields.keys())
        if file.tell() == 0:
            writer.writeheader()
        for log_entry in logs:
            writer.writerow(log_entry.model_dump())

    return {"message": "Log entries received and saved successfully"} 

@app.post("/course_edit_module/")
async def course_edit_module(moduleData: ModuleData):
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_course_edit_module",
        "moodlewsrestformat": "json",
        "id": moduleData.module_id,
        "action": moduleData.action
    }
    
      # Realiza la solicitud a la API de Moodle
    async with httpx.AsyncClient() as client:
        response = await client.post(MOODLE_URL, params=params)

    # Verifica el estado de la respuesta
    if response.status_code == 200:
        result = response.json()
        if "exception" in result:
            raise HTTPException(status_code=500, detail=f"Error en la API de Moodle: {result['exception']}")
        else:
            return {"message": "Modulo actualizado exitosamente"}
    else:
        raise HTTPException(status_code=500, detail=f"Error al llamar a la API de Moodle: {response.text}")



@app.post("/update_course_moodle")
async def update_course_moodle(course_data: CourseData):
    # Define la función de la API de Moodle para actualizar cursos
    moodle_api_function = "core_course_update_courses"
    
      # Configura los parámetros para la solicitud
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": moodle_api_function,
        "moodlewsrestformat": "json",
        "courses[0][id]": course_data.id,  # ID del curso existente
        "courses[0][fullname]": course_data.fullname,
        "courses[0][shortname]": course_data.shortname,  # Puedes ajustar este parámetro según tus necesidades
        "courses[0][categoryid]": course_data.categoryid, #0,  # ID de la categoría del curso (ajusta según tu estructura)
        "courses[0][visible]": course_data.visible, #1,  # Puedes ajustar la visibilidad del curso (1 para visible, 0 para oculto)
        "courses[0][format]": course_data.format #"topics",  # Puedes ajustar el formato del curso (topics, weeks, etc.)
    }
     # Realiza la solicitud a la API de Moodle
    async with httpx.AsyncClient() as client:
        response = await client.post(MOODLE_URL, params=params)

    # Verifica el estado de la respuesta
    if response.status_code == 200:
        result = response.json()
        if "exception" in result:
            raise HTTPException(status_code=500, detail=f"Error en la API de Moodle: {result['exception']}")
        else:
            return {"message": "Curso actualizado exitosamente"}
    else:
        raise HTTPException(status_code=500, detail=f"Error al llamar a la API de Moodle: {response.text}")


# Ruta para enviar un mensaje a un usuario en Moodle utilizando el método POST
@app.post("/send_message_moodle")
# Función para actualizar un curso existente en Moodle
async def send_message_moodle(message_data: MessageData):
    
    # Define la función de la API de Moodle para actualizar cursos
    moodle_api_function = "core_message_send_instant_messages"

    # Configura los parámetros para la solicitud
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": moodle_api_function,
        "moodlewsrestformat": "json",
       # "courses[0][id]": course_data.id,  # ID del curso existente
        
        "messages[0][touserid]": message_data.touserid,
        "messages[0][text]": message_data.text,
        "messages[0][textformat]": message_data.textformat,

    }

    # Realiza la solicitud a la API de Moodle
    async with httpx.AsyncClient() as client:
        response = await client.post(MOODLE_URL, params=params)

    # Verifica el estado de la respuesta
    if response.status_code == 200:
        result = response.json()
        if "exception" in result:
            raise HTTPException(status_code=500, detail=f"Error en la API de Moodle: {result['exception']}")
        else:
            return {"message": "Mensaje enviado exitosamente"}
    else:
        raise HTTPException(status_code=500, detail=f"Error al llamar a la API de Moodle: {response.text}")



#Obtener los datos de un usuario dado
@app.get("/get_user_moodle")
async def get_user_moodle(username: str):
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_user_get_users",
        "moodlewsrestformat": "json",
        "criteria[0][key]": "username",
        "criteria[0][value]": username,
       
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(MOODLE_URL, params=params)

    if response.status_code == 200:
        user_data = response.json()
        return user_data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve user data")


#Obtener todos los usuarios
@app.get("/get_all_users_moodle")
async def get_all_users_moodle():
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_user_get_users",
        "moodlewsrestformat": "json",
        "criteria[0][key]": "email", #se especifica el parametro email como filtro ya que se puede poner como valor de filtro "%%" que selecciona todos emails
        "criteria[0][value]": "%%",
       
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(MOODLE_URL, params=params)

    if response.status_code == 200:
        user_data = response.json()
        return user_data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve user data")






@app.get("/get_all_users")
async def get_all_users():
    # Parámetros para llamar a la función core_user_get_users
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_user_get_users",
        "moodlewsrestformat": "json"
    }

    try:
        # Realizar la solicitud GET a la API de Moodle
        async with httpx.AsyncClient() as client:
            response = await client.get(MOODLE_URL, params=params)
        response.raise_for_status()  # Lanza una excepción si hay un error HTTP

        # Procesar la respuesta JSON
        data = response.json()
        users = data.get("users", [])
        return users

    except httpx.HTTPStatusError as e:
        # Capturar errores HTTP (por ejemplo, 404, 500, etc.)
        raise HTTPException(status_code=e.response.status_code, detail="Error en la API de Moodle")
    except httpx.RequestError:
        # Capturar errores de red (por ejemplo, timeout, conexión rechazada, etc.)
        raise HTTPException(status_code=500, detail="Error al llamar a la API de Moodle: Problema de conexión")



@app.post("/send_learning_objects")
async def send_learning_objects(learning_objects: List[str]):
    try:
        
                file_objects = open('/path/to/learning_objects.txt', 'w')
                for i, obj in enumerate(learning_objects):
                    file_objects.write(f"ID: {i+1}, Title: {obj}\n")
                file_objects.close()
                return {"message": "Learning objects sent successfully"}
    except Exception as e:
                return {"error": str(e)}
            

               
def clean_dataframe(df):
    # Reemplazar infinitos por NaN
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Eliminar filas donde 'Shortest path alg:' sea NaN
    if 'Shortest path alg:' in df.columns:
        df = df.dropna(subset=['Shortest path alg:'])

    # Reemplazar NaN por None en otras columnas (si es necesario)
    df = df.applymap(lambda x: None if pd.isna(x) else x)
    
    return df


def recommend_lo(learning_object_id: int):
                #df_recs=get_recs_for(learning_object_id)

               
                
                df_recs = recommender.get_recs_for(learning_object_id)
                
                
                return df_recs


    
"""
@app.get("/recommend/{learning_object_id}")
async def recommend(learning_object_id: int):
    # Llamar a la función recommend_lo y obtener el resultado
    result_df = recommend_lo(learning_object_id)
    print(result_df)

    # Limpiar el DataFrame para eliminar valores problemáticos
    result_df = clean_dataframe(result_df)

    # Convertir el DataFrame a un diccionario con listas
    result_dict = result_df.to_dict(orient='list') 
    print(result_dict)
      
    # Verificar si el resultado es un diccionario válido
    if isinstance(result_dict, dict) and all(isinstance(value, list) for value in result_dict.values()):
        return result_dict
    else:
        raise HTTPException(status_code=500, detail="El resultado no es válido")

 """
@app.get("/recommend/{learning_object_id}")
async def recommend(learning_object_id: int):
    try:
        # Llamar a la función recommend_lo y obtener el resultado
        result_df = recommend_lo(learning_object_id)
        print("Result DataFrame:", result_df)

        # Limpiar el DataFrame para eliminar valores problemáticos
        result_df = clean_dataframe(result_df)
        print("Cleaned DataFrame:", result_df)

        # Convertir el DataFrame a un diccionario con listas
        result_dict = result_df.to_dict(orient='list')
        print("Result Dict:", result_dict)

        # Verificar si el resultado es un diccionario válido
        if isinstance(result_dict, dict) and all(isinstance(value, list) for value in result_dict.values()):
            return result_dict
        else:
            print("Invalid result_dict format.")
            raise HTTPException(status_code=500, detail="El resultado no es válido")

    except Exception as e:
        print("An error occurred:", str(e))
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/get_objects_from_csv")
async def get_objects_from_csv():
            objects = []            
            with open('../learning_object_path_recommender/learning_object_path_recommender/data/lo_data_ED.csv', 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    obj = {
                        "id": int(row['loId']),
                        "title": row['title']
                    }
                    objects.append(obj)
            
            return objects



# Iniciar el servidor FastAPI
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)