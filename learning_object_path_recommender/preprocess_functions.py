import pandas as pd
import re
import numpy as np


def saveLoDataOrder(): #El orden de momento será un valor incremental en el orden en que se guardan los registros del fichero Lo_data.csv
    lo_data=pd.read_csv('outputs/Lo_data.csv')
    lo_data['order']=range(1,len(lo_data)+1)
    lo_data.to_csv('outputs/Lo_data.csv',index=False)


def extraer_palabras_entre_the_y_with_id(texto):
    # Patrón de expresión regular para encontrar las palabras entre el segundo "the" y el segundo "with id"
    patron = r"The.*?the.(.*?)with id "



    # Encontrar la coincidencia con el patrón en el texto
    coincidencia = re.search(patron, texto)


    if coincidencia:
        palabras_entre = coincidencia.group(1)
        return palabras_entre
    else:
        return None




# Función para extraer códigos de un texto y agregarlos como columnas al DataFrame
def extraer_codigos_y_agregar_columnas(texto):
    # Patrón de expresión regular para encontrar todos números entre comillas o entre este valor &#039;
    patron = r"'(\d+)'|&#039;(\d+)&#039;"
    #patron = r"'(\d+)'"
    


    # Encontrar todos los números que coincidan con el patrón
    #print(texto)
    codigos = re.findall(patron, texto)
    codigos_limpios = [grupo[0] if grupo[0] else grupo[1] for grupo in codigos]
    codigos = codigos_limpios

    # Inicializar variables para los códigos de usuario y componente
    codigo_usuario = None
    codigo_componente = None
    codigo_subcomponente = None
    word=None

    # Asignar el primer código encontrado como código de usuario
    if codigos:
        codigo_usuario = codigos[0]

    # Si hay al menos tres códigos, asignar el tercer código como código de componente
    if len(codigos) >= 2:
      codigo_componente = codigos[-1]

    if len(codigos) == 3:
      # Patrón de expresión regular para encontrar las palabras entre el segundo "the" y el segundo "with id"
      word=extraer_palabras_entre_the_y_with_id(texto)
      codigo_subcomponente=codigos[1]

    # Crear un diccionario con los códigos de usuario y componente
    dict_codigos = {'idUsuario': codigo_usuario, 'idComponente': codigo_componente, 'subComponente': word, 'idsubComponente':codigo_subcomponente}

    return pd.Series(dict_codigos)



def preprocessAndSave(logs_file, lecturer_list):

    df=pd.read_csv(logs_file)
   
    #df['Hora']= pd.to_datetime(df['Hora'])

    #Me quedo solo con los usuarios donde el 'Nombre completo del usuario' sean distintos de '-'
    #ya que el usuario no puede ser anónimo, neccesito identificar que sean solo los datos de los estudiantes los que preparan el modelo
    df_usersact=df[df['Nombre completo del usuario']!='-']

    #Elimino todos los componentes de tipo sistema
    #Sistema: Se refiere a la configuración y administración del sistema Moodle en sí, lo que generalmente está reservado para los administradores.
    df_usersact[df_usersact['Componente']!='Sistema']


    df=df_usersact

    # Aplicar la función a la columna 'Descripción' para extraer los códigos y crear nuevas columnas
    df = df.dropna(subset=['Descripción']) #elimino donde la descripción sea nula nan
    nuevas_columnas = df['Descripción'].apply(extraer_codigos_y_agregar_columnas)

    # Concatenar las nuevas columnas al DataFrame original
    df = pd.concat([df, nuevas_columnas], axis=1)


    #quitar los usuarios profesores y administradores
    #for lecturer in lecturer_list:
    #    df= df[df['idUsuario']!=lecturer]

    # Filtrar las filas del DataFrame que no estén en lecturer_list
    df = df[~df['idUsuario'].isin(lecturer_list)]

    #Hora de la acción, id del usuario,Nombre evento, id del componente (ej curso de tipo Sistema), subcompente (ej: el caso de discusion en el componente Foro), id del subcomponente
    df_4graph=df[['Hora','idUsuario','Nombre completo del usuario','Nombre evento','idComponente','Componente','Contexto del evento','subComponente','idsubComponente']]
    df_4graph.to_csv('outputs/moodle_log_preproc_kk.csv',sep='|')




def getDataForRecommender():
    #Preparar datos preprocesados para el modelo de recomendación
    df= pd.read_csv('outputs/moodle_log_preproc_kk.csv',sep='|')

    #Elimio todos los registros donde el contexto del evento sea el curso EI1013-MT1013 - Estructures de Dades (2021/2022), o sea el nombre del curso en sí, este log coincide con el registro "curso visto" del campo Nombre evento. 
    #No uso el campo 'Nombre evento'='curso visto', porque existen otros valores asociados a nombre del evento como Lista de usuarios vista, etc, que sí los recoge el nombre del contexto asociado al nombre del curso
    #get course name from the context of the event and save it in a variable
    course_name=df[df['Nombre evento']=='Curso visto']['Contexto del evento'].iloc[0]

    df=df[df['Contexto del evento']!=course_name]


    #Elimino todos los valoes donde el id del usuario o del componente sean nulos
    df_sin_nan = df.dropna(subset=['idUsuario'])
    df_sin_nan = df_sin_nan.dropna(subset=['idComponente'])
    df=df_sin_nan
    df['idUsuario'] = df['idUsuario'].astype(int)
    df['idComponente'] = df['idComponente'].astype(int)


    """
    # Definir una función lambda que concatena las tres columnas
    concatenar_columnas = lambda row: row['Nombre evento'] + ' ' + row['Componente'] + ' ' + str(row['idComponente'])

    # Aplicar la función lambda a lo largo de las filas del DataFrame para crear la nueva columna
    df['Concatenado'] = df.apply(concatenar_columnas, axis=1)
    df.head()
    """

    #df=df[df['Nombre evento']!='Curso visto'] #No hace falta esta linea, ya que ya elimino este tipo de evento cuando elimino los registos del contxto asociado al nombre del curso mas arriba
    r=df[['idUsuario','Nombre evento','idComponente']]
    r=r.groupby(['idUsuario','idComponente']).size().reset_index(name='frec')
    # Ordenar el DataFrame de mayor a menor según la columna 'frecuencia'
    r = r.sort_values(by='frec', ascending=False)


    #Dejar solo elementos de los componentes tipo Carpeta, Recurso,URL
    df_reduced = df[df['Componente'].isin(["Carpeta","Recurso","URL"]) ]



    #unir df y r a nivel de idUsuario e idComponente, para agregarle la frecuencia (frecuencia total de accesos de ese usuario al item) como valor o rating del item
    r1=r[['idUsuario','idComponente','frec']]
    df_merged=pd.merge(df_reduced,r1, on=['idUsuario','idComponente'])
    df_merged=df_merged[['Hora','idUsuario','Nombre evento','idComponente','Contexto del evento', 'Componente','frec']] #frec es la frecuencia total
    df_merged.columns=['Hora','idUsuario','Nombre evento','idComponente','Contexto del evento', 'Componente','rating']



    #lo es learning object
    lo=df_merged[['Hora','idUsuario','idComponente','rating']]
    lo.columns=['timestamp','userId','loId','rating']
    lo= lo[['userId','loId','rating','timestamp']]



    # Convertir la columna 'Fecha' al formato de fecha
    lo['timestamp'] = pd.to_datetime(lo['timestamp'], format='%d/%m/%y, %H:%M:%S')
    #lo['timestamp'] = pd.to_datetime(lo['timestamp'])

    # Convertir la columna 'Fecha' al formato de timestamp de valores enteros
    
    lo['timestamp'] = lo['timestamp'].astype('int64') // 10**9  # Convertir nanosegundos a segundos



    #ordenar por usuario y path para tener el path en el orden en que visito cada usuario cada LO
    lo=lo.drop_duplicates()
    lo=lo.sort_values(['userId','timestamp'])


    #Dejar solo la primera visita al componente, eliminar el resto
    #r1=lo.groupby(['userId','loId']).first()
    r1=lo #no elimino las visitas repetidas a cada LO, las dejo para que el modelo las tenga en cuenta, ya que la primera visita a un recurso, no tiene por qué ser la más importante, puede ser que el usuario no haya entendido el contenido y vuelva a visitarlo, por lo que es importante que el modelo tenga en cuenta todas las visitas a un LO
    

    #r1 los utiliza las funciones  saveUserStandardWeight(df,'pesos_usuarios.csv') ,saveLoStandardWeight(df,'pesos_lo.csv'),saveLoSequentialRatings(df,'Lo_ratings_seq.csv')
    #df_merged lo utiliza la funcion que guarda los datos de los LO
    return [r1,df_merged] #r1 es el dataframe con los pesos de los usuarios y los LOs, df_merged es el dataframe con los datos de los logs preprocesados. 


#file_name es el nombre del archivo de salida formato csv, ejemplo 'pesos_usuarios.csv'
def saveUserStandardWeight(r1,file_name):
   #Calular los pesos por estudiante
    media_frec= r1['rating'].mean()
    nl=0
    pesos=[]

    r_aux=r1
    r_aux=r_aux.reset_index()

    # Obtener la media de rating para todos los usuarios
    media_rating_por_usuario = r_aux.groupby('userId')['rating'].mean()
    media_rating_por_usuario
    
    # Calcular los pesos por usuario
    pesos_user = media_rating_por_usuario / media_frec

    # Obtener el mínimo y máximo de los pesos de los usuarios
    min_peso = pesos_user.min()
    max_peso = pesos_user.max()

    # Normalizar los pesos de los usuarios entre 0 y 1
    pesos_user_normalizados = (pesos_user - min_peso) / (max_peso - min_peso)

    pesos_user_normalizados=pesos_user_normalizados.reset_index()

    pesos_user_normalizados.columns=['userId','w']
    pesos_user_normalizados.to_csv('outputs/'+file_name, index=None)



def saveLoStandardWeight(r1,file_name):
    media_frec= r1['rating'].mean() #media de la frecuencia de acceso a los LOs

    r_aux=r1
    r_aux=r_aux.reset_index()

    # Calcular la media de rating para cada loId
    media_rating_por_loId = r_aux.groupby('loId')['rating'].mean()

    # Calcular los pesos por loId
    pesos_loId = media_rating_por_loId / media_frec #peso de cada LO
    #pesos_loId = media_rating_por_loId  #peso de cada LO

    # Obtener el mínimo y máximo de los pesos de los usuarios
    min_peso = pesos_loId.min()
    max_peso = pesos_loId.max()

    # Normalizar los pesos de los usuarios entre 0 y 1
    pesos_movie_normalizados = (pesos_loId - min_peso) / (max_peso - min_peso)

    pesos_movie_normalizados=pesos_movie_normalizados.reset_index()
    pesos_movie_normalizados.columns=['loId','w']
    pesos_movie_normalizados.to_csv('outputs/'+file_name, index=None)



#Mi Funcion asigna como "rating" el orden en que el usuario visito cada LO (de 1 a n)
def new_rating(path):
    n = len(path)
    values = []
    for i in range(0, n):
        values.append((n - i) / n)  # Ajuste para que los valores estén entre 0 y 1

    path['rating'] = values
    return path


#output_file_name es el nombre del archivo de salida formato csv
#Guarda como rating el orden de acceso de cada usuario a cada LO (de n a 1), pero normalizado entre 0 y 1
def saveLoSequentialRatings(r1,output_file_name):
    #r1=r1.set_index('userId') #No hace falta porque ya r1 viene con el userId y loId como index
    nl=0
    r2=r1.set_index('userId')
    dfn=pd.DataFrame(columns=['userId','loId','rating',	'timestamp'])
    for uid in r2.index.get_level_values('userId').unique():
        nl+=1
        # let's examine each user path
        path = r2.loc[uid]
        #print(path)
        path=new_rating(path)
        #path['userId']=uid
        #print(path)
        path=path.reset_index()
        #print(path)
        # Concatenar las nuevas filas por debajo del DataFrame existente
        dfn = pd.concat([dfn, path], ignore_index=True)

    dfn.to_csv('outputs/'+output_file_name,index=None)


def save_tfidf_weight(r1,file_name):
    # Calcular el TF-IDF 


    r_aux=r1
    r_aux=r_aux.reset_index()

    # Calculamos el total de visitas por usuario
    total_visitas_usuario = r_aux.groupby('userId')['rating'].transform('sum')

    # Calculamos la frecuencia de término (TF)
    r_aux['tf'] = r_aux['rating'] / total_visitas_usuario

    # Calculamos la frecuencia inversa de documento (IDF)
    # En este caso, la rareza del loId se puede medir simplemente contando el número de usuarios que han visitado cada película
    usuarios_por_pelicula = r_aux.groupby('loId')['userId'].nunique()
    num_total_usuarios = r_aux['userId'].nunique()
    r_aux['idf'] = np.log(num_total_usuarios / usuarios_por_pelicula)

    # Calculamos el TF-IDF adaptado
    r_aux['tf_idf'] = r_aux['tf'] * r_aux['idf']

    # Ahora 'r_aux' contiene la columna 'tf_idf' que representa el TF-IDF adaptado para cada visita de usuario a una película



    up=usuarios_por_pelicula.values
    resultado=np.log(num_total_usuarios / usuarios_por_pelicula)
    r_lista=resultado.values
    tfidf = up*r_lista

    # Seleccionar solo las películas únicas
    peliculas_sin_repetir = r_aux[['loId']].drop_duplicates()
    peliculas_sin_repetir['tfidf']=tfidf


    # Obtener el mínimo y máximo de los pesos de los usuarios
    min_peso = peliculas_sin_repetir['tfidf'].min()
    max_peso =  peliculas_sin_repetir['tfidf'].max()

    # Normalizar los pesos de los usuarios entre 0 y 1
    pesos_peli_normalizados = (tfidf - min_peso) / (max_peso - min_peso)

    #print("Los pesos de los usuarios normalizados son:")
    #print(pesos_peli_normalizados)

    peliculas_sin_repetir['tfidf_norm']=pesos_peli_normalizados


    pesos_movie_normalizados=peliculas_sin_repetir[['loId','tfidf_norm']]



    #exportar a csv
    #pesos_movie_normalizados=pesos_movie_normalizados.reset_index()
    pesos_movie_normalizados.columns=['loId','w']
    pesos_movie_normalizados.to_csv('outputs/{file_name}', index=None)



def saveLoData(df_merged,output_file_name):
    r= df_merged[['idComponente','Contexto del evento','Componente']]
    r=r.drop_duplicates()
    # Obtener una única tupla por idComponente único
    unique_tuples = r.groupby('idComponente').first().reset_index()
    r=unique_tuples
    r.columns=['loId','title','category']
    r.to_csv('outputs/'+output_file_name,index=None)