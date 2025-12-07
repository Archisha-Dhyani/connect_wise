import os
from pinecone import Pinecone, ServerlessSpec

def ensure_index_exists(api_key: str, index_name: str, vector_dim: int, region: str):
    """
    Ensure Pinecone index exists (Pinecone v3 compatible).
    """
    pc = Pinecone(api_key=api_key)

    # List index names
    existing_indexes = pc.list_indexes().names()

    # Create index if missing
    if index_name not in existing_indexes:
        print(f"🔹 Creating Pinecone index '{index_name}'...")
        pc.create_index(
            name=index_name,
            dimension=vector_dim,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",  # or "gcp" depending on your dashboard
                region=region
            )
        )
    else:
        print(f"Index '{index_name}' already exists.")

    # Connect to index
    index = pc.Index(index_name)
    return index


def upsert_users(index, user_vectors):
    """
    user_vectors: list of dicts { "id": "user_001", "vector": [...], "metadata": {...} }
    """
    vectors_to_upsert = [
        {"id": u["id"], "values": u["vector"], "metadata": u.get("metadata", {})}
        for u in user_vectors
    ]

    index.upsert(vectors=vectors_to_upsert)
    print(f"✅ Upserted {len(vectors_to_upsert)} vectors to Pinecone.")


def query_similar(index, query_vector, top_k=5):
    """
    Returns Pinecone query results.
    """
    res = index.query(
        vector=query_vector.tolist(),
        top_k=top_k,
        include_values=False,
        include_metadata=True
    )
    return res
