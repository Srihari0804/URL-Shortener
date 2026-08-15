import os
import redis.asyncio as redis

def get_redis():
    host = os.environ.get("REDIS_HOST", "localhost")
    port = int(os.environ.get("REDIS_PORT", 6379))
    client = redis.Redis(host=host, port=port, decode_responses=True)
    return client
