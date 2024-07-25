#!/usr/bin/env python3
import pandas as pd
import os
import threading
from .search import Search
from .algs import CosineSimilarity, ShortestPath
from .preprocess_functions_moodle_server import prepareData

class Recommender:
    def __init__(self, los_csv, ratings_csv, limit=5, interval=21600):
        self.los_csv = los_csv
        self.ratings_csv = ratings_csv
        self.limit = limit
        self.interval = interval
        self.los = pd.read_csv(self.los_csv, index_col='loId', converters={'title': self.truncate_title})
        self.cosine = None
        self.shortp = None
        self.start_timer()

    def truncate_title(self, title):
        if len(title) > 50:
            title = title[:40] + ' ... ' + title[-6:]
        return title

    def execute_function(self):
        prepareData()
        ratings = pd.read_csv(self.ratings_csv, index_col=['userId', 'loId'])
        self.cosine = CosineSimilarity(ratings, limit=self.limit)
        self.shortp = ShortestPath(ratings, limit=self.limit)
        print("Recomendaciones actualizadas.")

    def start_timer(self):
        threading.Timer(self.interval, self.start_timer).start()
        self.execute_function()

    def show_recs_for(self, lo_id):
        print('===> {}'.format(self.los.loc[lo_id]['title']))
        
        cosine_recs = self.cosine.recommend(lo_id)
        cosine_recs = cosine_recs.join(self.los, on='loId', how='inner')
        cosine_recs = cosine_recs.reset_index('loId')
        
        shortp_recs = self.shortp.recommend(lo_id)
        shortp_recs = shortp_recs.join(self.los, on='loId', how='inner')
        shortp_recs = shortp_recs.reset_index('loId')
        
        recs = cosine_recs.join(shortp_recs, lsuffix='_c', rsuffix='_s')[['title_c', 'title_s']]
        recs = recs.rename(columns={'title_c': 'Cosine similarity alg:', 'title_s': 'Shortest path alg:'})
        print(recs)

    def get_recs_for(self, lo_id):
        if self.cosine is None or self.shortp is None:
            print("Recommendation algorithms not initialized.")
            return None
        
        cosine_recs = self.cosine.recommend(lo_id)
        cosine_recs = cosine_recs.join(self.los, on='loId', how='inner')
        cosine_recs = cosine_recs.reset_index('loId')
        
        shortp_recs = self.shortp.recommend(lo_id)
        shortp_recs = shortp_recs.join(self.los, on='loId', how='inner')
        shortp_recs = shortp_recs.reset_index('loId')
        
        recs = cosine_recs.join(shortp_recs, lsuffix='_c', rsuffix='_s')[['loId_c', 'title_c', 'loId_s', 'title_s']]
        recs = recs.rename(columns={'loId_c': 'IDc:', 'title_c': 'Cosine similarity alg:', 'loId_s': 'IDs:', 'title_s': 'Shortest path alg:'})
        return recs

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    los_csv = '{}/outputs/Lo_data.csv'.format(script_dir)
    ratings_csv = '{}/outputs/Lo_ratings_seq.csv'.format(script_dir)
    recommender = Recommender(los_csv, ratings_csv)
