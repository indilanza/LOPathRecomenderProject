from preprocess_functions import *

#logs_file='data/logs_EI1013-MT1013-20212022_20240403-1239.csv' #Logs matematica computacional
logs_file='data/logs_VJ1214-20232024_20231103-1049.csv' #logs Raul
#logs_file='data/logs_PHB001-20222023_20240503-1001.csv' #logs asigntura captura y almacenamiento de datos

#quitar los usuarios profesores
"""
Indira Lanza   id 107743
Carlos Marin Lora  id 135774
Begoña Martínez Salvador   id 6687
Antonio Morales Escrig    id 7711
"""
#lecturer_list=['107743','135774','6687','7711'] #profesores de la asignatura matematica computacional
lecturer_list=['19762','16212']
#lecturer_list=['107743','6686','17715'] #profesores de la asignatura captura y almacenamiento de datos
preprocessAndSave(logs_file, lecturer_list)

[df,df_loData]=getDataForRecommender()

saveUserStandardWeight(df,'pesos_usuarios.csv')

saveLoStandardWeight(df,'pesos_lo.csv')

saveLoSequentialRatings(df,'Lo_ratings_seq.csv')

saveLoData(df_loData,'Lo_data.csv')

saveLoDataOrder()