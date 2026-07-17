import os
from pymongo import MongoClient

mongo_uri = os.environ.get("MONGO_URI", "mongodb+srv://chethan:1612@cluster0.zoxmbzi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(mongo_uri)
db = client['chhatrapati_db']

collections = db.list_collection_names()
for coll_name in collections:
    docs = db[coll_name].find({"$text": {"$search": "logo"}})
    count = 0
    for _ in docs:
        count += 1
    if count > 0:
        print(f"Found 'logo' in {coll_name}")

print("Check completed.")
