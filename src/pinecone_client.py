# src/pinecone_client.py

import os
from pinecone import Pinecone, ServerlessSpec

def init_pinecone(api_key: str, environment: str, index_name: str, dimension: int):
    pc = Pinecone(api_key=api_key)

    # check if index already exists
    existing_indexes = [idx["name"] for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"Creating new Pinecone index '{index_name}'...")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=environment)
        )
    else:
        print(f"Index '{index_name}' already exists.")

    # connect to it
    index = pc.Index(index_name)
    return index

def upsert_users(index, user_vectors):
    """
    user_vectors: list of dicts { "id": "user_001", "vector": [..], "metadata": {...} }
    """
    vectors_to_upsert = [
        {"id": u["id"], "values": u["vector"], "metadata": u.get("metadata", {})}
        for u in user_vectors
    ]
    index.upsert(vectors=vectors_to_upsert)
    print(f"✅ Upserted {len(vectors_to_upsert)} vectors to Pinecone.")

def query_similar(index, query_vector, top_k=5):
    res = index.query(
        vector=query_vector.tolist(),
        top_k=top_k,
        include_values=False,
        include_metadata=True
    )
    return res
from pinecone import Pinecone

def ensure_index_exists(api_key, environment, index_name, vector_dim):
    pc = Pinecone(api_key=api_key)

    # Check if index already exists
    if not pc.has_index(index_name):
        print(f"Creating Pinecone index '{index_name}'...")
        pc.create_index(
            name=index_name,
            dimension=vector_dim,
            metric="cosine",
            spec={
                "serverless": {
                    "cloud": "aws",
                    "region": environment
                }
            }
        )
        print(f"Index '{index_name}' created successfully!")
    else:
        print(f"Index '{index_name}' already exists.")

    # Return a handle to the index
    return pc.Index(index_name)
