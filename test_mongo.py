import certifi
from pymongo import MongoClient
import json

import os
from dotenv import load_dotenv

load_dotenv()
ca = certifi.where()
uri = os.environ.get("MONGO_URI")
client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=ca)
try:
    client.server_info()
    print(json.dumps({"status": "SUCCESS"}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
