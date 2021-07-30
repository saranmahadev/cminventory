import datetime
import json
import pymongo

class Db:
    def __enter__(self): 
        print('Database Connection Opened @ {now}'.format(now = datetime.datetime.now())) 
        return self

    def __init__(self,collection):
        with open("credentials.json",'r') as c:
            cred = json.load(c)   
            self.client = pymongo.MongoClient("mongodb+srv://{user}:{password}@cluster0.ulvmw.mongodb.net/myFirstDatabase?retryWrites=true&w=majority".format(user = cred["dbUser"],password = cred["dbPassword"]))
        self.db = self.client["inventory"]
        self.collection = self.db[collection]
   
    def __str__(self):
        return "Database connection"

    def __repr__(self):
        return "Database connection"
    
    def insert(self,data):
        self.collection.insert_one(data)

    def find(self,query):
        return self.collection.find(query)

    def all(self):
        return self.collection.find()

    def update(self,query,data):
        return self.collection.update_one(query,data)

    def delete(self,query):
        return self.collection.delete_one(query)
        
    def __exit__(self,exc_type, exc_value, exc_traceback):
        print("Database Connection Closed @ {now}".format(now = datetime.datetime.now()))
        self.client.close()
