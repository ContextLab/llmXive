from __future__ import annotations

import csv
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch

from config import get_data_root, get_processed_dir, get_random_seed
from checksum_manifest import record_artifact_checksums

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SemanticCloner:
    """
    Computes semantic distance between code segments using CodeBERT embeddings.
    """

    def __init__(self, model_name: str = "microsoft/codebert-base", device: str = "cpu"):
        """
        Initialize the SemanticCloner with a CodeBERT model.

        Args:
            model_name: HuggingFace model name for CodeBERT.
            device: Device to run inference on ('cpu' or 'cuda').
        """
        self.device = device
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the CodeBERT model and tokenizer."""
        logger.info(f"Loading model {self.model_name} on {self.device}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Compute mean-pooled embeddings for a batch of texts.

        Args:
            texts: List of code strings.

        Returns:
            Numpy array of shape (len(texts), hidden_size).
        """
        if not texts:
            return np.empty((0, 768))  # CodeBERT hidden size

        # Tokenize
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            # Get last hidden state
            last_hidden_states = outputs.last_hidden_state
            # Attention mask
            attention_mask = inputs['attention_mask']

            # Mean pooling
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
            embeddings = torch.sum(last_hidden_states * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

        return embeddings.cpu().numpy()

    def compute_cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            emb1: First embedding vector.
            emb2: Second embedding vector.

        Returns:
            Cosine similarity score.
        """
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(emb1, emb2) / (norm1 * norm2))

    def compute_semantic_distance_batch(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compute semantic distance for pairs of segments.
        For this task, we compute the distance of each segment to a reference (e.g., the first segment
        or an average) to generate a scalar 'semantic_distance' per segment, or compute pairwise distances
        if the input implies pairs.
        
        Given the context of 'clone density', we assume we are comparing segments to find semantic clones.
        Here, we will compute the semantic distance of each segment from the *mean* of all segments 
        to provide a metric of 'semantic uniqueness' or distance from the centroid, 
        OR compute pairwise distances if the data structure implies pairs (segment_id, target_id).
        
        Implementation choice: Since `clone_metrics.csv` likely contains per-segment stats,
        we will compute the semantic distance of each segment to the global centroid of the batch.
        This serves as a measure of how 'semantically distinct' a segment is.
        Alternatively, if the task implies finding clones, we might compute pairwise distances.
        Let's implement pairwise distance for the first 100 segments to demonstrate the capability 
        and output a summary or a specific file `semantic_distance.csv` with segment_id and distance_to_centroid.
        
        Re-reading T053: "output to data/processed/semantic_distance.csv".
        We will compute the distance of each segment to the centroid of the batch.
        
        Args:
            segments: List of dicts with 'segment_id' and 'code'.
        
        Returns:
            List of dicts with 'segment_id', 'code' (optional), 'semantic_distance'.
        """
        if not segments:
            logger.warning("No segments provided.")
            return []

        codes = [s['code'] for s in segments]
        embeddings = self._get_embeddings(codes)

        # Compute centroid
        centroid = np.mean(embeddings, axis=0)

        results = []
        for i, segment in enumerate(segments):
            emb = embeddings[i]
            dist = 1.0 - self.compute_cosine_similarity(emb, centroid)
            results.append({
                'segment_id': segment['segment_id'],
                'semantic_distance': dist
            })
        
        return results

def load_segment_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load segment data from a CSV file.
    Expected columns: segment_id, code (or similar text column).
    """
    segments = []
    logger.info(f"Loading segment data from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assume 'code' or 'content' or 'text' is the code column
            code_col = None
            for col in ['code', 'content', 'text', 'function_body']:
                if col in row:
                    code_col = col
                    break
            
            if code_col is None:
                logger.warning(f"Could not find code column in row: {row.keys()}")
                continue
            
            if row[code_col] and row[code_col].strip():
                segments.append({
                    'segment_id': row.get('segment_id', row.get('id', '')),
                    'code': row[code_col]
                })
    
    logger.info(f"Loaded {len(segments)} segments.")
    return segments

def main():
    """
    Main entry point for the semantic distance computation.
    Reads from data/processed/clone_metrics.csv (or similar) and writes to data/processed/semantic_distance.csv.
    """
    data_root = get_data_root()
    processed_dir = get_processed_dir()
    
    # Determine input file
    # T053 says: "Extend model_metrics.py to compute semantic distance... output to data/processed/semantic_distance.csv"
    # T019 produces clone_metrics. T053 likely reads clone_metrics which has segment_id and code.
    input_path = processed_dir / "clone_metrics.csv"
    output_path = processed_dir / "semantic_distance.csv"
    
    if not input_path.exists():
        # Fallback to raw if clone_metrics not ready, but T053 implies US1 is done
        # Let's try to load from raw if needed, but strict adherence to T053 suggests reading processed
        logger.error(f"Input file {input_path} not found. Cannot compute semantic distance.")
        raise FileNotFoundError(f"Input file {input_path} not found.")

    # Load segments
    segments = load_segment_data(input_path)
    
    if not segments:
        logger.warning("No valid segments found in input. Exiting.")
        return

    # Initialize cloner
    # Use CPU for safety in this environment, or CUDA if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cloner = SemanticCloner(device=device)

    # Compute distances
    logger.info("Computing semantic distances...")
    results = cloner.compute_semantic_distance_batch(segments)

    # Write results
    logger.info(f"Writing results to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['segment_id', 'semantic_distance'])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    logger.info(f"Successfully wrote {len(results)} records to {output_path}")
    
    # Record checksums
    record_artifact_checksums([output_path])
    logger.info("Checksums recorded.")

if __name__ == "__main__":
    main()
