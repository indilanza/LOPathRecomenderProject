import pandas as pd
import re
import numpy as np
import os

script_dir = os.path.dirname(os.path.realpath(__file__))

def saveLoDataOrder():
    # The order will be an incremental value based on the order of records in Lo_data.csv
    LoData_csv = '{}/outputs/Lo_data.csv'.format(script_dir)

    lo_data = pd.read_csv(LoData_csv)
    lo_data['order'] = range(1, len(lo_data) + 1)
    lo_data.to_csv(LoData_csv, index=False)

def getDataForRecommender():
    dir = os.path.join(script_dir, '../../moodle_logs/student_logs.csv')
    df = pd.read_csv(dir, sep=',')

    df = df[['userid', 'contextinstanceid', 'timecreated']]
    r = df[['userid', 'contextinstanceid']].groupby(['userid', 'contextinstanceid']).size().reset_index(name='frec')

    r = r.sort_values(by='frec', ascending=False)
    r1 = r[['userid', 'contextinstanceid', 'frec']]
    df2 = df[['timecreated', 'userid', 'contextinstanceid']]
    df_merged = pd.merge(r1, df2, on=['userid', 'contextinstanceid'])
    df_merged = df_merged[['timecreated', 'userid', 'contextinstanceid', 'frec']]
    df_merged.columns = ['timestamp', 'userId', 'loId', 'rating']

    lo = df_merged[['timestamp', 'userId', 'loId', 'rating']]
    lo = lo[['userId', 'loId', 'rating', 'timestamp']]
    lo = lo.drop_duplicates()
    lo = lo.sort_values(['userId', 'timestamp'])

    return lo

def saveUserStandardWeight(r1, file_name):
    # Calculate weights per student
    media_frec = r1['rating'].mean()

    r_aux = r1.reset_index()

    # Calculate the mean rating for all users
    mean_rating_per_user = r_aux.groupby('userId')['rating'].mean()

    # Calculate weights per user
    user_weights = mean_rating_per_user / media_frec

    # Normalize user weights between 0 and 1
    normalized_user_weights = (user_weights - user_weights.min()) / (user_weights.max() - user_weights.min())
    normalized_user_weights = normalized_user_weights.reset_index()
    normalized_user_weights.columns = ['userId', 'w']

    dir = os.path.join(script_dir, 'outputs', file_name)
    normalized_user_weights.to_csv(dir, index=None)

def saveLoStandardWeight(r1, file_name):
    media_frec = r1['rating'].mean()
    r_aux = r1.reset_index()

    # Calculate the mean rating for each loId
    mean_rating_per_loId = r_aux.groupby('loId')['rating'].mean()

    # Calculate weights per loId
    loId_weights = mean_rating_per_loId / media_frec

    # Normalize weights between 0 and 1
    normalized_loId_weights = (loId_weights - loId_weights.min()) / (loId_weights.max() - loId_weights.min())
    normalized_loId_weights = normalized_loId_weights.reset_index()
    normalized_loId_weights.columns = ['loId', 'w']

    dir = os.path.join(script_dir, 'outputs', file_name)
    normalized_loId_weights.to_csv(dir, index=None)

def new_rating(path):
    n = len(path)
    values = [(n - i) / n for i in range(n)]  # Normalize values between 0 and 1
    path['rating'] = values
    return path

def saveLoSequentialRatings(r1, output_file_name):
    r2 = r1.set_index('userId')
    dfn = pd.DataFrame(columns=['userId', 'loId', 'rating', 'timestamp'])

    for uid in r2.index.get_level_values('userId').unique():
        path = r2.loc[[uid]]  # Copy to avoid SettingWithCopyWarning
        path = new_rating(path)
        path = path.reset_index()

        dfn = pd.concat([dfn, path], ignore_index=True)

    dir = os.path.join(script_dir, 'outputs', output_file_name)
    dfn.to_csv(dir, index=None)

def save_tfidf_weight(r1, file_name):
    r_aux = r1.reset_index()

    # Calculate total visits per user
    total_visits_per_user = r_aux.groupby('userId')['rating'].transform('sum')

    # Calculate Term Frequency (TF)
    r_aux['tf'] = r_aux['rating'] / total_visits_per_user

    # Calculate Inverse Document Frequency (IDF)
    users_per_lo = r_aux.groupby('loId')['userId'].nunique()
    total_users = r_aux['userId'].nunique()
    r_aux['idf'] = np.log(total_users / users_per_lo)

    # Calculate adapted TF-IDF
    r_aux['tf_idf'] = r_aux['tf'] * r_aux['idf']

    # Calculate normalized TF-IDF weights
    tfidf = r_aux[['loId', 'tf_idf']].drop_duplicates()
    min_tfidf = tfidf['tf_idf'].min()
    max_tfidf = tfidf['tf_idf'].max()
    tfidf['tfidf_norm'] = (tfidf['tf_idf'] - min_tfidf) / (max_tfidf - min_tfidf)

    normalized_weights = tfidf[['loId', 'tfidf_norm']]
    normalized_weights.columns = ['loId', 'w']

    output_file_name = '{}/outputs/'.format(script_dir) + file_name
    normalized_weights.to_csv(output_file_name, index=None)

def saveLoData(mydf, output_file_name):
    r = mydf[['loId']]
    dir = os.path.join(script_dir, '../../moodle_logs/student_logs.csv')
    df = pd.read_csv(dir, sep=',')

    r = r.merge(df, left_on='loId', right_on='contextinstanceid', how='left')
    r = r.drop_duplicates()
    unique_tuples = r.groupby('loId').first().reset_index()
    r = unique_tuples[['loId', 'contextlevel', 'contextid']]
    r.columns = ['loId', 'title', 'category']

    dir = os.path.join(script_dir, 'outputs', output_file_name)
    r.to_csv(dir, index=None)

def prepareData():
    df_aux = getDataForRecommender()
    saveUserStandardWeight(df_aux, 'pesos_usuarios.csv')
    saveLoStandardWeight(df_aux, 'pesos_lo.csv')
    saveLoSequentialRatings(df_aux, 'Lo_ratings_seq.csv')
    saveLoData(df_aux, 'Lo_data.csv')
    # saveLoDataOrder()
