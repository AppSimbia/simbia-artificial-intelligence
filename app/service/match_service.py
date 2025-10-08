from typing import List

from ..repository import postgres_repository
from ..common.utils import get_distance
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from kneed import KneeLocator

import pandas as pd

import os

from ..repository.redis_repository import r

def list_posts() -> pd.DataFrame:
    query = "SELECT * FROM VW_PostList LIMIT 100;"
    conn, cursor = postgres_repository.open_connection()
    df = pd.read_sql_query(query, conn)
    cursor.close()
    conn.close()
    return df

def get_data(category_id: int, quantity: int, measure_unit: int, industry_id:int) -> pd.DataFrame:
    conn, cursor = postgres_repository.open_connection()
    query = "SELECT ccategoryname FROM productcategory WHERE idproductcategory = %s;"
    cursor.execute(query, (category_id,))
    category = cursor.fetchone()[0]

    query2 = "SELECT nlatitude, nlongitude, cindustrytypename FROM industry i JOIN industrytype it ON it.idindustrytype = i.idindustrytype WHERE idindustry = %s;"
    cursor.execute(query2, (industry_id,))
    data = cursor.fetchone()
    latitude = data[0]
    longitude = data[1]
    industry_type = data[2]

    data_dict = {
        "ccategoryname": [str(category)],
        "cindustrytypename": [str(industry_type)],
        "nlatitude": [float(latitude)],
        "nlongitude": [float(longitude)],
        "nquantity": [int(quantity)],
        "cmeasureunit": [str(measure_unit)]
    }

    return pd.DataFrame(data_dict)

def get_weights(df: pd.DataFrame) -> dict:
    weights = {}

    for c in df.columns:
        if c.startswith("ccategoryname_"):
            weights[c] = 1.7
        if c.startswith("cindustrytypename_"):
            weights[c] = 0.5
        if c.startswith("cindustrytypename_"):
            weights[c] = 0.5


    weights["distance"] = 1.5
    weights["nquantity"] = 1

    return weights

def format_data(df: pd.DataFrame, user_search: pd.DataFrame): 
    nlatitude = user_search["nlatitude"]
    nlongitude = user_search["nlongitude"]
    df["distance"] = df.apply(
        lambda x: get_distance(float(x["nlatitude"]), float(x["nlongitude"]), float(nlatitude.iloc[0]), float(nlongitude.iloc[0])),
        axis=1
    )
    user_search["distance"] = 0

    df = df.drop(columns=["nlatitude","nlongitude"])
    user_search = user_search.drop(columns=["nlatitude","nlongitude"])

    df_dummies = pd.get_dummies(df, columns=["ccategoryname","cindustrytypename","cmeasureunit"], dtype=int)
    user_search_dummies = pd.get_dummies(user_search, columns=["ccategoryname","cindustrytypename","cmeasureunit"], dtype=int)
    user_search_dummies = user_search_dummies.reindex(columns=df_dummies.columns, fill_value=0)
    scaler = MinMaxScaler()
    scaler.fit(df_dummies[["nquantity","distance"]])
    df_dummies[["nquantity","distance"]] = scaler.transform(df_dummies[["nquantity","distance"]])
    user_search_dummies[["nquantity","distance"]] = scaler.transform(user_search_dummies[["nquantity","distance"]])
    df_dummies = df_dummies.drop(columns=["idpost"])
    user_search_dummies = user_search_dummies.drop(columns=["idpost"])

    weights = get_weights(df_dummies)

    for col, peso in weights.items():
        df_dummies[col] = df_dummies[col] * peso
        user_search_dummies[col] = user_search_dummies[col] * peso

    return df_dummies, user_search_dummies

def get_knee(df: pd.DataFrame) -> int:
    r.flushall()
    # Vendo se o k está no redis
    redis_elbow_key = os.getenv("REDISKEY_ELBOW")
    if len(df) < 10:
        knee = 1
    # Vendo se o k está no redis
    elif r.exists(redis_elbow_key) and int(r.get(redis_elbow_key)) <= len(df):
        knee = int(r.get(redis_elbow_key))
    else:
        # Decidindo o K baseando-se no método do cotovelo
        inertia = []

        max = 40
        if len(df) < 40:
            max = len(df)+1
        Ks = range(1, max, 1)
        for k in Ks:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(df)
            inertia.append(kmeans.inertia_)

        knee = KneeLocator(Ks, inertia, curve='convex', direction='decreasing')
        knee = knee.knee
        r.set(redis_elbow_key, str(knee), ex=86400)

    return knee    

def get_distances(df: pd.DataFrame, user_search: pd.DataFrame):
    cols = list(df.columns)
    ref = user_search.iloc[0]

    distances = [
        sum(((row[c] - ref[c]))**2 for c in cols) ** 0.5
        for _, row in df.iterrows()
    ]
    return distances

def return_suggestion(user_data: dict):
    df_posts = list_posts()
    user_search = get_data(user_data["category_id"], user_data["quantity"], user_data["measure_unit"], user_data["industry_id"])

    df_formatted, user_search_formatted = format_data(df_posts, user_search)
    knee = get_knee(df_formatted)

    kmeans = KMeans(n_clusters=knee, random_state=42, n_init=10)
    resultado = kmeans.fit_predict(df_formatted)
    df_posts["cluster"] = resultado
    df_formatted["cluster"] = resultado

    user_cluster = kmeans.predict(user_search_formatted)

    # Filtrando o df para termos apenas os que estão no cluster
    df_posts = df_posts[(df_posts["cluster"] == user_cluster[0])]
    df_formatted = df_formatted[(df_formatted["cluster"] == user_cluster[0])]
    df_formatted = df_formatted.drop(columns=["cluster"])

    df_posts["distance_to_search"] = get_distances(df_formatted, user_search_formatted)
    df_posts = df_posts.sort_values(by=["distance_to_search"]) 
    return list(df_posts["idpost"])
    