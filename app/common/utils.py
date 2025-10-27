
import math

# Calcula distancia fisica basiada em latitude e longitude
def get_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # raio da Terra em km

    # converte graus para radianos
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c
