from pymongo import MongoClient

class DbProvider:

    def __init__(self):
        self.client = MongoClient(host='localhost',
                                  port=27017,
                                  username='admin',
                                  password='password',
                                  authSource='admin')
        self.db = self.client['file_archive']
        self.collection = self.db['files']
    
    def provide_to_database(self, data):
        if self.collection.count_documents({'tagID': data.get('tagID')}, limit = 1):
            print('File exists in database')
        else:
            self.collection.insert_one(data)