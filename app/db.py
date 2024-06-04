from pymongo import MongoClient
from .config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME


class MongoDBConnector:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()

    def insert_or_update_document(self, data):
        self.collection.update_one({'file_path': data['file_path']}, {'$set': data}, upsert=True)

    def get_document(self, file_path):
        return self.collection.find_one({'file_path': file_path})

    def delete_document(self, file_path):
        self.collection.delete_one({'file_path': file_path})

    def find_relevant_embeddings(self, query_embedding, top_n=5):
        pipeline = [
            {
                '$project': {
                    'file_path': 1,
                    'similarity': {
                        '$function': {
                            'body': """function(embedding, query_embedding) {
                                const dotProduct = embedding.reduce((sum, a, idx) => sum + a * query_embedding[idx], 0);
                                const normA = Math.sqrt(embedding.reduce((sum, a) => sum + a * a, 0));
                                const normB = Math.sqrt(query_embedding.reduce((sum, a) => sum + a * a, 0));
                                return dotProduct / (normA * normB);
                            }""",
                            'args': ['$embedding', query_embedding],
                            'lang': 'js'
                        }
                    }
                }
            },
            {
                '$sort': {'similarity': -1}
            },
            {
                '$limit': top_n
            }
        ]
        results = list(self.collection.aggregate(pipeline))
        return [(doc['file_path'], doc['similarity']) for doc in results]
