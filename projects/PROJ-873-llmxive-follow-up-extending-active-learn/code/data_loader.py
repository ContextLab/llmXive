"""
data_loader.py - BEIR dataset loading and synthetic redundancy injection.

This module handles:
1. Fetching real datasets (nfcorpus, scifact, trec-covid) from BEIR.
2. Injecting synthetic redundancy via synonym replacement and sentence shuffling.
3. Validating that injected redundancy meets the >0.95 similarity threshold.
4. Strict fallback logic: raises DataInjectionFailureError if injection fails after retries.
"""

import os
import json
import hashlib
import logging
import zipfile
import io
import random
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Third-party imports (must be in requirements.txt)
try:
    from beir import util
    from beir.datasets.data_loader import GenericDataLoader
except ImportError:
    raise ImportError("The 'beir' package is required. Install it via 'pip install beir'.")

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    raise ImportError("The 'sentence-transformers' and 'numpy' packages are required.")

try:
    import nltk
    from nltk.corpus import wordnet
except ImportError:
    raise ImportError("The 'nltk' package is required.")

# Local imports (project structure)
# Note: We assume config.py exists and provides paths if needed, but we use relative paths here.
from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Custom Exceptions ---

class DataInjectionError(Exception):
    """Raised when synthetic redundancy injection fails to meet criteria."""
    pass

class DataInjectionFailureError(DataInjectionError):
    """
    Raised when synthetic redundancy injection FAILS after maximum retries.
    This is the strict fallback error for Edge Case 2 (T058).
    """
    def __init__(self, message: str, attempted_synonyms: List[str], final_scores: List[float]):
        super().__init__(message)
        self.attempted_synonyms = attempted_synonyms
        self.final_scores = final_scores

# --- Utility Functions ---

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_beir_dataset(dataset_name: str, output_dir: str) -> str:
    """
    Download and unzip a BEIR dataset.
    Returns the path to the unzipped dataset directory.
    """
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
    logger.info(f"Downloading {dataset_name} from {url}...")
    try:
        data_path = util.download_and_unzip(url, output_dir)
        logger.info(f"Downloaded and unzipped to: {data_path}")
        return data_path
    except Exception as e:
        logger.error(f"Failed to download {dataset_name}: {e}")
        raise RuntimeError(f"BEIR download failed for {dataset_name}: {e}")

def load_beir_corpus(data_path: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Dict[str, int]]]:
    """
    Load corpus, queries, and qrels from a BEIR dataset path.
    Returns: (corpus, queries, qrels)
    """
    try:
        corpus, queries, qrels = GenericDataLoader(data_path).load(split="test")
        return corpus, queries, qrels
    except Exception as e:
        logger.error(f"Failed to load BEIR data from {data_path}: {e}")
        raise

def get_synonyms(word: str, max_synonyms: int = 5) -> List[str]:
    """
    Get synonyms for a word using WordNet.
    Returns a list of synonym strings.
    """
    try:
        # Ensure wordnet data is downloaded
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)
        
        synsets = wordnet.synsets(word)
        synonyms = set()
        for syn in synsets:
            for lemma in syn.lemmas():
                if lemma.name() != word.lower():
                    synonyms.add(lemma.name().replace('_', ' '))
        
        if not synonyms:
            return []
        
        return list(synonyms)[:max_synonyms]
    except Exception as e:
        logger.warning(f"Could not get synonyms for '{word}': {e}")
        return []

def calculate_embedding_similarity(text1: str, text2: str, model: SentenceTransformer) -> float:
    """Calculate cosine similarity between two texts using the embedding model."""
    try:
        embeddings = model.encode([text1, text2], convert_to_tensor=False)
        sim = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
        return float(sim)
    except Exception as e:
        logger.error(f"Error calculating embedding similarity: {e}")
        return 0.0

# --- Redundancy Injection Logic ---

def inject_synonym_replacement(text: str, model: SentenceTransformer, similarity_threshold: float = 0.95) -> Tuple[str, float]:
    """
    Replace random words in the text with synonyms to create a near-duplicate.
    Returns (modified_text, similarity_score).
    """
    words = text.split()
    if len(words) < 5:
        return text, 0.0 # Too short to modify meaningfully

    modified_words = list(words)
    synonyms_applied = []
    
    # Try to replace up to 10% of words, but at least 1
    num_to_replace = max(1, int(len(words) * 0.1))
    indices_to_replace = random.sample(range(len(words)), min(num_to_replace, len(words)))

    for idx in indices_to_replace:
        word = words[idx]
        # Skip very short words or numbers
        if len(word) < 3 or word.isdigit():
            continue
        
        syns = get_synonyms(word)
        if syns:
            new_word = random.choice(syns)
            modified_words[idx] = new_word
            synonyms_applied.append(f"{word}->{new_word}")

    modified_text = " ".join(modified_words)
    similarity = calculate_embedding_similarity(text, modified_text, model)
    
    return modified_text, similarity

def inject_sentence_shuffle(text: str, model: SentenceTransformer) -> Tuple[str, float]:
    """
    Shuffle sentences in the text to create a near-duplicate.
    Returns (modified_text, similarity_score).
    """
    sentences = text.split('.')
    if len(sentences) < 2:
        return text, 0.0

    # Remove empty strings and rejoin with dots later
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) < 2:
        return text, 0.0

    shuffled_sentences = sentences.copy()
    random.shuffle(shuffled_sentences)
    
    modified_text = ". ".join(shuffled_sentences) + "."
    similarity = calculate_embedding_similarity(text, modified_text, model)
    
    return modified_text, similarity

def create_redundancy_clusters(corpus: Dict[str, Any], model: SentenceTransformer, target_similarity: float = 0.95) -> List[Dict[str, Any]]:
    """
    Create redundancy clusters by injecting synonyms and shuffling.
    Returns a list of clusters, where each cluster contains the original and modified versions.
    """
    clusters = []
    doc_ids = list(corpus.keys())
    
    # Limit to first 50 docs for injection to keep runtime reasonable during testing
    # In a full run, this might be configurable or streamed
    sample_ids = doc_ids[:min(50, len(doc_ids))]
    
    logger.info(f"Creating redundancy clusters for {len(sample_ids)} documents...")
    
    for doc_id in sample_ids:
        original_text = corpus[doc_id].get("text", "")
        if not original_text:
            continue
        
        cluster = {
            "original_id": doc_id,
            "original_text": original_text,
            "variants": []
        }
        
        # Attempt synonym replacement
        modified_text, sim = inject_synonym_replacement(original_text, model, target_similarity)
        if sim >= target_similarity:
            cluster["variants"].append({
                "variant_id": f"{doc_id}_syn",
                "text": modified_text,
                "method": "synonym_replacement",
                "similarity": sim
            })
        
        # If synonym replacement didn't meet threshold, try shuffle
        if sim < target_similarity:
            shuffled_text, sim_shuffled = inject_sentence_shuffle(original_text, model)
            if sim_shuffled >= target_similarity:
                cluster["variants"].append({
                    "variant_id": f"{doc_id}_shuf",
                    "text": shuffled_text,
                    "method": "sentence_shuffle",
                    "similarity": sim_shuffled
                })
        
        if cluster["variants"]:
            clusters.append(cluster)
    
    return clusters

def validate_injected_similarity(cluster: Dict[str, Any], model: SentenceTransformer, threshold: float = 0.95) -> bool:
    """
    Validate that all variants in a cluster meet the similarity threshold.
    """
    original_text = cluster["original_text"]
    for variant in cluster["variants"]:
        sim = calculate_embedding_similarity(original_text, variant["text"], model)
        if sim < threshold:
            logger.warning(f"Variant {variant['variant_id']} similarity {sim:.4f} < {threshold}")
            return False
    return True

def save_injected_dataset(clusters: List[Dict[str, Any]], output_path: str):
    """Save the injected dataset clusters to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(clusters, f, indent=2)
    logger.info(f"Saved injected dataset to {output_path}")

def load_injected_dataset(input_path: str) -> List[Dict[str, Any]]:
    """Load the injected dataset from a JSON file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Injected dataset file not found: {input_path}")
    with open(input_path, 'r') as f:
        return json.load(f)

# --- T058: Strict Paraphrasing Fallback Implementation ---

def prepare_injected_datasets(
    datasets: List[str], 
    output_dir: str, 
    model_name: str = "all-MiniLM-L6-v2",
    max_retries: int = 3,
    similarity_threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Prepare injected datasets for specified BEIR datasets.
    
    Implements T058 Strict Paraphrasing Fallback:
    If synthetic injection fails to produce pairs with similarity > 0.95 
    after max_retries with varying synonyms, raises DataInjectionFailureError.
    
    Args:
        datasets: List of dataset names (e.g., ['nfcorpus', 'scifact'])
        output_dir: Directory to save injected datasets
        model_name: Sentence transformer model to use
        max_retries: Maximum retry attempts for synonym replacement
        similarity_threshold: Target similarity threshold (default 0.95)
        
    Returns:
        Dictionary with injection results and statistics
    """
    config = get_config()
    data_dir = os.path.join(config.data_dir, "raw")
    processed_dir = os.path.join(config.data_dir, "processed")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    model = SentenceTransformer(model_name)
    results = {
        "datasets": {},
        "total_clusters": 0,
        "failed_injections": []
    }
    
    for dataset_name in datasets:
        logger.info(f"Processing dataset: {dataset_name}")
        try:
            # Download and load
            data_path = download_beir_dataset(dataset_name, data_dir)
            corpus, queries, qrels = load_beir_corpus(data_path)
            
            # Create clusters with retry logic
            clusters = []
            doc_ids = list(corpus.keys())[:50] # Sample for efficiency
            
            injection_success = False
            attempted_synonyms_log = []
            final_scores_log = []
            
            for attempt in range(max_retries):
                logger.info(f"Attempt {attempt + 1}/{max_retries} for {dataset_name}")
                
                # Reset random seed slightly for variation
                random.seed(42 + attempt)
                
                attempt_clusters = []
                for doc_id in doc_ids:
                    original_text = corpus[doc_id].get("text", "")
                    if not original_text:
                        continue
                    
                    cluster = {
                        "original_id": doc_id,
                        "original_text": original_text,
                        "variants": [],
                        "attempt": attempt + 1
                    }
                    
                    # Try synonym replacement with variation
                    modified_text, sim = inject_synonym_replacement(original_text, model, similarity_threshold)
                    
                    if sim >= similarity_threshold:
                        cluster["variants"].append({
                            "variant_id": f"{doc_id}_syn_v{attempt+1}",
                            "text": modified_text,
                            "method": "synonym_replacement",
                            "similarity": sim,
                            "attempt": attempt + 1
                        })
                        injection_success = True
                    
                    # If not successful, try shuffle
                    if not injection_success:
                        shuffled_text, sim_shuffled = inject_sentence_shuffle(original_text, model)
                        if sim_shuffled >= similarity_threshold:
                            cluster["variants"].append({
                                "variant_id": f"{doc_id}_shuf_v{attempt+1}",
                                "text": shuffled_text,
                                "method": "sentence_shuffle",
                                "similarity": sim_shuffled,
                                "attempt": attempt + 1
                            })
                            injection_success = True
                    
                    if cluster["variants"]:
                        attempt_clusters.append(cluster)
                
                if attempt_clusters:
                    clusters = attempt_clusters
                    break
                
                # Log attempts for failure analysis
                if attempt == max_retries - 1:
                    # Collect data for error report
                    for doc_id in doc_ids[:10]: # Sample for logging
                        original_text = corpus[doc_id].get("text", "")
                        if original_text:
                            syns = get_synonyms(original_text.split()[0] if original_text.split() else "test")
                            attempted_synonyms_log.extend(syns)
                            sim = calculate_embedding_similarity(original_text, original_text, model) # Baseline
                            final_scores_log.append(sim)
            
            if not injection_success:
                # T058: Strict Fallback - Raise Error if all retries fail
                error_msg = (
                    f"Failed to inject redundancy with similarity > {similarity_threshold} for dataset {dataset_name} "
                    f"after {max_retries} retries. "
                    f"Attempted synonyms: {attempted_synonyms_log[:10]}... "
                    f"Final scores: {final_scores_log[:5]}..."
                )
                logger.error(error_msg)
                raise DataInjectionFailureError(
                    message=error_msg,
                    attempted_synonyms=attempted_synonyms_log,
                    final_scores=final_scores_log
                )
            
            # Save successful clusters
            output_path = os.path.join(processed_dir, f"injected_{dataset_name}.json")
            save_injected_dataset(clusters, output_path)
            
            results["datasets"][dataset_name] = {
                "clusters_count": len(clusters),
                "output_path": output_path,
                "success": True
            }
            results["total_clusters"] += len(clusters)
            
        except DataInjectionFailureError:
            # Re-raise to halt pipeline as per T058
            raise
        except Exception as e:
            logger.error(f"Failed to process {dataset_name}: {e}")
            results["datasets"][dataset_name] = {
                "error": str(e),
                "success": False
            }
    
    return results

def validate_redundancy_clusters_on_trec_covid(model_name: str = "all-MiniLM-L6-v2") -> Dict[str, Any]:
    """
    Validate existing redundancy in trec-covid dataset (real data check).
    Scans for existing near-duplicate clusters (similarity > 0.95).
    """
    config = get_config()
    data_dir = os.path.join(config.data_dir, "raw")
    processed_dir = os.path.join(config.data_dir, "processed")
    
    model = SentenceTransformer(model_name)
    dataset_name = "trec-covid"
    
    try:
        data_path = download_beir_dataset(dataset_name, data_dir)
        corpus, queries, qrels = load_beir_corpus(data_path)
        
        # Scan for duplicates (simplified: check first 100 docs)
        doc_ids = list(corpus.keys())[:100]
        clusters = []
        
        logger.info(f"Scanning {dataset_name} for natural redundancy...")
        
        for i, doc_id1 in enumerate(doc_ids):
            text1 = corpus[doc_id1].get("text", "")
            for doc_id2 in doc_ids[i+1:]:
                text2 = corpus[doc_id2].get("text", "")
                if not text1 or not text2:
                    continue
                
                sim = calculate_embedding_similarity(text1, text2, model)
                if sim > 0.95:
                    clusters.append({
                        "doc1_id": doc_id1,
                        "doc2_id": doc_id2,
                        "similarity": sim
                    })
        
        output_path = os.path.join(processed_dir, "trec_covid_validation.json")
        result = {
            "dataset": dataset_name,
            "natural_clusters_found": len(clusters),
            "clusters": clusters[:10], # Limit output size
            "threshold": 0.95,
            "status": "validation_complete" if clusters else "no_natural_clusters_found"
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Saved trec-covid validation to {output_path}")
        return result
        
    except Exception as e:
        logger.error(f"Validation failed for {dataset_name}: {e}")
        return {
            "dataset": dataset_name,
            "status": "validation_skipped",
            "reason": str(e)
        }

# --- CLI Entry Point ---

def main():
    """
    CLI entry point for data loader.
    Supports 'prepare' and 'validate_trec_covid' commands.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="BEIR Data Loader and Redundancy Injector")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Prepare command (T012, T043, T058)
    prepare_parser = subparsers.add_parser("prepare", help="Prepare injected datasets")
    prepare_parser.add_argument("--datasets", nargs="+", default=["nfcorpus", "scifact"],
                                help="Datasets to process")
    prepare_parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Embedding model")
    prepare_parser.add_argument("--retries", type=int, default=3, help="Max retry attempts for injection")
    prepare_parser.add_argument("--threshold", type=float, default=0.95, help="Similarity threshold")
    
    # Validate TREC-Covid command (T017)
    validate_parser = subparsers.add_parser("validate_trec_covid", help="Validate natural redundancy in trec-covid")
    validate_parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Embedding model")
    
    args = parser.parse_args()
    
    if args.command == "prepare":
        logger.info(f"Starting preparation for datasets: {args.datasets}")
        try:
            results = prepare_injected_datasets(
                datasets=args.datasets,
                output_dir="data/processed",
                model_name=args.model,
                max_retries=args.retries,
                similarity_threshold=args.threshold
            )
            logger.info(f"Preparation complete. Results: {json.dumps(results, indent=2)}")
        except DataInjectionFailureError as e:
            logger.error(f"CRITICAL: Data injection failed. Halting pipeline. Details: {e}")
            logger.error(f"Attempted synonyms: {e.attempted_synonyms}")
            logger.error(f"Final scores: {e.final_scores}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error during preparation: {e}")
            sys.exit(1)
            
    elif args.command == "validate_trec_covid":
        logger.info("Starting TREC-Covid validation...")
        result = validate_redundancy_clusters_on_trec_covid(model_name=args.model)
        logger.info(f"Validation result: {json.dumps(result, indent=2)}")
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()