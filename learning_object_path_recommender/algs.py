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
        # let's see what's the mean rating for each LO,
        df_mean = df.groupby(['loId'], sort = False).mean().rename(columns = {'rating': 'mean'})
        # join mean values to original DataFrame
        df = df.join(df_mean, on = 'loId', sort = False)
        # and subtract mean values from each rating,
        # so that rating of 0 becomes neutral
        df['rating'] = df['rating'] - df['mean']
        # ok? now pivot original DataFrame so that it becomes a feature/document matrix
        # and fill all NaNs (where a user hasn't rated a LO) with zeros, which is legal now
        df = df.pivot_table(index = 'userId', columns = 'loId', values = 'rating').fillna(0)
        # if there were LOs, having only equal ratings (ie, all 4.0)
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



class  ShortestPath:
    # Initialize the class with necessary data
    def __init__(self, df, df_uw, df_mw, grade_weights, ause_grade_weight=False, limit=20):
        self.limit = limit
        self.df_uw = df_uw
        self.df_mw = df_mw
        self.grade_weights=grade_weights
        self.use_grade_weight = ause_grade_weight
        self.distances = {}  # to store shortest paths

         # Verificación
        if not isinstance(self.use_grade_weight, bool):
            raise ValueError(f"Expected boolean for use_grade_weight, but got {type(self.use_grade_weight)}")

        # Sort dataframe by userId and timestamp
        df = df.sort_values(by=['userId', 'timestamp'])

        # Drop timestamp column
        df = df.drop(labels='timestamp', axis=1)
        
        # Get unique learning object IDs
        self.mids = df.index.get_level_values('loId').unique()
        df = df.reset_index(level='loId')

        # Create adjacency list
        self.al = self.build_adjacency_list(df)
        self.compute_shortest_paths()

    def build_adjacency_list(self, df):
        al = {}
        for uid in df.index.get_level_values('userId').unique():
            # Examine each user path
            path = df.loc[uid]
            if isinstance(path, pd.DataFrame):
                # Otherwise means a user made only one rating, not quite helpful here
                for m1, m2 in zip(path[:-1].itertuples(), path[1:].itertuples()):
                    # Initialize the adjacency list
                    al.setdefault(m1.loId, {}).setdefault(m2.loId, 0)
                    
                    # Get weights for user and learning objects
                    wu = self.get_user_weight(uid)
                    wm = self.get_lo_weight(m2.loId)

                    # Calculate the similarity
                    similarity = self.calculate_similarity(m1, m2, uid)

                    # Calculate the edge weight
                    freq_order = self.calculate_freq_order(uid, df, m1.loId, m2.loId)
                    prof_weight = self.get_prof_weight(m1.loId, m2.loId)
                    
                    edge_weight = (similarity * wu * wm * freq_order * prof_weight)
                    
                    al[m1.loId][m2.loId] += edge_weight

        return al

    def get_user_weight(self, uid):
        wu = self.df_uw.loc[self.df_uw['userId'] == uid, 'w'].values[0]
        if self.use_grade_weight==True:
            wu_grades = self.df_uw_grades.loc[self.df_uw_grades['userId'] == uid, 'w_grade'].values[0]
            wu *= wu_grades
        return wu if wu != 0 else -1

    def get_lo_weight(self, loId):
        wm = self.df_mw.loc[self.df_mw['loId'] == loId, 'w'].values[0]
        return wm if wm != 0 else -1

    def calculate_similarity(self, m1, m2, uid):
        rating_diff = abs(m1.rating - m2.rating)
        wu_prof_m1 = self.get_prof_weight(m1.loId)
        wu_prof_m2 = self.get_prof_weight(m2.loId)
        return 1 / np.exp((m1.rating * wu_prof_m1) - (m2.rating * wu_prof_m2))

    def calculate_freq_order(self, uid, df, lo1, lo2):
        # Filter the DataFrame for the specific user
        user_df = df.loc[uid]

        # Initialize the frequency counter
        freq = 0

        # Loop through the user's interactions to count transitions from lo1 to lo2
        for i in range(len(user_df) - 1):
            if user_df.iloc[i]['loId'] == lo1 and user_df.iloc[i + 1]['loId'] == lo2:
                freq += 1

        return freq

    def get_prof_weight(self, m1, m2=None):
        #if m2:
        #    return self.df_mw.loc[(self.df_mw['loId1'] == m1) & (self.df_mw['loId2'] == m2), 'w_prof'].values[0]
        #return self.df_mw.loc[self.df_mw['loId'] == m1, 'w_prof'].values[0]
        return 1

   # Get recommendations for a learning object (WORKING)
    """def recommend(self, lo_id):
        if not lo_id in self.al:
            return pd.DataFrame([], columns=['loId']).set_index('loId')
        
        # Convertir el diccionario a una lista de tuplas (loId, score)
        items = list(self.al[lo_id].items())
        # Crear un DataFrame a partir de esta lista de tuplas
        r = pd.DataFrame(items, columns=['loId', 'score'])

        #r = pd.DataFrame(self.al[lo_id], columns=['loId', 'score'])
        return r.set_index('loId') """
    

    # Get recommendations for a learning object
    def recommend(self, lo_id):
        if lo_id not in self.recs:
            return pd.DataFrame([], columns=['loId']).set_index('loId')

        # Get the precomputed shortest paths for the given LO
        r = pd.DataFrame(self.recs[lo_id], columns=['loId', 'distance'])
        
        # Sort by distance in ascending order (shorter distance means more relevant)
        r = r.sort_values(by='distance', ascending=True)
        
        # Limit the number of recommendations based on self.limit
        return r.head(self.limit).set_index('loId')






    def compute_shortest_paths(self):
        for mid in self.al:
            # Convert weights to their inverses to make them suitable for Dijkstra's algorithm
            self.al[mid] = list(map(lambda kv: (kv[0], 1 / kv[1] if kv[1] != 0 else float('inf')), self.al[mid].items()))
            self.al[mid].sort(key=lambda r: r[1])

        res = {}
        for mid in self.al:
            r = {}
            e = {}
            q = []
            d = self.limit + 1
            e[mid] = [0, mid]  # Initialize with a distance of 0 from the starting node
            heappush(q, e[mid])
            while q:
                v = heappop(q)
                if v[1] == -1 or not v[1] in self.al:
                    continue
                d -= 1
                if d < 0:
                    break

                r[v[1]] = v[0]  # Store the cumulative distance to this node
                for av in self.al[v[1]]:
                    if av[0] in r:
                        continue
                    alt = v[0] + av[1]
                    if av[0] in e:
                        if alt < e[av[0]][0]:
                            ii = e[av[0]][1]
                            e[av[0]][1] = -1
                            e[av[0]] = [alt, ii]
                            heappush(q, e[av[0]])
                    else:
                        e[av[0]] = [alt, av[0]]
                        heappush(q, e[av[0]])
            del r[mid]
            res[mid] = list(r.items())
            res[mid].sort(key=lambda r: r[1])  # Sort by distance in ascending order
        self.recs = res


