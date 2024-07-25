# Proyecto de Recomendación

## Diagrama de Clases y métodos principales

![Diagrama de Clases](/imgs/Clase UML.png)

### Descripción del Diagrama

- **FastAPI (main.py)**:
  - Define una aplicación FastAPI con una ruta `/recommendations/{lo_id}`.
  - Depende de la clase `Recommender` del archivo `recommend.py`.

- **Recommender (recommend.py)**:
  - Encapsula la lógica de recomendación.
  - Inicializa y utiliza instancias de las clases `CosineSimilarity` y `ShortestPath` del archivo `algs.py`.
  - Métodos para manejar la actualización periódica de los datos y proporcionar recomendaciones.

- **CosineSimilarity y ShortestPath (algs.py)**:
  - Definen la lógica de los algoritmos de recomendación.
  - `CosineSimilarity` calcula similitudes basadas en el coseno.
  - `ShortestPath` calcula rutas más cortas basadas en las interacciones de los usuarios.
