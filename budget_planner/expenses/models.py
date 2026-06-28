from expenses.database import DatabaseManager
from django.contrib.auth.hashers import make_password, check_password
from bson.objectid import ObjectId
from datetime import datetime
#structure and behaviour 

class UserModel:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.collection = self.db_manager.get_collection('users')
        if self.collection is not None:
            self.collection.create_index("email", unique=True)

    def register(self, name, email, password):
        if self.collection is None:
            return False, "Database connection error."
        if self.collection.find_one({"email": email}):
            return False, "Email already exists."
        user_data = {
            "name": name,
            "email": email,
            "password": make_password(password),
            "created_at": datetime.now()
        }
        try:
            self.collection.insert_one(user_data)
            return True, "User registered successfully."
        except Exception as e:
            return False, str(e)

    def login(self, email, password):
        if self.collection is None:
            return False, "Database connection error.", None
        user = self.collection.find_one({"email": email})
        if user and check_password(password, user['password']):
            return True, "Login successful.", user
        return False, "Invalid email or password.", None


class RecordModel:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.collection = self.db_manager.get_collection('transactions')

    def get_all(self):
        if self.collection is None:
            return []
        records = list(self.collection.find())
        # Strip the _id before turning to a pandas dataframe or dict to avoid serialization issues
        for r in records:
            if '_id' in r:
                del r['_id']
        return records

    def get_record_by_tid(self, transaction_id):
        if self.collection is None:
            return None
        record = self.collection.find_one({"Transaction_ID": transaction_id})
        if record and '_id' in record:
            del record['_id']
        return record
