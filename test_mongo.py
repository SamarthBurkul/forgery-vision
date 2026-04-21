import certifi
from pymongo import MongoClient
import json

ca = certifi.where()
uri = "mongodb+srv://samarthburkul67_db_user:N4J8vQiYjHcGFsuT@cluster0.rld51zf.mongodb.net/forensicai?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=ca)
try:
    client.server_info()
    print(json.dumps({"status": "SUCCESS"}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
