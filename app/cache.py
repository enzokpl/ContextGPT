# cache.py
import redis
from .config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD


class RedisCache:
    def __init__(self):
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.redis.close()

    def set(self, key, value, ex=None):  # ex é o tempo de expiração em segundos
        self.redis.set(key, value, ex=ex)

    def get(self, key):
        return self.redis.get(key)

    def delete(self, key):
        self.redis.delete(key)
