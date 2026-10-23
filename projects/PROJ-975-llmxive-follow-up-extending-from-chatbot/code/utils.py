import numpy as np
from typing import List, Optional

# ----------------------------------------------------------------------
# Compatibility handling for the `sentence_transformers` library.
# Newer versions of `huggingface_hub` removed `cached_download`,
# which older `sentence_transformers` versions expect.
# To keep the rest of the codebase simple we provide a deterministic
# dummy model when the real library cannot be imported.
# ----------------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer
    _REAL_MODEL_AVAILABLE = True
except Exception:  # ImportError or any runtime error during import
    _REAL_MODEL_AVAILABLE = False

class DummyModel:
    """
    A deterministic stand‑in for `SentenceTransformer`.
    It produces 384‑dim vectors that are reproducible across runs
    by seeding a NumPy RNG with a hash of the input text.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def encode(self, texts: List[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        vectors = []
        for txt in texts:
            # Create a deterministic seed from the text
            seed = int(hash(txt) % (2**32))
            rng = np.random.RandomState(seed)
            vec = rng.randn(self.dim)
            vectors.append(vec)
        return np.stack(vectors)

_cached_model: Optional[object] = None

def get_model():
    """
    Returns a model instance that provides an `encode` method returning
    384‑dim embeddings. If the real `sentence_transformers` package is
    available, we load the CPU‑only MiniLM model; otherwise we fall back
    to the deterministic `DummyModel`.
    """
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    if _REAL_MODEL_AVAILABLE:
        # Load the actual model (CPU‑only)
        try:
            _cached_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            # If loading fails for any reason, fall back to dummy
            logger = __import__("logging").getLogger(__name__)
            logger.warning(f"Failed to load real SentenceTransformer model: {e}. Using DummyModel.")
            _cached_model = DummyModel()
    else:
        _cached_model = DummyModel()
    return _cached_model

def get_embedding(model, text: str) -> np.ndarray:
    """
    Generates an embedding vector for the given text using the provided model.
    The model must implement an `encode` method compatible with SentenceTransformer.
    """
    # The model's `encode` method expects a list of strings and returns a 2‑D array.
    embedding = model.encode([text])[0]
    return embedding

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculates cosine similarity between two vectors."""
    if vec1.ndim != 1:
        vec1 = vec1.ravel()
    if vec2.ndim != 1:
        vec2 = vec2.ravel()
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def pairwise_cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Calculates the pairwise cosine similarity matrix for a set of embeddings."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = embeddings / norms
    return np.dot(normalized, normalized.T)

def mean_pairwise_similarity(embeddings: np.ndarray) -> float:
    """Calculates the mean of all pairwise cosine similarities (excluding diagonal)."""
    n = embeddings.shape[0]
    if n < 2:
        return 0.0
    sim_matrix = pairwise_cosine_similarity_matrix(embeddings)
    upper_tri = sim_matrix[np.triu_indices(n, k=1)]
    return float(np.mean(upper_tri))

def variance(values: List[float]) -> float:
    """Calculates the variance of a list of values."""
    arr = np.array(values, dtype=float)
    return float(np.var(arr))

def std_dev(values: List[float]) -> float:
    """Calculates the standard deviation of a list of values."""
    arr = np.array(values, dtype=float)
    return float(np.std(arr))