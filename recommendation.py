import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
pd.options.mode.chained_assignment = None  # default='warn'
from sklearn.metrics.pairwise import linear_kernel
from datetime import datetime, date, time, timedelta
import psycopg2 as ps
import json

def get_recommendations(event):
    host_name = 'database-instance-seatgeek.cu6ka4nizuqr.us-east-1.rds.amazonaws.com'
    dbname = 'seatgeek_database'
    port = '5432'
    username = 'katya_admin'
    password = 'Katya123'
    conn = None
    curr = None

    def connect_to_db(host_name, dbname, port, username, password):
        try:
            conn = ps.connect(host=host_name, database=dbname, user=username, password=password, port=port)
        except ps.OperationalError as e:
            raise e
        else:
            print('Connected!')
        return conn
    
    conn = connect_to_db(host_name, dbname, port, username, password)
    curr = conn.cursor()

    current_date = datetime.now()

    # retrieve the records from the database
    future_events = pd.read_sql(""" SELECT event_id, event, borough, state, venue, img_link, full_date, full_tag FROM events100 WHERE full_date >= current_date""", conn, coerce_float=False)

    conn.commit()
    curr.close()
    conn.close()
    ##############################################################################

    future_events = future_events.sort_values(by ='full_date', ignore_index=True)
    future_events = future_events.drop_duplicates(subset=['event'], keep='first')
    indices = pd.Series(future_events.index, index=future_events['event']).drop_duplicates()


    tfidf = TfidfVectorizer(stop_words="english")
    tfidf_matrix = tfidf.fit_transform(future_events['full_tag'])
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
    indices = pd.Series(future_events.index, index=future_events['event']).drop_duplicates()

    def get_event_recommendations(event):
        idx = indices[event]
        sim_scores = enumerate(cosine_sim[idx])
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:9]
        sim_index = [i[0] for i in sim_scores]

        df = future_events.iloc[sim_index]
        df = df[['event_id','event','borough','state','venue','img_link','full_date']]
        #print(df)
        rec_json = df.to_json(orient='records', double_precision=0, date_format='iso')
        #print(rec_json)
        #rec_json2 = json.dumps(json.loads(rec_json))
        rec_json2 = json.loads(rec_json)

        #print(rec_json2)
        return rec_json2

    response = get_event_recommendations(event)
    return response
    



    #get_recommendations('The Lion King ')