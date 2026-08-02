"""
Active Ranker module for llmXive.
Implements baseline ranking, pre-clustering filtering, and LLM consensus validation.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from models import CandidateList
from clustering import filter_candidates_by_clustering, MinHashCluster

# Configuration
MAX_TOKENS = 200
TEMPERATURE = 0.0

logger = logging.getLogger(__name__)

def load_cluster_results(cluster_path: str) -> List[Dict[str, Any]]:
    """Load clustering results from a JSON file."""
    if not os.path.exists(cluster_path):
        raise FileNotFoundError(f"Cluster file not found: {cluster_path}")
    with open(cluster_path, 'r') as f:
        return json.load(f)

def apply_pre_clustering_filter(
    candidates: CandidateList,
    clusters: List[Dict[str, Any]],
    reduction_threshold: float = 0.30
) -> CandidateList:
    """
    Apply MinHash-LSH pre-clustering to filter redundant candidates.
    Returns a reduced candidate list and logs the reduction ratio.
    """
    if not clusters:
        logger.warning("No clusters provided, skipping pre-clustering filter.")
        return candidates

    original_size = len(candidates.items)
    filtered_items = filter_candidates_by_clustering(candidates, clusters)
    filtered_size = len(filtered_items)

    reduction_ratio = 1.0 - (filtered_size / original_size) if original_size > 0 else 0.0
    logger.info(f"Pre-clustering filter applied: {original_size} -> {filtered_size} "
                f"(reduction: {reduction_ratio:.2%})")

    if reduction_ratio < reduction_threshold:
        logger.warning(f"Reduction ratio {reduction_ratio:.2%} is below threshold {reduction_threshold:.2%}. "
                       "Continuing with filtered list, but this may indicate poor clustering.")

    return CandidateList(items=filtered_items, metadata=candidates.metadata)

def run_ranker_with_filter(
    candidates: CandidateList,
    budget: int,
    clusters: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Run the active ranker on the candidate list, optionally applying pre-clustering.
    Returns ranking results and metrics.
    """
    if clusters:
        candidates = apply_pre_clustering_filter(candidates, clusters)

    # Placeholder for actual ranking logic (to be implemented in US2)
    # For now, return a mock result structure
    return {
        "ranked_items": candidates.items[:budget],
        "budget_used": min(budget, len(candidates.items)),
        "metrics": {
            "total_candidates": len(candidates.items),
            "budget": budget
        }
    }

def validate_proxy_consensus(
    sample_path: str,
    prompt_template_path: str,
    output_path: str,
    model_name: str = "llama3:8b-instruct-q4_K_M"
) -> Dict[str, Any]:
    """
    Validate the cosine similarity proxy against LLM consensus.
    
    Loads a sample of flagged pairs from sample_path, sends them to a local LLM
    via Ollama (or transformers) for ground-truth verification, and computes
    the accuracy of the proxy (cosine > 0.95).
    
    Args:
        sample_path: Path to JSON file containing list of sample indices or pair data.
        prompt_template_path: Path to the prompt template file.
        output_path: Path to write the results JSON.
        model_name: Name of the Ollama model to use.
    
    Returns:
        Dict with keys: accuracy (float), total_samples (int), agreed (int).
    """
    import subprocess
    import time

    # Load the sample
    if not os.path.exists(sample_path):
        raise FileNotFoundError(f"Sample file not found: {sample_path}")
    
    with open(sample_path, 'r') as f:
        sample_data = json.load(f)
    
    # Handle both list of indices (if we need to reload from log) or list of dicts
    # Based on T013b, it writes indices. We need to load the full log to get the pairs.
    comparison_log_path = "data/processed/comparison_log.json"
    if not os.path.exists(comparison_log_path):
        raise FileNotFoundError(f"Comparison log not found: {comparison_log_path}")
    
    with open(comparison_log_path, 'r') as f:
        full_log = json.load(f)
    
    # If sample_data is a list of indices
    if isinstance(sample_data, list) and len(sample_data) > 0 and isinstance(sample_data[0], (int, str)):
        indices = [int(i) for i in sample_data]
        pairs_to_validate = [full_log[i] for i in indices if i < len(full_log)]
    else:
        # Assume it's already a list of pair dicts
        pairs_to_validate = sample_data

    if not pairs_to_validate:
        logger.warning("No pairs to validate in sample.")
        result = {"accuracy": 0.0, "total_samples": 0, "agreed": 0}
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        return result

    # Load prompt template
    if not os.path.exists(prompt_template_path):
        raise FileNotFoundError(f"Prompt template not found: {prompt_template_path}")
    
    with open(prompt_template_path, 'r') as f:
        template = f.read()

    logger.info(f"Starting LLM consensus validation on {len(pairs_to_validate)} samples.")
    
    agreed_count = 0
    total_count = len(pairs_to_validate)
    
    for i, pair in enumerate(pairs_to_validate):
        doc1 = pair.get("doc1_text") or pair.get("text1") or ""
        doc2 = pair.get("doc2_text") or pair.get("text2") or ""
        similarity = pair.get("cosine_similarity", 0.0)
        
        # Format prompt
        prompt = template.format(
            doc1=doc1[:1000], # Truncate to avoid context limits
            doc2=doc2[:1000],
            similarity=similarity
        )
        
        # Call Ollama
        try:
            response = subprocess.run(
                ["ollama", "run", model_name, prompt],
                capture_output=True,
                text=True,
                timeout=60 # 60s timeout per call
            )
            
            output = response.stdout.strip().upper()
            logger.debug(f"Sample {i}: LLM output: {output}")
            
            if "YES" in output:
                # LLM says they are redundant (near-duplicates)
                # Proxy says they are redundant if similarity > 0.95
                if similarity > 0.95:
                    agreed_count += 1
                    logger.debug(f"Sample {i}: AGREE (Proxy: Redundant, LLM: Redundant)")
                else:
                    logger.debug(f"Sample {i}: DISAGREE (Proxy: Unique, LLM: Redundant)")
            else:
                # LLM says they are NOT redundant
                if similarity <= 0.95:
                    agreed_count += 1
                    logger.debug(f"Sample {i}: AGREE (Proxy: Unique, LLM: Unique)")
                else:
                    logger.debug(f"Sample {i}: DISAGREE (Proxy: Redundant, LLM: Unique)")
                    
        except subprocess.TimeoutExpired:
            logger.error(f"Sample {i}: Ollama call timed out. Skipping.")
        except Exception as e:
            logger.error(f"Sample {i}: Error calling LLM: {e}. Skipping.")

    accuracy = agreed_count / total_count if total_count > 0 else 0.0
    result = {
        "accuracy": accuracy,
        "total_samples": total_count,
        "agreed": agreed_count
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Consensus validation complete. Accuracy: {accuracy:.4f} ({agreed_count}/{total_count})")
    return result

def main():
    """CLI entry point for ranker tasks."""
    import argparse
    parser = argparse.ArgumentParser(description="Active Ranker and Consensus Validation")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate Proxy Consensus command
    validate_parser = subparsers.add_parser("validate_consensus", help="Run LLM consensus validation")
    validate_parser.add_argument("--sample", required=True, help="Path to sample JSON")
    validate_parser.add_argument("--prompt", required=True, help="Path to prompt template")
    validate_parser.add_argument("--output", required=True, help="Path to output JSON")
    validate_parser.add_argument("--model", default="llama3:8b-instruct-q4_K_M", help="Ollama model name")

    args = parser.parse_args()

    if args.command == "validate_consensus":
        validate_proxy_consensus(
            sample_path=args.sample,
            prompt_template_path=args.prompt,
            output_path=args.output,
            model_name=args.model
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()