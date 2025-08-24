import os
from ..repository.redis_repository import r

def valida_header(header:str) -> bool:
    rediskey_auth = os.getenv("REDISKEY_AUTH")
    if not r.exists(rediskey_auth):
        return False

    auth = r.get(rediskey_auth)

    return header == auth 
