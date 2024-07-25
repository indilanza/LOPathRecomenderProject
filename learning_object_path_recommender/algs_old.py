import numpy as np
import pandas as pd
import scipy.sparse as sp
import sklearn.preprocessing as pp
from math import exp
from heapq import heappush, heappop
import os

# conventional i2i
class CosineSimilarity():
    # expects DataFrame, loaded from ratings.csv
    def __init__(self, df, limit=20):
        self.limit = limit

        # no need for timestamp here
        df = df.drop(labels = 'timestamp', axis = 1)
        # let's see what's the mean rating for each movie,
        df_mean = df.groupby(['loId'], sort = False).mean().rename(columns = {'rating': 'mean'})
        # join mean values to original DataFrame
        df = df.join(df_mean, on = 'loId', sort = False)
        # and subtract mean values from each rating,
        # so that rating of 0 becomes neutral
        df['rating'] = df['rating'] - df['mean']
        # ok? now pivot original DataFrame so that it becomes a feature/document matrix
        # and fill all NaNs (where a user hasn't rated a movie) with zeros, which is legal now
        df = df.pivot_table(index = 'userId', columns = 'loId', values = 'rating').fillna(0)
        # if there were movies, having only equal ratings (ie, all 4.0)
        # then we can't really recommend anything to them, hence removing
        df = df.loc[:, (df != 0).any(axis = 0)]
        # here we go, let's turn DataFrame into sparse matrix, normalize ratings,
        cnm = pp.normalize(sp.csr_matrix(df.values), axis = 0)
        # calculate recommendations and turn sparse matrix back into DataFrame,
        # having loId index, loId columns and values, representing relevance of A to B
        self.recs = pd.DataFrame((cnm.T * cnm).todense(), columns=df.columns, index=df.columns)

    # retrieves "limit" of recommendations for given lo_id out of precalculated DataFrame
    def recommend(self, lo_id):
        if not lo_id in self.recs.index.values:
            return pd.DataFrame([], columns=['loId']).set_index('loId')
        r = self.recs[lo_id].sort_values(ascending=False)
        #r = r.drop(labels=lo_id)
        r = r.drop(lo_id) #elimino la fila con el indice loId
        r = r.to_frame().rename(columns = {lo_id: 'score'}) #este es el original
        #r = r.to_frame() #loId esta es mi modificacion
        return r.head(n=self.limit)


# now, the new way of getting i2i recommendations
class ShortestPath():
    # expects DataFrame, loaded from ratings.csv
    def __init__(self, df, limit=20):
        self.limit = limit

        #cargar pesos de los usuarios
        script_dir = os.path.dirname(os.path.realpath(__file__))
        #movies_csv = '{}/data/lo_data_ED.csv'.format(script_dir)
        df_uw = pd.read_csv('{}/data/user_weight.csv'.format(script_dir))
        df_uw_grades = pd.read_csv('{}/data/user_weight_grades.csv'.format(script_dir))

        #cargar pesos de las peliculas
        df_mw=pd.read_csv('{}/data/movie_weight.csv'.format(script_dir))

        # here the order of happenings is very crucial,
        df = df.sort_values(by=['userId', 'timestamp'])
        print(df.values)
        #print len of dataframe
        print(len(df))
        # once sorted, we can remove timestamp (will save us a couple of bytes)
        df = df.drop(labels = 'timestamp', axis = 1)
        # mids stands for movie IDs (I'm yet another lazy coder)
        self.mids = df.index.get_level_values('loId').unique()
        df = df.reset_index(level = 'loId')

        # al is adjacency list, by the way
        al = {}
        for uid in df.index.get_level_values('userId').unique():
            # let's examine each user path
            path = df.loc[uid]
            if isinstance(path, pd.DataFrame):
                # otherwise means a user made only one rating, not quite helpful here
                for m1, m2 in zip(path[:-1].itertuples(), path[1:].itertuples()):
                    # for each pair of rated movie and next rated movie
                    al.setdefault(m1.loId, {}).setdefault(m2.loId, 0)
                    # we see what a user thinks of how similar they are,
                    # the more both ratings are close to each other - the higher
                    # is similarity
                    #al[m1.loId][m2.loId] += 1/exp(abs(m1.rating - m2.rating)) - 0.5
                    
                    #obtener el valor de los pesos del usuario uid en base a la interaccion con "los objetos de abrendisaje m1", mi metodo penaliza a los alumnos que interactuan por encima de la media con los LO, ya que no es eficiente en el tiempo revisitar  tantas veces el mismo LO             
                    wu = df_uw.loc[df_uw['userId'] == uid, 'w'].values[0]

                    #obtener el valor de los pesos del usuario en base a su puntuacion final
                    #comprobar si el usuario existe en el dataframe de los pesos de los usuarios
                    if len(df_uw_grades.loc[df_uw_grades['userId'] == uid]) == 0: #si no existe el usuario en el dataframe de los pesos de los usuarios. Esto puede ser que el usuario no sea un alumno o si lo fuera no haya sido calificado. Entonces se le asigna un peso pequeño valor de 0.0001 (mimo valor sustituido en el caso de que haya obtneido cero en la asignatura)
                        #wu_grades = 0.001
                        wu_grades=-1
                        
                    else:
                        wu_grades = df_uw_grades.loc[df_uw_grades['userId'] == uid, 'w_grade'].values[0]
                    

                    wu_total= wu*wu_grades

                   
                    #obtener el valor de los pesos de los objetos de aprendizaje m2. La funcion del peso, penaliza aquellas LO que se visitan con una fruencia alta, ya que posrian ser manuales que se visitan con mucha frecuencia               
                    wm = df_mw.loc[df_mw['loId'] == m2.loId, 'w'].values[0]


                    if wu_total == 0:
                        wu_total=-1   

                    if wm == 0:
                        wm=-1                  

                    #CONFIGURACIONES QUE MEJOR FUNCIONAN HASTA AHORA wu_total=wu Y wm=1
                    #comentar o no segun se quiera utilizar los pesos de los usuarios y los LO
                    #wu_total=1
                    #wu_total=wu 
                    #wu_total=wu_grades #funciona incorrectamente porque con elq uery: boletin problemas del tema 2, como 4 opcion de salida pone Archivo: problemas tema 1, y no deberia ir hacia atras
                    #wm=1


                    #Forumlada modificada para incluir los pesos de los usuarios y las peliculas
                    #Comprobar y corregir para le caso de que se divida por cero...... 
                    #Agregué + 0.5 para evitar la division por cero                                     
                    #al[m1.loId][m2.loId] += 1/wu_total*wm/exp(abs(m1.rating - m2.rating))  - 0.5
                    #Me di cuenta que en el algoritmo implementado en lugar de dividir 1 por los valores grandes para obtener una longitud pequeña, en su lugar obtienes valores grandes que despues le ponen signo negativo para que sean los valores pequeños de distancia al ordenar y recomendar. Entonces ta formula solo contiene el denominador de la fortmula prouesta en el articulo de la web
                    #Notal qeu en la formual originar consideraban los pesos iguales para los usuarios y los LO, pero en mi caso los he separado en pesos calculados en base a su frecuencia de interaccion global.
                    #al[m1.loId][m2.loId] += wu_total*wm/exp(abs(m1.rating - m2.rating))  - 0.5  #esta formula tiene un inconveniente porque mientras un camino dado este mas reforazo por mas alumnos, su distancia siempre sera la mas corta. Y da igual que ponga 1/entre toda al formual, ocurre el mismo resultado o similar, sobre todo cuando prueb con el boletin 3
                    al[m1.loId][m2.loId] +=  1/wu_total*wm/exp(abs(m1.rating - m2.rating))  - 0.5  
                   

        for mid in al:
            # let's make a list for each movie in adjacency list, so that
            # adjacency list becomes a list indeed, along the way, we have to
            # inverse summed up similarity, so that the higher is the similarity -
            # the shorter is the length of an edge in movies graph
            al[mid] = list(map(lambda kv: (kv[0], -kv[1]), al[mid].items())) #inverte los signos de los pesos a negativo para hacer que los valores mas grandes sean mas pequeños, haciendo asi la distancia mas corta
            # yes, list is required to be sorted from closest to farthest
            al[mid].sort(key = lambda r: r[1])

        res = {}
        for mid in al:
            # you still here? sweet
            # we have BFS with priority queue here,
            # I always thought that its name is Dijkstra algorithm
            # although lately realized, that Dijkstra's one used to be
            # a little bit more naive. Wat moet ik doen?
            # r stands for Results
            r = {}
            # e stands for elements in the queue
            e = {}
            # q stands for queue (sincerely, C.O.)
            q = []
            # d stands for Depth of search
            # (well, actually, there's no depth in breadth first search,
            # it's just a number of nodes we're willing to visit)
            d = limit + 1
            # starting from originator itself
            e[mid] = [0, mid]
            heappush(q, e[mid])
            while q:
                # while there are vertices in the queue
                v = heappop(q)
                # and they are not dummy (-1 is explained below) or not known
                if v[1] == -1 or not v[1] in al:
                    continue
                d -= 1
                # and required depth isn't reached:
                if d < 0:
                    break

                # we consider current vertice a next relevant recommendation
                r[v[1]] = v[0]

                # and we have to fill the queue with
                # other adjacent vertices
                for av in al[v[1]]:
                    if av[0] in r:
                        # this one we've already seen
                        continue
                    # we're getting further from originator
                    alt = v[0] + av[1]
                    if av[0] in e:
                        # but what if next adjacent vertice is already queued
                        if alt < e[av[0]][0]:
                            # well, if we found a shorter path, let's prioritize
                            # this vertice higher in the queue
                            ii = e[av[0]][1]
                            # here we go, -1 is a dummy distance value for a vertice
                            # that has been moved in the queue, one doesn't simply
                            # remove a node from heapified list, if you know what I mean
                            e[av[0]][1] = -1
                            # so we enqueue a new one
                            e[av[0]] = [alt, ii]
                            heappush(q, e[av[0]])
                    else:
                        # otherwise, just put it in the queue
                        e[av[0]] = [alt, av[0]]
                        heappush(q, e[av[0]])
            # of course, recommendation of a movie to itself is way too obvious
            del r[mid]
            # listify and sort other recommendaions
            res[mid] = list(r.items())
            res[mid].sort(key = lambda r: -r[1])
        # save results
        self.recs = res

    # returns all recommendations for a given lo_id
    # the trick here is that "limit" has already been applied upon calculation
    # and the higher is the "limit" - the longer calculation takes, linearly,
    # so here's no magical overtake of fancy scipy sparse matrix by pure python algorithm
    def recommend(self, lo_id):
        if not lo_id in self.recs:
            return pd.DataFrame([], columns=['loId']).set_index('loId')
        r = pd.DataFrame(self.recs[lo_id], columns=['loId', 'score'])
        return r.set_index('loId')


