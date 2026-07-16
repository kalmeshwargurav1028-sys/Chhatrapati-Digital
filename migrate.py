import sqlite3
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv('MONGO_URI')

if not MONGO_URI:
    print("Error: MONGO_URI not found in .env")
    exit(1)

client = MongoClient(MONGO_URI)
# Use 'chhatrapati_digital' database
db = client.get_default_database()

sqlite_conn = sqlite3.connect('inquiries.db')
sqlite_conn.row_factory = sqlite3.Row
cursor = sqlite_conn.cursor()

def migrate_table(table_name):
    print(f"Migrating table: {table_name}...")
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"  Table {table_name} is empty. Skipping.")
            return

        documents = []
        for row in rows:
            doc = dict(row)
            # MongoDB uses _id instead of id. If id exists, map it or just let Mongo create _id.
            # We'll map 'id' to '_sqlite_id' to keep the relation if needed.
            if 'id' in doc:
                doc['_sqlite_id'] = doc.pop('id')
            documents.append(doc)

        # Clear existing data in collection before migrating
        db[table_name].delete_many({})
        
        # Insert new documents
        result = db[table_name].insert_many(documents)
        print(f"  Successfully migrated {len(result.inserted_ids)} records to collection '{table_name}'.")
    except sqlite3.OperationalError as e:
        print(f"  Error reading table {table_name}: {e}")

tables_to_migrate = [
    'inquiries',
    'admin_profile',
    'notifications',
    'reviews',
    'pricing_packages',
    'services',
    'portfolio',
    'our_story',
    'invoices',
    'client_tickets'
]

print("Starting migration to MongoDB Atlas...")
for table in tables_to_migrate:
    migrate_table(table)

print("\nMigration completed successfully!")
sqlite_conn.close()

# Rename the old sqlite db to back it up
os.rename('inquiries.db', 'inquiries.db.backup')
print("Backed up inquiries.db to inquiries.db.backup")
