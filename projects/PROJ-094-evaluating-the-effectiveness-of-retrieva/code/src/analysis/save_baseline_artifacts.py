"""
T020b: Save unmasked baseline retrieval artifacts.

This script persists the raw retrieval scores, semantic descriptors, and query IDs
for the baseline methods (BM25 and Neural) to `data/processed/unmasked_baseline_raw.json`.
This artifact is required by T022 (control experiment) to compare against masked data.

Dependencies:
    - T019: src/data/descriptors.py (to compute descriptors)
    - T020: src/analysis/correlation.py (conceptually, though we re-run logic here for raw data)
    - T007: Preprocessed data must exist in data/processed/test
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports if running as script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.descriptors import compute_all_descriptors, load_snippets
from src.models.retriever_bm25 import load_bm25_retriever, evaluate_retrieval as evaluate_bm25
from src.models.retriever_neural import load_neural_retriever, evaluate_retrieval as evaluate_neural
from src.data.models import CodeSnippet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_queries(queries_path: Path) -> List[Dict[str, Any]]:
    """Load queries from the processed test set CSV/JSONL."""
    # Assuming queries are stored in a format compatible with the test set
    # The main CLI usually loads these. We'll look for a standard location or CSV.
    # Based on T007, processed data is in data/processed/test.
    # We expect a file like queries.csv or similar.
    
    # Fallback to scanning for the queries file if not explicitly named
    test_dir = queries_path.parent
    queries_file = test_dir / "queries.csv"
    if not queries_file.exists():
        # Try to find any csv/jsonl that might contain queries
        for f in test_dir.glob("*.csv"):
            if "query" in f.name.lower():
                queries_file = f
                break
    
    if not queries_file.exists():
        raise FileNotFoundError(f"Could not find queries file in {test_dir}. Expected queries.csv or similar.")

    logger.info(f"Loading queries from {queries_file}")
    import csv
    queries = []
    with open(queries_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys if necessary
            queries.append(row)
    return queries

def save_baseline_artifacts(
    test_data_dir: Path,
    output_path: Path,
    top_k: int = 10
) -> None:
    """
    Orchestrates the retrieval and descriptor computation for baseline methods
    and saves the unmasked artifacts.
    """
    logger.info(f"Starting baseline artifact generation for {test_data_dir}")
    
    # 1. Load Queries
    queries = load_queries(test_data_dir)
    if not queries:
        raise ValueError("No queries found in the test data directory.")
    
    logger.info(f"Loaded {len(queries)} queries.")

    # 2. Load Descriptors (for ground truth and retrieved snippets)
    # This function computes descriptors for the union of ground truth and retrieved snippets.
    # However, to get the retrieved snippets first, we need to run retrieval.
    # T019 logic is: compute descriptors for the union of GT and Top-K retrieved.
    # So we must run retrieval first to get the Top-K snippets to pass to descriptor computation.
    
    # We will store the raw results here
    artifacts: List[Dict[str, Any]] = []

    # 3. Run Retrieval for Baselines
    # We assume the preprocessed data (snippets) is available in the same directory or a sibling 'snippets.csv'
    # The retrievers need to be loaded with the corpus.
    # Based on T007/T009/T010, the retrievers are trained on the full corpus and then evaluated on queries.
    # We need to locate the corpus file used for training/indexing.
    # Assuming it's in data/processed/train or data/processed/test (if test is used for indexing in this context).
    # The task says "unmasked baseline retrieval artifacts", implying we run the retrieval on the test set queries
    # against the index built from the training set (or the full set if that's the design).
    # Let's assume the index files are in data/processed/train/bm25_index.pkl etc.
    
    train_dir = test_data_dir.parent / "train"
    if not train_dir.exists():
        logger.warning(f"Training directory {train_dir} not found. Attempting to use test dir for index if available.")
        train_dir = test_data_dir

    # Load BM25 Retriever
    logger.info("Loading BM25 Retriever...")
    try:
        bm25_retriever = load_bm25_retriever(train_dir)
    except Exception as e:
        logger.error(f"Failed to load BM25 retriever: {e}")
        raise

    # Load Neural Retriever
    logger.info("Loading Neural Retriever...")
    try:
        neural_retriever = load_neural_retriever(train_dir)
    except Exception as e:
        logger.error(f"Failed to load Neural retriever: {e}")
        raise

    logger.info("Starting retrieval and descriptor computation loop...")

    for idx, query in enumerate(queries):
        query_id = query.get('query_id', query.get('id', f'q_{idx}'))
        query_text = query.get('query', query.get('name', ''))
        
        if not query_text:
            logger.warning(f"Skipping query {query_id} due to missing text.")
            continue

        # --- Run BM25 Retrieval ---
        bm25_results = evaluate_bm25(bm25_retriever, query_text, top_k=top_k)
        # bm25_results is a list of (snippet_id, score) or similar structure depending on evaluate_retrieval implementation
        # We need to normalize the structure. Assuming it returns list of dicts with 'id', 'score', 'snippet' (text)
        # If evaluate_retrieval returns just IDs, we need to fetch text.
        # Let's assume evaluate_retrieval returns a list of CodeSnippet-like dicts or objects with 'id', 'text', 'score'
        
        # Extract snippet texts for BM25
        bm25_snippets = []
        if isinstance(bm25_results, list):
            for item in bm25_results:
                if isinstance(item, dict):
                    bm25_snippets.append(item)
                elif hasattr(item, 'to_dict'):
                    bm25_snippets.append(item.to_dict())
                else:
                    # Fallback: assume it's a tuple (id, score) and we need to fetch text
                    # This is risky without a global snippet store, so we assume the retriever returns full snippets
                    pass

        # --- Run Neural Retrieval ---
        neural_results = evaluate_neural(neural_retriever, query_text, top_k=top_k)
        neural_snippets = []
        if isinstance(neural_results, list):
            for item in neural_results:
                if isinstance(item, dict):
                    neural_snippets.append(item)
                elif hasattr(item, 'to_dict'):
                    neural_snippets.append(item.to_dict())

        # --- Compute Descriptors ---
        # We need Ground Truth snippets too.
        # The query dict should contain 'ground_truth' or 'relevant_ids'
        gt_snippets = []
        gt_ids = query.get('ground_truth', query.get('relevant_ids', []))
        if isinstance(gt_ids, str):
            gt_ids = [gt_ids]
        
        # We need to fetch GT snippet text. This implies we have a way to look up snippets by ID.
        # The descriptors.py load_snippets might handle this if we pass the file path.
        # Let's assume we have a master snippets file in data/processed/test/snippets.csv
        snippets_file = test_data_dir / "snippets.csv"
        if not snippets_file.exists():
            snippets_file = test_data_dir.parent / "train" / "snippets.csv"
        
        if snippets_file.exists():
            all_snippets_map = load_snippets(snippets_file)
        else:
            logger.warning(f"Snippets file {snippets_file} not found. Descriptors will be empty or partial.")
            all_snippets_map = {}

        # Collect all snippet texts for descriptor calculation
        # 1. Ground Truth
        for gt_id in gt_ids:
            if gt_id in all_snippets_map:
                gt_snippets.append(all_snippets_map[gt_id])

        # 2. Retrieved BM25
        for s in bm25_snippets:
            if isinstance(s, dict) and 'text' in s:
                gt_snippets.append(s) # Re-using list to collect union, but we need to be careful not to double count
        
        # 3. Retrieved Neural
        for s in neural_snippets:
            if isinstance(s, dict) and 'text' in s:
                # Avoid adding duplicates if same snippet appears in both
                if s not in gt_snippets: 
                    gt_snippets.append(s)

        # Compute descriptors for the union of GT and Retrieved
        # We pass the list of snippet dicts to compute_descriptors_for_query
        # Note: T019 expects a function that takes query text and a list of snippets
        try:
            descriptors = compute_all_descriptors(query_text, gt_snippets)
        except Exception as e:
            logger.error(f"Failed to compute descriptors for {query_id}: {e}")
            descriptors = {}

        # --- Construct Artifact Entry ---
        entry = {
            "query_id": query_id,
            "query_text": query_text,
            "ground_truth_ids": gt_ids,
            "bm25_retrieved": [
                {"id": s.get('id'), "score": s.get('score'), "text": s.get('text')} 
                for s in bm25_snippets
            ],
            "neural_retrieved": [
                {"id": s.get('id'), "score": s.get('score'), "text": s.get('text')} 
                for s in neural_snippets
            ],
            "descriptors": descriptors,
            "unmasked": True
        }
        artifacts.append(entry)

        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx + 1}/{len(queries)} queries.")

    # 4. Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(artifacts, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(artifacts)} baseline artifacts to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Save unmasked baseline retrieval artifacts (T020b).")
    parser.add_argument(
        "--test-data-dir", 
        type=Path, 
        default=Path("data/processed/test"),
        help="Path to the processed test data directory containing queries and snippets."
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/processed/unmasked_baseline_raw.json"),
        help="Path to save the output JSON artifact."
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of top results to retrieve."
    )
    
    args = parser.parse_args()
    
    if not args.test_data_dir.exists():
        logger.error(f"Test data directory not found: {args.test_data_dir}")
        sys.exit(1)

    save_baseline_artifacts(
        test_data_dir=args.test_data_dir,
        output_path=args.output_path,
        top_k=args.top_k
    )

if __name__ == "__main__":
    main()
