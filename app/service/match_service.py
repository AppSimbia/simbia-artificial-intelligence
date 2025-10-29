from typing import List

from ..repository import postgres_repository
from ..common.utils import get_distance
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from kneed import KneeLocator

import pandas as pd

import os

from ..repository.redis_repository import r

# Retorna todos os posts
def list_posts(id_industry) -> pd.DataFrame:
    query = """SELECT idpost,
                ccategoryname,
                cindustrytypename,
                nlatitude,
                nlongitude,
                nquantity,
                cmeasureunit
             FROM VW_PostList
            WHERE idIndustry <> %s;"""
    conn, cursor = postgres_repository.open_connection()
    df = pd.read_sql_query(query, conn, params=(id_industry,))
    cursor.close()
    conn.close()
    df = df.dropna()
    if len(df) == 0:
        raise Exception("Não há dados o suficiente para realizar a busca.")
    return df

# Baseado no Input, gera uma linha com dados iguais o do DataFrame de posts
def get_data(category_id: int, quantity: int, measure_unit: int, industry_id:int) -> pd.DataFrame:
    try:

        conn, cursor = postgres_repository.open_connection()
        query = "SELECT ccategoryname FROM productcategory WHERE idproductcategory = %s;"
        cursor.execute(query, (category_id,))
        category = cursor.fetchone()[0]

        if not category:
            raise Exception("Não há dados o suficiente para realizar a busca.")

        query2 = "SELECT nlatitude, nlongitude, cindustrytypename FROM industry i JOIN industrytype it ON it.idindustrytype = i.idindustrytype WHERE idindustry = %s;"
        cursor.execute(query2, (industry_id,))
        data = cursor.fetchone()
        latitude = data[0]
        longitude = data[1]
        industry_type = data[2]

        if not latitude or not longitude or not industry_type:
            raise Exception("Não há dados o suficiente para realizar a busca.")

        data_dict = {
            "ccategoryname": [str(category)],
            "cindustrytypename": [str(industry_type)],
            "nlatitude": [float(latitude)],
            "nlongitude": [float(longitude)],
            "nquantity": [int(quantity)],
            "cmeasureunit": [str(measure_unit)]
        }

        return pd.DataFrame(data_dict)
    except Exception as e:
        raise Exception("Não há dados o suficiente para realizar a busca.")

# Retorna os pesos de cada coluna
def get_weights(df: pd.DataFrame) -> dict:
    # Esses pesos foram decididos baseados em nossa regra de negócio
    # Acreditamos que para a indústria, é mais importante que a categoria escolhida seja a que apareça principalmente, focando depois na distância física, por questões de logística.
    # A quantidade e a unidade de medida mantem um valor padrão, pois a distância pode fugir do desejado, mas não muito
    # Por fim, o tipo de industria é o menos relevante, sendo apenas para desempate, pois tipos de industria diferentes podem vender coisas iguais
    weights = {}

    for c in df.columns:
        if c.startswith("ccategoryname_"):
            weights[c] = 1.7
        if c.startswith("cindustrytypename_"):
            weights[c] = 0.5
        if c.startswith("cmeasureunit_"):
            weights[c] = 0.5


    weights["distance"] = 1.5
    weights["nquantity"] = 1

    return weights

# Pego os dois DataFrames e trato eles para serem usados nos modelos
def format_data(df: pd.DataFrame, user_search: pd.DataFrame): 
    # Pego a latitude e a longitude da industria e calculo a distancia fisica dela para todas as outras
    nlatitude = user_search["nlatitude"]
    nlongitude = user_search["nlongitude"]
    df["distance"] = df.apply(
        lambda x: get_distance(float(x["nlatitude"]), float(x["nlongitude"]), float(nlatitude.iloc[0]), float(nlongitude.iloc[0])),
        axis=1
    )
    user_search["distance"] = 0

    # Agora que já usei, removo as colunas de latitude e longitude
    df = df.drop(columns=["nlatitude","nlongitude"])
    user_search = user_search.drop(columns=["nlatitude","nlongitude"])

    # Pego os dummies das colunas categoricas
    df_dummies = pd.get_dummies(df, columns=["ccategoryname","cindustrytypename","cmeasureunit"], dtype=int)
    user_search_dummies = pd.get_dummies(user_search, columns=["ccategoryname","cindustrytypename","cmeasureunit"], dtype=int)
    user_search_dummies = user_search_dummies.reindex(columns=df_dummies.columns, fill_value=0)
    # Passo os valores numéricos no min max scaler
    scaler = MinMaxScaler()
    scaler.fit(df_dummies[["nquantity","distance"]])
    df_dummies[["nquantity","distance"]] = scaler.transform(df_dummies[["nquantity","distance"]])
    user_search_dummies[["nquantity","distance"]] = scaler.transform(user_search_dummies[["nquantity","distance"]])

    # Removo o id do post
    df_dummies = df_dummies.drop(columns=["idpost"])
    user_search_dummies = user_search_dummies.drop(columns=["idpost"])

    # Pego o peso e aplico para cada coluna
    weights = get_weights(df_dummies)

    for col, peso in weights.items():
        df_dummies[col] = df_dummies[col] * peso
        user_search_dummies[col] = user_search_dummies[col] * peso

    return df_dummies, user_search_dummies

# Aqui descubro o melhor K para o Kmeans
def get_knee(df: pd.DataFrame) -> int:
    redis_elbow_key = os.getenv("REDISKEY_ELBOW")
    # Se não tiver 10 dados, eu escolho 1 como K, para evitar gastar processamento
    if len(df) < 10:
        knee = 1
    # Vendo se o k já está no redis
    elif r.exists(redis_elbow_key) and int(r.get(redis_elbow_key)) <= len(df):
        knee = int(r.get(redis_elbow_key))
    else:
        # Decidindo o K baseando-se no método do cotovelo
        inertia = []

        # O máximo que eu vou chutar para K é 40
        max = 40
        
        # Caso tenha menos de 40 eu pego o tamanho do df + 1
        if len(df) < max:
            max = len(df)+1
        Ks = range(1, max, 1)
        for k in Ks:
            # Rodo o Kmeans e pego a inertia para fazer o cotovelo
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(df)
            inertia.append(kmeans.inertia_)

        # Passo o KneeLocator para decidir de vez o cotovelo
        knee = KneeLocator(Ks, inertia, curve='convex', direction='decreasing')
        knee = knee.knee

        # Guardando esse valor no Redis por um dia, para economizarmos memória
        r.set(redis_elbow_key, str(knee), ex=86400)

    return knee    

# Aqui eu aplico a fórmula da distância Euclidiana e retorno os valores
def get_distances(df: pd.DataFrame, user_search: pd.DataFrame):
    cols = list(df.columns)
    ref = user_search.iloc[0]

    distances = [
        sum(((row[c] - ref[c]))**2 for c in cols) ** 0.5
        for _, row in df.iterrows()
    ]
    return distances

def return_suggestion(user_data: dict):
    # 1. Listamos os posts e pegamos os dados do usuário
    df_posts = list_posts(user_data["industry_id"])
    user_search = get_data(user_data["category_id"], user_data["quantity"], user_data["measure_unit"], user_data["industry_id"])

    # 2. Formatamos os dados do usuário para o Kmeans
    df_formatted, user_search_formatted = format_data(df_posts, user_search)

    # 3. Pegamos o melhor K para os dados
    knee = get_knee(df_formatted)

    # 4. Treinamos o KMeans para separar os posts em vários clusters
    # O KMeans foi escolhido porque ele separa os valores em N clusters baseando-se na distância e no KNN, ele cria os próprios 
    # clusters, já que eu não tenho uma categoria fixa e minha intenção não é categorizar, eu uso ele. Dai ele me retorna o 
    # cluster e eu uso apenas os posts naquele cluster para a sugestão
    kmeans = KMeans(n_clusters=knee, random_state=42, n_init=10)
    resultado = kmeans.fit_predict(df_formatted)
    df_posts["cluster"] = resultado
    df_formatted["cluster"] = resultado

    # 5. Decidimos o cluster do dado do usuário
    user_cluster = kmeans.predict(user_search_formatted)

    # 6. Filtramos o df para termos apenas os que estão no cluster
    df_posts = df_posts[(df_posts["cluster"] == user_cluster[0])]
    df_formatted = df_formatted[(df_formatted["cluster"] == user_cluster[0])]
    df_formatted = df_formatted.drop(columns=["cluster"])

    # 7. Calculamos a distancia euclidiana e ordenamos por ela para retornarmos
    # Aqui eu já tenho menos dados do que todos os posts, agora eu quero sugerir eles em ordem, para quem usar a API consegui 
    # mostrar o top N que quiser. Uso a distância euclidiana, calculando baseando-se em todas as colunas.
    # Com isso, eu tenho apenas os posts mais próximos do usuário e ainda ordenados entre eles, nisso, quem consome a API tem a 
    # liberdade de escolher quantos dados do retorno irá utilizar.
    df_posts["distance_to_search"] = get_distances(df_formatted, user_search_formatted)
    df_posts = df_posts.sort_values(by=["distance_to_search"]) 
    return list(df_posts["idpost"])

# Para a validação cruzada, a avaliação do modelo e a métrica, seriam necessários dados de teste e o único jeito de eu testar se 
# a recomendação está realmente boa seria tendo os dados do uso do usuário no aplicativo. Por conta disso, não é possível avaliar 
# se o modelo realmente está funcionando ou não enquanto não tivermos alguns dados de uso do aplicativo.
# Como o objetivo aqui é retornar apenas uma sugestão de Post para o usuário, precisariamos validar, olhando a interação dele 
# (curtidas, matchs, etc) com os Posts sugeridos e ver qual a opção que gera melhores interações e prende mais o usuário, 
# aumentando a chance dele de realizar o match (objetivo principal do aplicativo)
# Para o futuro do aplicativo, podemos fazer testes com os usuários, mudando os parâmetros e os modelos e vendo as preferencias e
# quais trazem melhores resultados