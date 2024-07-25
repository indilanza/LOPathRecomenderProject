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
