import pytest
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def test_cosine_similarity_threshold():
    # Simulate ID centroid and OOD embedding
    id_centroid = np.array([[1.0, 0.0, 0.0]])
    ood_embedding = np.array([[0.1, 0.1, 0.1]])
    
    sim = cosine_similarity(id_centroid, ood_embedding)[0][0]
    assert sim < 0.3
