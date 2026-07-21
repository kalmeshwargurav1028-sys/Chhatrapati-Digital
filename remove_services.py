import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://kalmeshwargurav1028_db_user:OzKo1PYkMjTN5xOR@cluster0.ipegkdw.mongodb.net/chhatrapati_digital?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client.chhatrapati_digital

# Remove the specific services
db.services.delete_many({"title": {"$in": ["Premium Signage (LED & 3D)", "Web Development"]}})

print("Services removed from MongoDB successfully!")
