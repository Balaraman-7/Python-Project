import os

import dns.resolver
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


# Default MongoDB Atlas connection string
# Override with the MONGODB_URI environment variable if needed
ATLAS_DEFAULT_URI = (
    "mongodb+srv://balaraman07:bala07@cluster0.ceyy3m0.mongodb.net/"
    "budget_planner?retryWrites=true&w=majority&appName=Cluster0"
)


class DatabaseManager:
    _instance = None

    def __new__(cls):
        # Reset instance if previous connection failed (db is None)
        if cls._instance is not None and cls._instance.db is None:
            cls._instance = None

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                # Override DNS to use Google's public DNS (fixes restrictive networks/mobile hotspots)
                dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
                dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4', '1.1.1.1']

                # Use MONGODB_URI env var if set, otherwise use Atlas default
                mongo_uri = os.environ.get('MONGODB_URI', ATLAS_DEFAULT_URI)
                cls._instance.client = pymongo.MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=10000
                )
                # Verify the connection
                cls._instance.client.admin.command('ping')
                # Use 'budget_planner' database (matches Atlas URI)
                cls._instance.db = cls._instance.client['budget_planner']
                print("[OK] Connected to MongoDB Atlas successfully!")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                print(f"[ERROR] Failed to connect to MongoDB Atlas: {e}")
                cls._instance.db = None
            except Exception as e:
                print(f"[ERROR] MongoDB connection error: {e}")
                cls._instance.db = None
        return cls._instance

    def get_collection(self, collection_name):
        if self.db is not None:
            return self.db[collection_name]
        return None
