from pymongo import MongoClient
from pymongo.errors import PyMongoError

import config

_client = None


class MongoConnectionError(RuntimeError):
    pass


def get_client():
    global _client
    if _client is None:
        if not config.MONGODB_URI:
            raise MongoConnectionError("MONGODB_URI não configurado.")
        _client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client


def run_aggregation(stages):
    try:
        client = get_client()
        collection = client[config.DB_NAME][config.COLLECTION_NAME]
        return list(collection.aggregate(stages))
    except PyMongoError as exc:
        raise MongoConnectionError(
            "Não foi possível conectar ao MongoDB Atlas. Verifique MONGODB_URI."
        ) from exc
