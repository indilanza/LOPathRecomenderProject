#!/usr/bin/env python3
import pandas as pd
#from search import Search
from .search import Search

#from algs import CosineSimilarity, ShortestPath
from .algs import CosineSimilarity, ShortestPath
from time import time
import os
import threading
from .preprocess_functions_moodle_server import prepareData

# LIMIT applies to everything, shown on the screen:
# movies search results, movies recommendations
LIMIT=5



script_dir = os.path.dirname(os.path.realpath(__file__))
#movies_csv = '{}/data/movies.csv'.format(script_dir)
#ratings_csv = '{}/data/ratings.csv'.format(script_dir)

#movies_csv = '{}/data/lo_data.csv'.format(script_dir)
#ratings_csv = '{}/data/lo_ratings.csv'.format(script_dir)

#ultimos ficheros testeados
#movies_csv = '{}/data/lo_data_ED.csv'.format(script_dir)
#ratings_csv = '{}/data/lo_ratings_ED.csv'.format(script_dir)

#Nuevos test con datos de los logs de moodle
movies_csv = '{}/outputs/Lo_data.csv'.format(script_dir)
ratings_csv = '{}/outputs/Lo_ratings_seq.csv'.format(script_dir)


pd.set_option('display.max_colwidth', 60)

# converter function, truncates long movie titles
def truncate_title(title):
    if len(title) > 50:
        title = title[:40] + ' ... ' + title[-6:]
    return title



#print('Loading...')
# loading movie ratings
ratings = pd.read_csv(ratings_csv, index_col = ['userId', 'loId'])

# loading smart searcher, two instances of which:
# one is matching words, existing in movie titles
movies = pd.read_csv(movies_csv, index_col = 'loId', converters = {'title': truncate_title})

# renders recommendations
def show_recs_for(movie_id):
    
    print('===> {}'.format(movies.loc[movie_id]['title']))
    
    cosine_recs = cosine.recommend(movie_id)


    cosine_recs = cosine_recs.join(movies, on='loId', how='inner')
    cosine_recs = cosine_recs.reset_index('loId')
    
    shortp_recs = shortp.recommend(movie_id)
    shortp_recs = shortp_recs.join(movies, on='loId', how='inner')
    shortp_recs = shortp_recs.reset_index('loId')
    recs = cosine_recs.join(shortp_recs, lsuffix='_c', rsuffix='_s')[['title_c', 'title_s']]
    recs = recs.rename(columns = {'title_c': 'Cosine similarity alg:', 'title_s': 'Shortest path alg:'})
    print(recs)


# get recommendations dataframe
def get_recs_for(movie_id):
    
    if cosine is None or shortp is None:
        print("Recommendation algorithms not initialized.")
        return None
    
    cosine_recs = cosine.recommend(movie_id)


    cosine_recs = cosine_recs.join(movies, on='loId', how='inner')
    cosine_recs = cosine_recs.reset_index('loId')
    
    shortp_recs = shortp.recommend(movie_id)
    shortp_recs = shortp_recs.join(movies, on='loId', how='inner')
    shortp_recs = shortp_recs.reset_index('loId')
    print(shortp_recs)
    recs = cosine_recs.join(shortp_recs, lsuffix='_c', rsuffix='_s')[['loId_c','title_c','loId_s', 'title_s']]
    recs = recs.rename(columns = {'loId_c': 'IDc:','title_c': 'Cosine similarity alg:','loId_s': 'IDs:', 'title_s': 'Shortest path alg:'})
    return recs


def ejecutar_funcion():
        global cosine, shortp
        prepareData()
        # loading movie ratings
        ratings_csv = '{}/outputs/Lo_ratings_seq.csv'.format(script_dir)
        ratings = pd.read_csv(ratings_csv, index_col = ['userId', 'loId'])
    # Aquí va tu función
        cosine = CosineSimilarity(ratings, limit=LIMIT)
        shortp = ShortestPath(ratings, limit=LIMIT)


if __name__ == "__main__":
    # Código que se ejecutará solo si este archivo se ejecuta directamente

    word_searcher = Search(df = movies, column = 'title', analyzer = 'word', ngram_range = (1,1))

# and the other one is matching ngrams against features of the former
    words = pd.DataFrame(word_searcher.features, columns = ['feat'])

    char_searcher = Search(df = words, column = 'feat', analyzer = 'char', ngram_range = (3,3))
    # please see search.py for details of implementation



    t = time()
    print('Cosine similarity recommendations are calculated in   ', end='', flush=True)
    # doing conventional i2i by means of cosine similarity algorithm (please see algs.py)
    cosine = CosineSimilarity(ratings, limit=LIMIT)
    #print('{:.3f} s'.format(time() - t))

    #t = time()
    #print('Shortest path recommendations are calculated in       ', end='', flush=True)
    # doing shortest path i2i (please see algs.py)
    shortp = ShortestPath(ratings, limit=LIMIT)
    #print('{:.3f} s'.format(time() - t))
    #print("\n")



    # search and recommend forever
    while True:
        r = input('Type in learning object title (q to quit): ')
        if not r:
            continue
        if r == 'q':
            break
        # if less than two words match features of word searcher
        # we're going for ngram search first, compulsory T9, if you will
        if len(list(filter(lambda w: w in word_searcher.features, r.split(' ')))) < 2:
            r = char_searcher.search(r)
            r = ' '.join(r.head(n=4)['feat'].values)
            if not r:
                continue
            print("looks like you're searching for: " + r)
        r = word_searcher.search(r)
        r = r.reset_index(level = 'loId')
        print("\n")
        if r.shape[0] == 1:
            show_recs_for(r['loId'].values[0])
        elif r.shape[0] > 1:
            print(r.head(n=LIMIT)['title'].to_frame())
            print("\n")
            index = input('Which one? (0-{}, default 0): '.format(min(r.shape[0], LIMIT)-1))
            print("\n")
            if not index:
                index = '0'
            if index.isdigit() and int(index) < min(r.shape[0], LIMIT):
                show_recs_for(r['loId'].values[int(index)])
        print("\n")



        pass
else:
    print('Tomo el camino del esle...Loading...')

    


    tiempo_en_segundos =21.600  

    threading.Timer(tiempo_en_segundos, ejecutar_funcion).start()

    # Inicia la función
    ejecutar_funcion()

    
    #cosine = CosineSimilarity(ratings, limit=LIMIT)
    


    #shortp = ShortestPath(ratings, limit=LIMIT)
 
