# # src/embeddings.py
# from gensim.models import Word2Vec
# import numpy as np
# from typing import List, Dict
# from src.utils import text_to_tokens

# class W2VEmbedder:
#     def __init__(self, vector_size=100, window=5, min_count=1, epochs=50, seed=42):
#         self.vector_size = vector_size
#         self.window = window
#         self.min_count = min_count
#         self.epochs = epochs
#         self.seed = seed
#         self.model = None

#     def train(self, list_of_texts: List[str]):
#         # list_of_texts: a list where each entry is a text field (string)
#         sentences = [text_to_tokens(t) for t in list_of_texts if t and len(text_to_tokens(t))>0]
#         # filter empty
#         sentences = [s for s in sentences if s]
#         if not sentences:
#             raise ValueError("No tokens to train on.")
#         self.model = Word2Vec(
#             sentences=sentences,
#             vector_size=self.vector_size,
#             window=self.window,
#             min_count=self.min_count,
#             epochs=self.epochs,
#             seed=self.seed
#         )

#     def embed_text(self, text: str) -> np.ndarray:
#         tokens = text_to_tokens(text)
#         if not tokens:
#             return np.zeros(self.vector_size, dtype=float)
#         vecs = []
#         for t in tokens:
#             if t in self.model.wv:
#                 vecs.append(self.model.wv[t])
#         if not vecs:
#             return np.zeros(self.vector_size, dtype=float)
#         return np.mean(vecs, axis=0)



# def build_weighted_user_vector(user_data, embedder, variables):
#     """
#     Builds a single weighted average vector for a user profile.
#     Each variable's vector is weighted based on its importance.
#     """
#     all_vecs = []
#     all_weights = []

#     for v in variables:
#         key = v["key"]
#         if not v.get("use_for_embedding", True):
#             continue

#         val = user_data.get(key)
#         if not val:
#             continue

#         # Convert lists into a single string (e.g., skills, interests)
#         if isinstance(val, list):
#             text = " ".join(str(x) for x in val)
#         else:
#             text = str(val)

#         vec = embedder.embed_text(text)
#         if vec is not None:
#             all_vecs.append(vec * v["default_weight"])
#             all_weights.append(v["default_weight"])

#     if not all_vecs:
#         return np.zeros(embedder.vector_size)

#     user_vector = np.sum(all_vecs, axis=0) / np.sum(all_weights)
#     return user_vector
# src/embeddings.py
# src/embeddings.py
from gensim.models import Word2Vec
import numpy as np
from typing import List, Dict, Any
from src.utils import text_to_tokens


class W2VEmbedder:
    def __init__(
        self,
        vector_size: int = 100,
        window: int = 5,
        min_count: int = 1,
        epochs: int = 50,
        seed: int = 42,
        model: Word2Vec = None
    ):
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.epochs = epochs
        self.seed = seed
        self.model = model  # can be loaded from disk

    def train(self, list_of_texts: List[str]):
        """
        Train a Word2Vec model on a list of texts.
        Each text is tokenized via text_to_tokens.
        """
        sentences = [
            text_to_tokens(t)
            for t in list_of_texts
            if t and len(text_to_tokens(t)) > 0
        ]
        sentences = [s for s in sentences if s]  # filter empty
        if not sentences:
            raise ValueError("No tokens to train on.")
        self.model = Word2Vec(
            sentences=sentences,
            vector_size=self.vector_size,
            window=self.window,
            min_count=self.min_count,
            epochs=self.epochs,
            seed=self.seed,
        )

    def save(self, path: str):
        """Save the underlying Word2Vec model to disk."""
        if self.model is None:
            raise ValueError("No model to save.")
        self.model.save(path)

    @classmethod
    def load(cls, path: str):
        """Load a Word2Vec model from disk and wrap it in W2VEmbedder."""
        model = Word2Vec.load(path)
        vector_size = model.vector_size
        return cls(vector_size=vector_size, model=model)

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a single text as the mean of its token vectors.
        """
        tokens = text_to_tokens(text)
        if not tokens or self.model is None:
            return np.zeros(self.vector_size, dtype=float)

        vecs = []
        for t in tokens:
            if t in self.model.wv:
                vecs.append(self.model.wv[t])

        if not vecs:
            return np.zeros(self.vector_size, dtype=float)

        return np.mean(vecs, axis=0)


def build_weighted_user_vector(
    user_data: Dict[str, Any],
    embedder: W2VEmbedder,
    variables: List[Dict[str, Any]],
) -> np.ndarray:
    """
    Builds a single weighted average vector for a user profile.
    Each variable's vector is weighted based on its importance.

    user_data: dict with keys like "skills", "location", etc.
    variables: list of configs from config/variables.py
               each having at least: {"key": "...", "default_weight": float, "use_for_embedding": bool}
    """
    all_vecs = []
    all_weights = []

    for v in variables:
        key = v["key"]
        if not v.get("use_for_embedding", True):
            continue

        val = user_data.get(key)
        if val is None:
            continue

        # Convert lists into a single string (e.g., skills, interests)
        if isinstance(val, list):
            text = " ".join(str(x) for x in val)
        else:
            text = str(val)

        vec = embedder.embed_text(text)
        if vec is not None:
            weight = v.get("default_weight", 1.0)
            all_vecs.append(vec * weight)
            all_weights.append(weight)

    if not all_vecs:
        return np.zeros(embedder.vector_size, dtype=float)

    user_vector = np.sum(all_vecs, axis=0) / np.sum(all_weights)
    return user_vector
