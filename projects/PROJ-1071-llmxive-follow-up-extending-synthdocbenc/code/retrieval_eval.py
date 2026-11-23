import os
import sys
import json
import time
import gc
import hashlib
import math
from typing import List, Dict, Any, Optional, Tuple

# Import existing utilities and models
from utils import pin_random_seed, compute_file_checksum, update_state_json, load_state_json
from logging_config import get_logger
from models.evaluation import RetrievalMetrics

# Import FAISS and sentence-transformers for similarity
try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_FAISS = True
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_FAISS = False
    HAS_SENTENCE_TRANSFORMERS = False

logger = get_logger(__name__)

# Configuration constants
MAX_TOKENS = 2048
SIMILARITY_THRESHOLD = 0.5
SIMILARITY_MODEL_NAME = "all-MiniLM-L6-v2"

def load_index_metadata(index_dir: str = "data/derived/index") -> Dict[str, Any]:
    """Load the FAISS index metadata file."""
    metadata_path = os.path.join(index_dir, "index_metadata.json")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Index metadata not found at {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        return json.load(f)

def load_ground_truth_set(gt_path: str = "data/derived/ground_truth_retrieval_set.json") -> Dict[str, Any]:
    """Load the ground truth retrieval set constructed in T016."""
    if not os.path.exists(gt_path):
        raise FileNotFoundError(f"Ground truth set not found at {gt_path}")
    
    with open(gt_path, 'r') as f:
        return json.load(f)

def load_retrieved_snippets(index_dir: str = "data/derived/index") -> Dict[str, List[Dict]]:
    """Load the chunked text snippets associated with the index."""
    snippets_path = os.path.join(index_dir, "snippets.json")
    if not os.path.exists(snippets_path):
        raise FileNotFoundError(f"Snippets file not found at {snippets_path}")
    
    with open(snippets_path, 'r') as f:
        return json.load(f)

def calculate_similarity(query_text: str, candidate_text: str, model) -> float:
    """Calculate cosine similarity between query and candidate text."""
    if not HAS_SENTENCE_TRANSFORMERS:
        raise ImportError("sentence-transformers library is required for similarity scoring.")
    
    try:
        embeddings = model.encode([query_text, candidate_text], convert_to_numpy=True)
        # Normalize
        norm_query = embeddings[0] / np.linalg.norm(embeddings[0])
        norm_cand = embeddings[1] / np.linalg.norm(embeddings[1])
        # Dot product for cosine similarity
        return float(np.dot(norm_query, norm_cand))
    except Exception as e:
        logger.error(f"Similarity calculation failed: {e}")
        return 0.0

def estimate_token_count(text: str) -> int:
    """Rough estimate of token count (approx 4 chars per token)."""
    return len(text.split()) * 1.3  # Rough heuristic for English text

def limit_tokens(text: str, max_tokens: int = MAX_TOKENS) -> str:
    """Truncate text to fit within max_tokens limit."""
    words = text.split()
    if estimate_token_count(text) <= max_tokens:
        return text
    
    # Truncate to fit
    max_words = int(max_tokens / 1.3)
    return " ".join(words[:max_words]) + "..."

def calculate_precision_recall(retrieved_ids: List[str], ground_truth_ids: List[str]) -> Tuple[float, float]:
    """Calculate precision and recall based on retrieved vs ground truth IDs."""
    if not retrieved_ids:
        return 0.0, 0.0 if not ground_truth_ids else 0.0
    
    retrieved_set = set(retrieved_ids)
    ground_truth_set = set(ground_truth_ids)
    
    if not ground_truth_set:
        # If no ground truth, precision is 0 if we retrieved anything, else undefined (0)
        return 0.0 if retrieved_ids else 0.0, 0.0
    
    true_positives = len(retrieved_set.intersection(ground_truth_set))
    precision = true_positives / len(retrieved_ids) if retrieved_ids else 0.0
    recall = true_positives / len(ground_truth_ids) if ground_truth_ids else 0.0
    
    return precision, recall

def evaluate_retrieval(
    index_dir: str = "data/derived/index",
    gt_path: str = "data/derived/ground_truth_retrieval_set.json",
    output_path: str = "data/derived/retrieval_metrics.json"
) -> Dict[str, Any]:
    """
    Main evaluation logic for T017.
    Consumes ground_truth_retrieval_set, calculates similarity, token limits, precision/recall.
    """
    if not HAS_FAISS or not HAS_SENTENCE_TRANSFORMERS:
        raise RuntimeError("Required libraries (faiss-cpu, sentence-transformers) are not installed.")

    logger.info("Starting retrieval evaluation (T017)...")
    
    # Load dependencies
    logger.info("Loading index metadata...")
    metadata = load_index_metadata(index_dir)
    
    logger.info("Loading ground truth set...")
    ground_truth_set = load_ground_truth_set(gt_path)
    
    logger.info("Loading snippets...")
    snippets = load_retrieved_snippets(index_dir)
    
    # Initialize similarity model
    logger.info(f"Loading sentence transformer model: {SIMILARITY_MODEL_NAME}...")
    model = SentenceTransformer(SIMILARITY_MODEL_NAME)
    
    # Metrics accumulators
    total_questions = 0
    total_precision = 0.0
    total_recall = 0.0
    total_false_positives = 0
    total_false_negatives = 0
    total_true_positives = 0
    total_true_negatives = 0
    
    # Per-question results
    question_results = []
    
    # Iterate over ground truth set
    # Expected structure: { "question_id": { "query": "...", "ground_truth_snippet_ids": [...] } }
    for q_id, q_data in ground_truth_set.items():
        total_questions += 1
        query_text = q_data.get("query", "")
        gt_ids = q_data.get("ground_truth_snippet_ids", [])
        
        # 1. Retrieve top-k snippets (simulating the retrieval step from T016)
        # We need to find the best matching snippets from the loaded metadata/snippets
        # Since we don't have the FAISS index loaded here (just metadata/snippets for this eval),
        # we simulate retrieval by scoring all snippets or a subset if too large.
        # For efficiency in this script, we score all available snippets for this document or use metadata to filter.
        
        # Optimization: If metadata has document-level mapping, we could filter. 
        # For now, we assume the 'snippets' dict contains all relevant chunks.
        # To be realistic, we'll score a subset or all if small. 
        # In a real pipeline, we'd query the FAISS index. Here we implement the scoring logic.
        
        scored_snippets = []
        for s_id, s_text in snippets.items():
            # Check if this snippet belongs to the same document as the query if possible
            # (Assuming snippet_id format: doc_id_page_id_chunk_id)
            # For simplicity, we score all. In production, FAISS handles this.
            sim = calculate_similarity(query_text, s_text, model)
            scored_snippets.append((s_id, sim))
        
        # Sort by similarity descending
        scored_snippets.sort(key=lambda x: x[1], reverse=True)
        
        # Apply token limit to the top retrieved set
        # We take top N, then limit total tokens
        retrieved_ids = []
        total_tokens = 0
        retrieved_texts = []
        
        for s_id, sim in scored_snippets:
            if total_tokens >= MAX_TOKENS:
                break
            s_text = snippets[s_id]
            tokens = estimate_token_count(s_text)
            if total_tokens + tokens > MAX_TOKENS:
                # Truncate this snippet to fit
                remaining_tokens = MAX_TOKENS - total_tokens
                truncated_text = limit_tokens(s_text, remaining_tokens)
                retrieved_texts.append(truncated_text)
                total_tokens += estimate_token_count(truncated_text)
            else:
                retrieved_texts.append(s_text)
                total_tokens += tokens
            
            retrieved_ids.append(s_id)
            
            # Stop if we have enough (e.g., top 5) or token limit hit
            if len(retrieved_ids) >= 5:
                break
        
        # 2. Calculate Metrics against Ground Truth
        precision, recall = calculate_precision_recall(retrieved_ids, gt_ids)
        
        # 3. Calculate False Positive Rate (SC-003)
        # "retrieved snippet similarity < 0.5 AND no ground truth"
        # Here we check the retrieved set.
        # A False Positive in this context: Retrieved a snippet that is NOT in ground truth AND has low similarity?
        # The definition in SC-003 is: "retrieved snippet similarity < 0.5 AND no ground truth"
        # This implies we count a retrieval as a false positive if the snippet is not in GT and sim < 0.5.
        # However, we retrieved the top 5. If any of them are not in GT and have low sim, they are FP.
        
        fp_count = 0
        for s_id, sim in scored_snippets[:len(retrieved_ids)]:
            if s_id not in gt_ids and sim < SIMILARITY_THRESHOLD:
                fp_count += 1
        
        # Accumulate
        total_precision += precision
        total_recall += recall
        total_true_positives += len(set(retrieved_ids).intersection(gt_ids))
        total_false_positives += fp_count
        
        # FN: GT items not retrieved
        total_false_negatives += len(set(gt_ids) - set(retrieved_ids))
        
        # TN: Not explicitly tracked in retrieval usually, but for completeness:
        # Total possible - (TP + FP + FN) ... complex without a fixed universe. Skip TN for now.
        
        question_results.append({
            "question_id": q_id,
            "retrieved_count": len(retrieved_ids),
            "precision": precision,
            "recall": recall,
            "false_positives": fp_count,
            "token_count": total_tokens
        })
        
        if total_questions % 10 == 0:
            logger.info(f"Processed {total_questions} questions...")

    # Aggregate
    avg_precision = total_precision / total_questions if total_questions > 0 else 0.0
    avg_recall = total_recall / total_questions if total_questions > 0 else 0.0
    
    # False Positive Rate: FP / (FP + TN) ? 
    # The task asks for "false-positive rate" defined in SC-003.
    # Let's report the count and the ratio of FP to total retrieved.
    total_retrieved = sum(len(r["retrieved_ids"]) for r in question_results) # Re-calc or store
    # Actually, let's just use the accumulated FP and total retrieved count logic
    # We need total retrieved count. Let's re-sum from results.
    total_retrieved_count = sum(r["retrieved_count"] for r in question_results)
    fpr = total_false_positives / total_retrieved_count if total_retrieved_count > 0 else 0.0

    metrics = {
        "total_questions": total_questions,
        "average_precision": avg_precision,
        "average_recall": avg_recall,
        "total_true_positives": total_true_positives,
        "total_false_positives": total_false_positives,
        "total_false_negatives": total_false_negatives,
        "false_positive_rate": fpr,
        "per_question_metrics": question_results
    }

    # Save to disk
    logger.info(f"Saving retrieval metrics to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Update state
    update_state_json({
        "task": "T017",
        "status": "completed",
        "metrics_file": output_path
    })
    
    logger.info("Retrieval evaluation completed.")
    return metrics

def save_perf_metrics(metrics: Dict[str, Any], output_path: str = "data/derived/perf_metrics.json"):
    """Save performance metrics to the derived directory."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            existing = json.load(f)
    else:
        existing = []
    
    existing.append(metrics)
    
    with open(output_path, 'w') as f:
        json.dump(existing, f, indent=2)

def main():
    """Entry point for T017."""
    pin_random_seed(42)
    
    try:
        metrics = evaluate_retrieval()
        logger.info(f"Evaluation complete. Precision: {metrics['average_precision']:.4f}, Recall: {metrics['average_recall']:.4f}")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    main()
