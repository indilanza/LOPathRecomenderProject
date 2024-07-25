from preprocess_functions_moodle_server import *



df_aux=getDataForRecommender()

saveUserStandardWeight(df_aux,'pesos_usuarios.csv')

saveLoStandardWeight(df_aux,'pesos_lo.csv')

saveLoSequentialRatings(df_aux,'Lo_ratings_seq.csv')

saveLoData(df_aux,'Lo_data.csv')

saveLoDataOrder()