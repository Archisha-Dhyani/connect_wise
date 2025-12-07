# api_main.py
import os
import uuid   # 🔹 ADD THIS
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np

from config.variables import VARIABLES
from src.embeddings import W2VEmbedder, build_weighted_user_vector
from src.pinecone_client import ensure_index_exists, query_similar, upsert_users  # 🔹 ADD upsert_users



def sanitize_metadata(raw_meta: dict) -> dict:
    """
    Pinecone requires metadata values to be:
    - string
    - number
    - boolean
    - list of strings

    This function:
    - drops None values
    - converts lists to list of strings
    - converts other non-primitive types to strings
    """
    clean = {}
    for k, v in raw_meta.items():
        # skip None/null
        if v is None:
            continue

        # lists -> list of strings
        if isinstance(v, list):
            clean[k] = [str(x) for x in v]
        # primitives allowed as-is
        elif isinstance(v, (str, int, bool)):
            clean[k] = v
        elif isinstance(v, float):
            clean[k] = float(v)  # ensure proper conversion

        else:
            clean[k] = str(v)

    return clean


# ----------------- Load env -----------------
load_dotenv()

PINE_API = os.getenv("PINECONE_API_KEY")
PINE_ENV = os.getenv("PINECONE_ENV")
INDEX_NAME = os.getenv("PINECONE_INDEX", "connectwise-index")
VECTOR_DIM = int(os.getenv("VECTOR_DIM", 100))

# Path to trained W2V model
BASE_DIR = os.path.dirname(__file__)
W2V_MODEL_PATH = os.path.join(BASE_DIR, "models", "w2v_connectwise.model")

# ----------------- FastAPI app -----------------
app = FastAPI(title="ConnectWise Matching API")

# CORS (so frontend can call this from another port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in prod, restrict to specific frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Pydantic models -----------------

class ProfilePayload(BaseModel):
    profile: dict
    saved_at: str | None = None
    version: str | None = None


# ----------------- Global objects (start-up) -----------------

if not os.path.exists(W2V_MODEL_PATH):
    raise RuntimeError(f"Word2Vec model not found at {W2V_MODEL_PATH}. Run scripts/run_pipeline.py first.")

if not PINE_API or not PINE_ENV:
    raise RuntimeError("Pinecone API key or environment not configured in .env.")

# load W2V model
EMBEDDER = W2VEmbedder.load(W2V_MODEL_PATH)
print("✅ Loaded Word2Vec model.")

# connect / create Pinecone index
INDEX = ensure_index_exists(PINE_API, INDEX_NAME, VECTOR_DIM, PINE_ENV)
print(f"✅ Connected to Pinecone index '{INDEX_NAME}'.")


# ----------------- Routes -----------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "index": INDEX_NAME,
        "vector_dim": VECTOR_DIM
    }


@app.post("/match-users")
def match_users(payload: ProfilePayload):
    try:
        user_data = payload.profile  # this is exactly your profile dict from frontend

        # embed new profile
        vec = build_weighted_user_vector(user_data, EMBEDDER, VARIABLES)

        if not np.any(vec):  # all zeros
            raise HTTPException(status_code=400, detail="Could not build a meaningful vector from profile.")

        # query pinecone
        res = query_similar(INDEX, vec, top_k=3)

        # res is a dict-like: {"matches": [...]}
        matches = []
        for m in res["matches"]:
            matches.append({
                "id": m["id"],
                "score": float(m["score"]),
                "metadata": m.get("metadata", {})
            })

        return {"matches": matches}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/register-and-match")
def register_and_match(payload: ProfilePayload):
    """
    1. Embed the incoming profile
    2. Store (upsert) it as a new user in Pinecone
    3. Query Pinecone for similar users
    4. Return the new user's ID + list of matches (excluding themself)
    """
    try:
        user_data = payload.profile  # the profile dict from frontend

        # 1) Embed the new profile
        vec = build_weighted_user_vector(user_data, EMBEDDER, VARIABLES)
        if not np.any(vec):  # all zeros
            raise HTTPException(status_code=400, detail="Could not build a meaningful vector from profile.")

        # 2) Create a unique user ID
        user_id = f"user_{uuid.uuid4().hex}"

        # 3) Upsert this new user into Pinecone
        # Flatten metadata: include profile fields + saved_at/version if provided
                # raw metadata: profile + optional saved_at/version
        raw_metadata = {
            **user_data,
        }
        if payload.saved_at is not None:
            raw_metadata["saved_at"] = payload.saved_at
        if payload.version is not None:
            raw_metadata["version"] = payload.version

        # 🔹 sanitize for Pinecone
        metadata = sanitize_metadata(raw_metadata)

        user_doc = {
            "id": user_id,
            "vector": vec.tolist(),
            "metadata": metadata,
        }


        # Reuse existing helper
        upsert_users(INDEX, [user_doc])

        # 4) Query Pinecone for similar users
        # You can tune top_k as you like
        res = query_similar(INDEX, vec, top_k=10)

        # 5) Build matches list and exclude the new user itself (if returned)
        matches = []
        for m in res["matches"]:
            if m["id"] == user_id:
                continue  # skip self
            matches.append({
                "id": m["id"],
                "score": float(m["score"]),
                "metadata": m.get("metadata", {}),
            })

        return {
            "user_id": user_id,
            "matches": matches,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
