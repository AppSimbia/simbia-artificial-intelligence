import os
from ..repository.redis_repository import r

# Validamos o header no redis, que é atualizado por quem manda o request para API
def validate_header(header:str) -> bool:
    rediskey_auth = os.getenv("REDISKEY_AUTH")
    if not r.exists(rediskey_auth):
        return False

    auth = r.get(rediskey_auth)

    return header == auth 
