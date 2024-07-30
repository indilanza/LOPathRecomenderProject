# Recommendation Project

## Class Diagram

![Class Diagram](/imgs/uml_classes.png)

### Diagram Description

- **FastAPI (main.py)**:
  - Defines a FastAPI application with a route `/recommendations/{lo_id}`.
  - Depends on the `Recommender` class from the `recommend.py` file.

- **Recommender (recommend.py)**:
  - Encapsulates the recommendation logic.
  - Private attributes:
    - `- los_csv: str`
    - `- ratings_csv: str`
    - `- limit: int`
    - `- interval: int`
    - `- los: DataFrame`
    - `- cosine: CosineSimilarity`
    - `- shortp: ShortestPath`
  - Public methods:
    - `+ __init__(...)`
    - `+ truncate_title(...)`
    - `+ ejecutar_funcion(...)`
    - `+ start_timer(...)`
    - `+ show_recs_for(...)`
    - `+ get_recs_for(...)`
  - Uses the `prepareData()` function from the preprocessing module (`preprocess_functions_moodle_server.py`).

- **CosineSimilarity and ShortestPath (algs.py)**:
  - Define the logic for the recommendation algorithms.
  - Private attributes:
    - `- limit: int`
    - `- recs: DataFrame` (for `CosineSimilarity`)
    - `- mids: Index` (for `ShortestPath`)
    - `- recs: dict` (for `ShortestPath`)
  - Public methods:
    - `+ __init__(...)`
    - `+ recommend(...)`

- **Preprocessing Module (preprocess_functions_moodle_server.py)**:
  - Contains functions to prepare the data.
  - Public functions:
    - `+ saveLoDataOrder()`
    - `+ getDataForRecommender()`
    - `+ saveUserStandardWeight(r1, file_name)`
    - `+ saveLoStandardWeight(r1, file_name)`
    - `+ saveLoSequentialRatings(r1, output_file_name)`
    - `+ save_tfidf_weight(r1, file_name)`
    - `+ saveLoData(mydf, output_file_name)`
    - `+ prepareData()`

## Communication Diagram between Moodle and FastAPI

![Communication Diagram](/imgs/RecommenderSystem_Communication.png)

### Diagram Description

#### Sending Moodle Logs to FastAPI

1. **Moodle Plugin** sends student action logs to the **FastAPI Service** via a `POST /logs` request.
   - **Interval**: Continuous or every X minutes (depending on the Moodle plugin configuration).

2. **FastAPI Service** receives the logs and saves them in the log database.

#### Periodic Update of Recommender Data

1. **FastAPI Service** has a timer that reads the logs from the database at regular intervals.
   - **Interval**: Every 6 hours (recommended).

2. **FastAPI Service** processes the logs and updates the recommender with the latest data.

#### Obtaining Recommendations from Moodle

1. **Moodle Plugin** sends a `GET /recommend/{learning_object_id}` request to the **FastAPI Service** to get recommendations for learning object paths.
   - **Interval**: On-demand (when a specific recommendation is needed).

2. **FastAPI Service** calls the **Recommender** to generate the recommendations.
3. **Recommender** returns the recommendations to the **FastAPI Service**.
4. **FastAPI Service** sends the list of recommended learning object paths back to the **Moodle Plugin**.
