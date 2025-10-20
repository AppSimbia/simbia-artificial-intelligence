from pymongo import MongoClient
import os


MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")
 
client = MongoClient(MONGODB_URL)
db = client[MONGODB_DB_NAME]


def get_collection(env_name: str):
    return db[os.getenv(env_name)]