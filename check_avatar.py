import os
from pymongo import MongoClient
mongo_uri = os.environ.get("MONGO_URI", "mongodb+srv://chethan:1612@cluster0.zoxmbzi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(mongo_uri)
db = client['chhatrapati_db']
profile = db.admin_profile.find_one()
if profile:
    avatar = profile.get('avatar')
    if avatar:
        print(f"Avatar is present. Length: {len(avatar)}. Starts with: {avatar[:50]}")
    else:
        print("Avatar field is missing or empty")
else:
    print("No profile found")
