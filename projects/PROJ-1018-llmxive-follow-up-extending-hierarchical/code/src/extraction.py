import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import numpy as np
from src.config import Config
from src.models import RelevanceProfile

logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    chunk_id: str
    text: str
    document_id: str
    start_token: int
    end_token: int
    scores: Optional[List[float]] = None

class DynamicHiLSWrapper:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def extract_scores(self, chunk: Chunk) -> List[float]:
        # Placeholder for actual HiLS inference logic
        # In a real implementation, this would call the model
        if chunk.text is None or len(chunk.text) == 0:
            raise ValueError("Chunk text is empty")
        # Simulate extraction based on config
        # This is a stub for the actual model call
        return [0.0] * self.config.k_clusters

    def handle_errors(self, error: Exception) -> None:
        self.logger.error(f"HiLS extraction error: {error}")
        raise error

def chunk_document(text: str, chunk_size: int) -> List[Chunk]:
    if len(text) < 2048:
        logger.warning(f"Document too short ({len(text)} chars), skipping.")
        return []
    
    chunks = []
    doc_id = f"doc_{id(text)}"
    current_pos = 0
    chunk_idx = 0

    while current_pos < len(text):
        end_pos = min(current_pos + chunk_size, len(text))
        chunk_text = text[current_pos:end_pos]
        
        # Pad if necessary (simple space padding for this implementation)
        if len(chunk_text) < chunk_size:
            chunk_text = chunk_text.ljust(chunk_size)

        chunk = Chunk(
            chunk_id=f"{doc_id}_chunk_{chunk_idx}",
            text=chunk_text,
            document_id=doc_id,
            start_token=current_pos,
            end_token=end_pos
        )
        chunks.append(chunk)
        
        current_pos += chunk_size
        chunk_idx += 1

    return chunks

def aggregate_profiles(chunks: List[Chunk]) -> List[RelevanceProfile]:
    profiles = []
    for chunk in chunks:
        if chunk.scores is None:
            # In a real flow, scores would be populated by DynamicHiLSWrapper
            # Here we assume they might be pre-set or we need to handle missing
            # For the purpose of this task, we assume scores are passed in or generated
            # If this function is called after extraction, scores should exist.
            continue
        
        profile = RelevanceProfile(
            chunk_id=chunk.chunk_id,
            scores=chunk.scores,
            document_id=chunk.document_id
        )
        profiles.append(profile)
    return profiles

def save_profiles(profiles: List[RelevanceProfile], path: str) -> None:
    data = [
        {
            "chunk_id": p.chunk_id,
            "scores": p.scores,
            "document_id": p.document_id
        }
        for p in profiles
    ]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(profiles)} profiles to {path}")

def validate_profiles(profiles: List[RelevanceProfile], config: Optional[Config] = None) -> bool:
    """
    Validates that:
    1. No retrieval scores are null or NaN.
    2. Dimensions match configuration (if config is provided).
    
    Raises ValueError if validation fails.
    """
    if not profiles:
        logger.warning("No profiles to validate.")
        return True

    expected_dim = config.k_clusters if config else None

    for i, profile in enumerate(profiles):
        if profile.scores is None:
            raise ValueError(f"Profile {i} (chunk_id={profile.chunk_id}) has None scores.")
        
        if not isinstance(profile.scores, list):
            raise ValueError(f"Profile {i} (chunk_id={profile.chunk_id}) scores are not a list.")

        for j, score in enumerate(profile.scores):
            if score is None:
                raise ValueError(f"Profile {i} (chunk_id={profile.chunk_id}) has a None score at index {j}.")
            if isinstance(score, float) and (np.isnan(score) or np.isinf(score)):
                raise ValueError(f"Profile {i} (chunk_id={profile.chunk_id}) has a NaN/Inf score at index {j}.")

        if expected_dim is not None:
            if len(profile.scores) != expected_dim:
                raise ValueError(
                    f"Profile {i} (chunk_id={profile.chunk_id}) has {len(profile.scores)} scores, "
                    f"expected {expected_dim} based on config."
                )
    
    logger.info(f"Validation passed for {len(profiles)} profiles.")
    return True
