# Recommendation Project
## Implementation

The recommendation system for learning objects is built exclusively using data from Moodle logs, which are easily accessible through the course logs download option. This data is provided in CSV format, containing details such as timestamps, user identities, event types, and component details. The reliance on Moodle logs allows for straightforward and efficient data extraction without requiring access to Moodle’s internal database. Below are the steps used to preprocess the data and prepare it for the recommendation system:

### 1. User and Component Filtering
To ensure that only student interactions are analyzed, logs related to instructors or administrators are filtered out. This step isolates entries where users are actively engaging with course content, such as accessing resources or participating in forums.

### 2. Data Anonymization
In compliance with privacy standards, all identifying information is anonymized. Using pseudonymization, each user’s identifier is replaced with a unique, randomly generated code. This ensures the analysis respects privacy while maintaining interaction patterns for each user.

### 3. Event Parsing and Code Extraction
Regular expressions are used to extract key identifiers, including user IDs, component IDs, and subcomponents (if available). These fields enrich the dataset, enabling an accurate representation of user engagement with learning objects.

### 4. Data Reduction and Relevant Event Selection
The preprocessing pipeline focuses on interactions with specific components such as "Folder," "Resource," and "URL." Non-informative events (e.g., system configuration logs) are excluded, capturing only interactions relevant to educational recommendations.

### 5. Interaction Frequency and Weight Assignment
The system calculates access frequencies for each user-resource pair, normalizing these values to derive a "rating" score. This rating reflects the relative significance of each learning object based on user engagement.

### 6. User Weight Calculation
Each user is assigned a weight based on their engagement with learning objects:
- The average interaction frequency (or "rating") across all users is calculated.
- For each user, the average rating is divided by the global average, yielding a normalized weight.
- This weight is scaled between 0 and 1 for consistency. Optionally, the weights can be enhanced using grades or success indicators, capturing both intermediate and final performance metrics.

### 7. Temporal Structuring
All interactions are organized chronologically, with timestamps converted to a machine-readable format. This temporal arrangement supports sequence-based recommendation models.

### 8. Output Fact Tables
The preprocessed data is saved in structured fact tables, aligning with the defined data model. Each fact table serves a distinct purpose in the recommendation process:

| **Fact Table**                     | **Description**                                                               |
|------------------------------------|-------------------------------------------------------------------------------|
| **Users weights**                  | Stores normalized user weights.                                               |
| **Learning Objects weights**       | Contains weight assignments for each learning object based on engagement.     |
| **Learning objects interaction logs** | Records sequential "rating" (engagement) values for each user-resource interaction. |
| **Learning objects data**          | Provides metadata for learning objects, including titles and categories.      |

### Key Advantages
1. **Scalability:** The system relies solely on Moodle log data, making it easily implementable across institutions.
2. **Simplicity:** The straightforward preprocessing ensures minimal technical requirements.
3. **Transparency:** The approach allows clear interpretability of the generated recommendations.

These structured outputs serve as the foundation for the recommendation and validation scripts, ensuring adaptability and ease of implementation for a wide range of educational environments.

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
