
# # scripts/run_pipeline.py
# import os
# import json
# import numpy as np
# from dotenv import load_dotenv
# from glob import glob
# from config.variables import VARIABLES
# from src.embeddings import W2VEmbedder, build_weighted_user_vector
# from src.pinecone_client import  upsert_users,  ensure_index_exists

# load_dotenv()

# PINE_API = os.getenv("PINECONE_API_KEY")
# PINE_ENV = os.getenv("PINECONE_ENV")
# INDEX_NAME = os.getenv("PINECONE_INDEX", "connectwise-index")
# VECTOR_DIM = int(os.getenv("VECTOR_DIM", 100))

# if not PINE_API or not PINE_ENV:
#     print("⚠️ Pinecone keys not set. You can still run word2vec training locally.")

# DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mock_users.json")


# def main():
#     # -------------------------------
#     # 1. Load user data
#     # -------------------------------
#     with open(DATA_PATH, "r", encoding="utf-8") as f:
#         users = json.load(f)

#     # -------------------------------
#     # 2. Build corpus for Word2Vec training
#     # -------------------------------
#     corpus_texts = []
#     for u in users:
#         for v in VARIABLES:
#             if v.get("use_for_embedding", True):
#                 val = u.get(v["key"])
#                 if isinstance(val, list):
#                     corpus_texts.append(" ".join(val))
#                 elif isinstance(val, str):
#                     corpus_texts.append(val)

#     # -------------------------------
#     # 3. Train Word2Vec model
#     # -------------------------------
#     embedder = W2VEmbedder(vector_size=VECTOR_DIM, epochs=60)
#     embedder.train(corpus_texts)
#     print("✅ Trained Word2Vec on mock data.")

#     # -------------------------------
#     # 4. Build weighted vectors for mock users
#     # -------------------------------
#     user_vectors = []
#     for i, u in enumerate(users):
#         vec = build_weighted_user_vector(u, embedder, VARIABLES)
#         user_vectors.append({
#             "id": f"user_{i+1}",
#             "vector": vec.tolist(),
#             "metadata": u
#         })
#     print(f"✅ Built weighted vectors for {len(user_vectors)} users.")

#     # -------------------------------
#     # 5. Pinecone upsert
#     # -------------------------------
#     if PINE_API and PINE_ENV:
#         index = ensure_index_exists(PINE_API, PINE_ENV, INDEX_NAME, VECTOR_DIM)
#         upsert_users(index, user_vectors)
#         print(f"✅ Upserted {len(user_vectors)} users to Pinecone index '{INDEX_NAME}'.")
#     else:
#         print("⚠️ Skipping Pinecone upsert because API key or env not set.")

#     # -------------------------------
#     # 6. Load most recent profile saved from app.py
#     # -------------------------------
#     profile_dir = os.path.join(os.getcwd(), "profiles")
#     profile_files = sorted(glob(os.path.join(profile_dir, "*.json")), key=os.path.getmtime, reverse=True)

#     if not profile_files:
#         print("\n⚠️ No profiles found in ./profiles/. Please run the Streamlit app first.")
#         return

#     latest_profile = profile_files[0]
#     print(f"\n📂 Found latest user profile: {os.path.basename(latest_profile)}")

#     with open(latest_profile, "r", encoding="utf-8") as f:
#         new_user = json.load(f)

#     # -------------------------------
#     # 7. Build embedding for this new user
#     # -------------------------------
#     new_vec = build_weighted_user_vector(new_user, embedder, VARIABLES)

#     # -------------------------------
#     # 8. Query Pinecone for top 3 matches
#     # -------------------------------
#     if PINE_API and PINE_ENV:
#         from src.pinecone_client import query_similar
#         top_matches = query_similar(index,new_vec, top_k=3)

#         print("\n🔍 Top 3 most similar users in the dataset:\n")
#         for match in top_matches["matches"]:
#             name = match["metadata"].get("name", "Unknown")
#             profession = match["metadata"].get("profession", "N/A")
#             score = round(match["score"], 3)
#             print(f"👤 {name} ({profession}) → Similarity: {score}")
#     else:
#         print("⚠️ Pinecone API not available. Skipping similarity query.")


# if __name__ == "__main__":
#     main()
# scripts/run_pipeline.py
import os
import json
import numpy as np
from dotenv import load_dotenv
from glob import glob
from config.variables import VARIABLES
from src.embeddings import W2VEmbedder, build_weighted_user_vector
from src.pinecone_client import upsert_users, ensure_index_exists

load_dotenv()

PINE_API = os.getenv("PINECONE_API_KEY")
PINE_ENV = os.getenv("PINECONE_ENV")
INDEX_NAME = os.getenv("PINECONE_INDEX", "connectwise-index")
VECTOR_DIM = int(os.getenv("VECTOR_DIM", 100))

if not PINE_API or not PINE_ENV:
    print("⚠️ Pinecone keys not set. You can still run word2vec training locally.")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mock_users.json")

# 🔹 NEW: where to save the trained model
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)
W2V_MODEL_PATH = os.path.join(MODELS_DIR, "w2v_connectwise.model")


def main():
    # -------------------------------
    # 1. Load user data
    # -------------------------------
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)

    # users here are already simple dicts (no ["profile"] wrapper),
    # like the JSON you sent for Priyansh, Ritika, etc.

    # -------------------------------
    # 2. Build corpus for Word2Vec training
    # -------------------------------
    corpus_texts = []
    for u in users:
        for v in VARIABLES:
            if v.get("use_for_embedding", True):
                key = v["key"]
                val = u.get(key)
                if isinstance(val, list):
                    corpus_texts.append(" ".join(str(x) for x in val))
                elif isinstance(val, str):
                    corpus_texts.append(val)
                elif isinstance(val, (int, float)):
                    corpus_texts.append(str(val))

    # -------------------------------
    # 3. Train Word2Vec model
    # -------------------------------
    embedder = W2VEmbedder(vector_size=VECTOR_DIM, epochs=60)
    embedder.train(corpus_texts)
    print("✅ Trained Word2Vec on mock data.")

    # 🔹 NEW: save the trained model
    embedder.save(W2V_MODEL_PATH)
    print(f"💾 Saved Word2Vec model to {W2V_MODEL_PATH}")

    # -------------------------------
    # 4. Build weighted vectors for mock users
    # -------------------------------
    user_vectors = []
    for i, u in enumerate(users):
        vec = build_weighted_user_vector(u, embedder, VARIABLES)
        user_vectors.append({
            "id": f"user_{i+1}",
            "vector": vec.tolist(),
            "metadata": u
        })
    print(f"✅ Built weighted vectors for {len(user_vectors)} users.")

    # -------------------------------
    # 5. Pinecone upsert
    # -------------------------------
    if PINE_API and PINE_ENV:
        index = ensure_index_exists(PINE_API, PINE_ENV, INDEX_NAME, VECTOR_DIM)
        upsert_users(index, user_vectors)
        print(f"✅ Upserted {len(user_vectors)} users to Pinecone index '{INDEX_NAME}'.")
    else:
        print("⚠️ Skipping Pinecone upsert because API key or env not set.")


if __name__ == "__main__":
    main()
