import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from models import CandidateList
from clustering import filter_candidates_by_clustering, MinHashCluster
import requests
import time
import random

# Configure logger
logger = logging.getLogger(__name__)

def load_cluster_results(path: str) -> List[MinHashCluster]:
    """Load cluster results from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cluster results file not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    clusters = []
    for item in data:
        clusters.append(MinHashCluster(**item))
    return clusters

def apply_pre_clustering_filter(
    candidates: CandidateList,
    clusters: List[MinHashCluster],
    threshold: float = 0.95
) -> CandidateList:
    """Filter candidates using MinHash-LSH clustering results."""
    filtered_candidates = filter_candidates_by_clustering(candidates, clusters, threshold)
    logger.info(f"Pre-clustering filter reduced candidates from {len(candidates.items)} to {len(filtered_candidates.items)}")
    return filtered_candidates

def run_ranker_with_filter(
    candidates: CandidateList,
    clusters: Optional[List[MinHashCluster]] = None,
    budget: int = 100
) -> Dict[str, Any]:
    """Run the active ranker with optional pre-clustering filter."""
    if clusters:
        candidates = apply_pre_clustering_filter(candidates, clusters)
    
    # Placeholder for actual ranking logic
    # In a real implementation, this would call the LLM or other ranking mechanism
    results = {
        "ranked_items": candidates.items[:budget],
        "budget_used": min(budget, len(candidates.items)),
        "total_candidates": len(candidates.items)
    }
    return results

def validate_proxy_consensus(
    sample_indices: List[int],
    comparison_logs_path: str,
    output_path: str = "data/results/consensus_accuracy.json",
    model_name: str = "llama3:8b-instruct-q4_0",
    temperature: float = 0.0,
    max_tokens: int = 200
) -> Dict[str, Any]:
    """
    Validate the cosine similarity proxy against LLM consensus.
    
    This function:
    1. Loads the stratified sample from `data/results/consensus_sample.json`
    2. Loads the comparison logs to get document pairs and similarity scores
    3. Calls a local LLM (via Ollama) to determine if each pair is redundant
    4. Compares LLM decisions with the cosine proxy (>0.95)
    5. Writes accuracy metrics to `output_path`
    
    Args:
        sample_indices: List of indices to validate (from consensus_sample.json)
        comparison_logs_path: Path to the JSON log of pairwise comparisons
        output_path: Path to write the accuracy results
        model_name: Ollama model name to use
        temperature: Temperature for LLM sampling (0.0 for deterministic)
        max_tokens: Max tokens for LLM response
    
    Returns:
        Dictionary with accuracy metrics
    """
    logger.info(f"Starting LLM consensus validation for {len(sample_indices)} samples")
    
    # Load comparison logs
    if not os.path.exists(comparison_logs_path):
        raise FileNotFoundError(f"Comparison logs not found: {comparison_logs_path}")
    
    with open(comparison_logs_path, 'r') as f:
        logs = json.load(f)
    
    # Ensure sample indices are within bounds
    valid_indices = [i for i in sample_indices if i < len(logs)]
    if len(valid_indices) != len(sample_indices):
        logger.warning(f"Filtered {len(sample_indices) - len(valid_indices)} invalid indices")
    
    # Load prompt template
    prompt_template_path = "code/prompts/consensus_validation.txt"
    if not os.path.exists(prompt_template_path):
        raise FileNotFoundError(f"Prompt template not found: {prompt_template_path}")
    
    with open(prompt_template_path, 'r') as f:
        prompt_template = f.read()
    
    # Ollama API endpoint
    ollama_url = "http://localhost:11434/api/generate"
    
    results = []
    correct = 0
    total = 0
    
    for idx in valid_indices:
        log_entry = logs[idx]
        doc1 = log_entry.get("doc1", "")
        doc2 = log_entry.get("doc2", "")
        similarity = log_entry.get("similarity", 0.0)
        
        # Prepare prompt
        prompt = prompt_template.format(
            doc1=doc1[:2000],  # Truncate if too long
            doc2=doc2[:2000],
            similarity=similarity
        )
        
        # Call Ollama
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(ollama_url, json=payload, timeout=60)
            response.raise_for_status()
            result_data = response.json()
            llm_answer = result_data.get("response", "").strip().upper()
            
            # Parse LLM answer (expecting YES/NO)
            is_llm_redundant = "YES" in llm_answer
            is_proxy_redundant = similarity > 0.95
            
            match = (is_llm_redundant == is_proxy_redundant)
            if match:
                correct += 1
            total += 1
            
            results.append({
                "index": idx,
                "similarity": similarity,
                "proxy_decision": is_proxy_redundant,
                "llm_decision": is_llm_redundant,
                "match": match
            })
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama call failed for index {idx}: {e}")
            # Skip this sample if LLM is unavailable
            continue
    
    # Calculate metrics
    accuracy = correct / total if total > 0 else 0.0
    
    metrics = {
        "total_samples": len(valid_indices),
        "successful_validations": total,
        "llm_agreements": correct,
        "accuracy": accuracy,
        "details": results
    }
    
    # Write results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Consensus validation complete. Accuracy: {accuracy:.2f} ({correct}/{total})")
    return metrics

def main():
    """Main entry point for the ranker module."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage for validation
    if os.path.exists("data/results/consensus_sample.json"):
        with open("data/results/consensus_sample.json", 'r') as f:
            sample_indices = json.load(f)
        
        metrics = validate_proxy_consensus(
            sample_indices=sample_indices,
            comparison_logs_path="data/processed/comparison_logs.json",
            output_path="data/results/consensus_accuracy.json"
        )
        print(json.dumps(metrics, indent=2))
    else:
        logger.warning("No consensus sample found. Run sampling first.")

if __name__ == "__main__":
    main()
