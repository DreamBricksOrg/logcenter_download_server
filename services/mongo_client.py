import logging

from pymongo import MongoClient
from pymongo.errors import PyMongoError

import config

logger = logging.getLogger(__name__)

_client = None


class MongoConnectionError(RuntimeError):
    pass


def get_client():
    global _client
    if _client is None:
        if not config.MONGODB_URI:
            raise MongoConnectionError("MONGODB_URI não configurado.")
        logger.info("Connecting to MongoDB Atlas...")
        _client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client


def run_aggregation(stages):
    logger.info(
        "Running aggregation on db=%r collection=%r (%d stage(s))",
        config.DB_NAME, config.COLLECTION_NAME, len(stages),
    )
    try:
        client = get_client()
        collection = client[config.DB_NAME][config.COLLECTION_NAME]
        rows = list(collection.aggregate(stages))
        logger.info(
            "Aggregation on db=%r collection=%r returned %d document(s)",
            config.DB_NAME, config.COLLECTION_NAME, len(rows),
        )
        return rows
    except PyMongoError as exc:
        logger.error(
            "PyMongo error on db=%r collection=%r: %s",
            config.DB_NAME, config.COLLECTION_NAME, exc, exc_info=True,
        )
        raise MongoConnectionError(
            "Não foi possível conectar ao MongoDB Atlas. Verifique MONGODB_URI."
        ) from exc
