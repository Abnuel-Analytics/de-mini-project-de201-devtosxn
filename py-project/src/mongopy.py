from pymongo import MongoClient


client = MongoClient("mongodb://deuser:depass@localhost:27017/?authSource=admin")
print(client.server_info()["version"])  # → "7.x.x"
client.close()
