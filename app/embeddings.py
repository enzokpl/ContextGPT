# embeddings.py
import numpy as np
from .config import client


def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding


def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)


def find_most_relevant_embeddings(query_embedding, embeddings, top_n=5):
    similarities = [(file_path, cosine_similarity(query_embedding, emb)) for file_path, emb in embeddings.items()]
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_n]
