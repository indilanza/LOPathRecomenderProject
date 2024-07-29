# Proyecto de Recomendación

## Diagrama de Clases

![Diagrama de Clases](/imgs/Clase UML.png)

### Descripción del Diagrama

- **FastAPI (main.py)**:
  - Define una aplicación FastAPI con una ruta `/recommendations/{lo_id}`.
  - Depende de la clase `Recommender` del archivo `recommend.py`.

- **Recommender (recommend.py)**:
  - Encapsula la lógica de recomendación.
  - Atributos privados:
    - `- los_csv: str`
    - `- ratings_csv: str`
    - `- limit: int`
    - `- interval: int`
    - `- los: DataFrame`
    - `- cosine: CosineSimilarity`
    - `- shortp: ShortestPath`
  - Métodos públicos:
    - `+ __init__(...)`
    - `+ truncate_title(...)`
    - `+ ejecutar_funcion(...)`
    - `+ start_timer(...)`
    - `+ show_recs_for(...)`
    - `+ get_recs_for(...)`
  - Utiliza la función `prepareData()` del módulo de preprocesamiento (`preprocess_functions_moodle_server.py`).

- **CosineSimilarity y ShortestPath (algs.py)**:
  - Definen la lógica de los algoritmos de recomendación.
  - Atributos privados:
    - `- limit: int`
    - `- recs: DataFrame` (para `CosineSimilarity`)
    - `- mids: Index` (para `ShortestPath`)
    - `- recs: dict` (para `ShortestPath`)
  - Métodos públicos:
    - `+ __init__(...)`
    - `+ recommend(...)`

- **Módulo de Preprocesamiento (preprocess_functions_moodle_server.py)**:
  - Contiene funciones para preparar los datos.
  - Funciones públicas:
    - `+ saveLoDataOrder()`
    - `+ getDataForRecommender()`
    - `+ saveUserStandardWeight(r1, file_name)`
    - `+ saveLoStandardWeight(r1, file_name)`
    - `+ saveLoSequentialRatings(r1, output_file_name)`
    - `+ save_tfidf_weight(r1, file_name)`
    - `+ saveLoData(mydf, output_file_name)`
    - `+ prepareData()`




## Diagrama de Comunicación entre Moodle y FastAPI

![Diagrama de Intercomunicación](ruta/a/tu/imagen.png)

### Descripción del Diagrama

#### Envío de Logs de Moodle a FastAPI

1. **Moodle Plugin** envía los logs de acciones de los estudiantes al **FastAPI Service** a través de una solicitud `POST /logs`.
   - **Intervalo**: Continuo o cada X minutos (dependiendo de la configuración del plugin de Moodle).

2. **FastAPI Service** recibe los logs y los guarda en la base de datos de logs.

#### Actualización Periódica de Datos del Recomendador

1. **FastAPI Service** tiene un temporizador que, a intervalos regulares, lee los logs desde la base de datos.
   - **Intervalo**: Cada 6 horas (recomendado).

2. **FastAPI Service** procesa los logs y actualiza el recomendador con los datos más recientes.

#### Obtención de Recomendaciones desde Moodle

1. **Moodle Plugin** envía una solicitud `GET /recommend/{learning_object_id}` al **FastAPI Service** para obtener recomendaciones de caminos de objetos de aprendizaje.
   - **Intervalo**: Bajo demanda (cuando se requiere una recomendación específica).

2. **FastAPI Service** llama al **Recommender** para generar las recomendaciones.
3. **Recommender** devuelve las recomendaciones al **FastAPI Service**.
4. **FastAPI Service** envía la lista de caminos de learning objects recomendados de vuelta al **Moodle Plugin**.

