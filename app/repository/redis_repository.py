import redis
import os

connection_url = os.getenv("REDIS_URL")

r = redis.from_url(connection_url, decode_responses=True)
