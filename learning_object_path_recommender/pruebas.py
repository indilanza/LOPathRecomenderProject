

from recommend import get_recs_for

def recommend_lo(learning_object_id: int):
    df_recs = get_recs_for(learning_object_id)
    #este es el formato del dataframe que se obtiene de la función get_recs_for
    #recs = recs.rename(columns = {'title_c': 'Cosine similarity alg:', 'title_s': 'Shortest path alg:'})

    # Convertir el DataFrame a JSON
    #recs_json = df_recs.to_json(orient='records')
                
    return df_recs




resul=recommend_lo(4527987)
print(resul)