import os

import pymongo
from pymongo.errors import ConnectionFailure


class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                # Use MONGODB_URI env var for production (MongoDB Atlas),
                # fall back to localhost for local development.
                mongo_uri = os.environ.get(
                    'MONGODB_URI',
                    'mongodb://localhost:27017/'
                )
                cls._instance.client = pymongo.MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=5000
                )
                cls._instance.client.admin.command('ping')
                cls._instance.db = cls._instance.client['budget_db']
                print("Connected to MongoDB successfully!")
            except ConnectionFailure:
                print("Failed to connect to MongoDB. Is MongoDB running?")
                cls._instance.db = None
            except Exception as e:
                print(f"MongoDB connection error: {e}")
                cls._instance.db = None
        return cls._instance

    def get_collection(self, collection_name):
        if self.db is not None:
            return self.db[collection_name]
        return None
