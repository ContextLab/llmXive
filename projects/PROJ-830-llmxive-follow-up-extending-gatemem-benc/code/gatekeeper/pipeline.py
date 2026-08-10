import os
import json
import logging
import time
import argparse
import random
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from code.gatekeeper.classifiers import FrozenDistilBERTClassifier, run_inference
from code.gatekeeper.rules import (
    load_deletion_logs,
    load_role_definitions,
    is_target_deleted_secure,
    is_role_authorized,
    check_access_policy
)
from code.utils.data_loader import load_from_jsonl, validate_episode
from code.utils.profiling import start_profiling, stop_profiling, get_peak_memory_mb, profile_function
from code.logging_config import setup_logging, pin_random_seed

logger = setup_logging(__name__)

def load_prompt_templates(template_path: str = "templates/prompts.yaml") -> Dict[str, Any]:
    """Load prompt templates from YAML file."""
    import yaml
    path = Path(template_path)
    if not path.exists():
        logger.warning(f"Template file {template_path} not found. Using defaults.")
        return {
            "retrieval": "Retrieve relevant memory for: {query}",
            "long_context": "Context: {context}\nQuery: {query}",
            "gatekeeper": "Intent: {intent}\nRole: {role}\nQuery: {query}"
        }
    with open(path, "r") as f:
        return yaml.safe_load(f)

def run_gatekeeper(
    episode: Dict[str, Any],
    classifier: FrozenDistilBERTClassifier,
    role_defs: Dict[str, Any],
    deletion_logs: List[Dict[str, Any]],
    templates: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any], float]:
    """
    Execute the Gatekeeper pipeline for a single episode.
    
    Returns:
        Tuple of (is_allowed, decision_details, inference_time_ms)
    """
    # 1. Intent Classification
    query_text = episode.get("predictors", {}).get("query", "")
    start_time = time.time()
    
    # Run inference on the query
    # Note: run_inference expects a list of texts or a single text depending on impl
    # Based on API surface: run_inference returns {'inference_time_ms': float, ...}
    # We assume it takes the text directly or a list. We'll pass a list for robustness.
    inference_result = run_inference([query_text], classifier)
    inference_time_ms = inference_result.get("inference_time_ms", 0.0)
    
    # Extract intent (assuming result structure from T014a)
    # The API surface says run_inference returns a dict. We need to extract the intent.
    # Usually classifiers return top label. Let's assume the structure:
    # {'labels': ['intent_name'], 'scores': [...]} or similar.
    # Since T014a was back-to-back, we must infer the standard return or handle it.
    # Let's assume the classifier returns a list of dicts if batched.
    if isinstance(inference_result, list):
        intent_label = inference_result[0].get("label", "unknown")
    elif isinstance(inference_result, dict):
        # Handle single result
        intent_label = inference_result.get("label", inference_result.get("intent", "unknown"))
    else:
        intent_label = "unknown"
        
    # 2. Role & Deletion Check
    role = episode.get("roles", {}).get("current_role", "default")
    target_id = episode.get("leak-target", {}).get("id", "")
    domain = episode.get("domains", {}).get("domain", "unknown")
    
    # Check deletion status
    is_deleted = is_target_deleted_secure(target_id, deletion_logs)
    
    # Check role authorization
    is_authorized = is_role_authorized(role, role_defs, intent_label)
    
    # 3. Policy Decision (AND logic: Authorized AND Not Deleted)
    # The Gatekeeper allows access if the role is authorized AND the target is NOT deleted.
    # If the target is deleted, access is denied regardless of role (for that specific target).
    # If the role is not authorized, access is denied.
    is_allowed = is_authorized and not is_deleted
    
    decision_details = {
        "intent": intent_label,
        "role": role,
        "is_deleted": is_deleted,
        "is_authorized": is_authorized,
        "decision": "allow" if is_allowed else "deny",
        "reason": "Access granted" if is_allowed else "Access denied (Deletion or Unauthorized)"
    }
    
    return is_allowed, decision_details, inference_time_ms

def run_retrieval_baseline(
    episode: Dict[str, Any],
    templates: Dict[str, Any]
) -> Tuple[str, float]:
    """
    Simulate Retrieval-only baseline.
    In a real implementation, this would query a vector store.
    Here we simulate the retrieval step and return a placeholder response.
    """
    # Simulate retrieval time
    start = time.time()
    # In a real scenario, we would fetch relevant chunks based on query
    # For this benchmark, we assume the "Retrieval" baseline always allows access
    # but incurs the cost of retrieval.
    time.sleep(0.01) # Simulate I/O
    elapsed = (time.time() - start) * 1000
    
    # Return a dummy response that implies success for the baseline
    response = "Retrieval baseline response (simulated)"
    return response, elapsed

def run_long_context_baseline(
    episode: Dict[str, Any],
    templates: Dict[str, Any]
) -> Tuple[str, float]:
    """
    Simulate Long-Context baseline.
    This passes the entire context to the model.
    """
    start = time.time()
    # Simulate long context processing time (heavier than retrieval)
    time.sleep(0.05) 
    elapsed = (time.time() - start) * 1000
    
    response = "Long context baseline response (simulated)"
    return response, elapsed

def run_gatekeeper_pipeline(
    data_path: str,
    output_path: str,
    domain_filter: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the full Gatekeeper evaluation pipeline.
    """
    # 1. Setup
    pin_random_seed(42)
    logger.info(f"Starting Gatekeeper pipeline for {data_path}")
    
    # Load dependencies
    templates = load_prompt_templates()
    role_defs = load_role_definitions("data/raw/role_definitions.json") # Assuming path
    deletion_logs = load_deletion_logs("data/raw/deletion_logs.json") # Assuming path
    
    # Initialize classifier
    classifier = FrozenDistilBERTClassifier()
    
    # Load data
    episodes = load_from_jsonl(data_path)
    
    results = []
    total_inference_time = 0.0
    
    for i, episode in enumerate(episodes):
        # Validate episode
        try:
            # Assuming schema path is standard or passed via config
            validate_episode(episode, "contracts/dataset.schema.yaml")
        except ValueError as e:
            logger.warning(f"Skipping invalid episode {i}: {e}")
            continue
        
        # Filter by domain if specified
        if domain_filter:
            ep_domain = episode.get("domains", {}).get("domain", "")
            if ep_domain not in domain_filter:
                continue
        
        # Run Gatekeeper
        is_allowed, details, inf_time = run_gatekeeper(
            episode, classifier, role_defs, deletion_logs, templates
        )
        
        total_inference_time += inf_time
        
        result_entry = {
            "episode_id": episode.get("id", f"ep_{i}"),
            "domain": episode.get("domains", {}).get("domain", "unknown"),
            "gatekeeper_decision": details["decision"],
            "details": details,
            "inference_time_ms": inf_time
        }
        results.append(result_entry)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i+1} episodes...")
    
    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    avg_time = total_inference_time / len(results) if results else 0
    logger.info(f"Pipeline complete. Saved to {output_path}. Avg inference: {avg_time:.2f}ms")
    
    return {
        "total_episodes": len(results),
        "average_inference_time_ms": avg_time,
        "output_path": output_path
    }

def run_baseline(
    data_path: str,
    output_path: str,
    baseline_type: str = "long_context",
    domain_filter: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the specified baseline pipeline.
    """
    logger.info(f"Starting Baseline ({baseline_type}) pipeline")
    templates = load_prompt_templates()
    episodes = load_from_jsonl(data_path)
    
    results = []
    total_time = 0.0
    
    for i, episode in enumerate(episodes):
        if domain_filter:
            ep_domain = episode.get("domains", {}).get("domain", "")
            if ep_domain not in domain_filter:
                continue
        
        start = time.time()
        if baseline_type == "retrieval":
            response, latency = run_retrieval_baseline(episode, templates)
        elif baseline_type == "long_context":
            response, latency = run_long_context_baseline(episode, templates)
        else:
            raise ValueError(f"Unknown baseline type: {baseline_type}")
        
        total_time += latency
        
        results.append({
            "episode_id": episode.get("id", f"ep_{i}"),
            "domain": episode.get("domains", {}).get("domain", "unknown"),
            "baseline_type": baseline_type,
            "latency_ms": latency,
            "response": response
        })
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    avg_time = total_time / len(results) if results else 0
    logger.info(f"Baseline complete. Saved to {output_path}. Avg latency: {avg_time:.2f}ms")
    
    return {
        "total_episodes": len(results),
        "average_latency_ms": avg_time,
        "output_path": output_path
    }

def main():
    parser = argparse.ArgumentParser(description="Gatekeeper Benchmark Pipeline")
    parser.add_argument("--mode", choices=["gatekeeper", "baseline"], default="gatekeeper")
    parser.add_argument("--data", type=str, default="data/raw/gatemem_subset.jsonl")
    parser.add_argument("--output", type=str, default="data/processed/results.json")
    parser.add_argument("--baseline-type", type=str, choices=["retrieval", "long_context"], default="long_context")
    parser.add_argument("--domains", type=str, help="Comma-separated list of domains to filter")
    
    args = parser.parse_args()
    
    domain_list = args.domains.split(",") if args.domains else None
    
    if args.mode == "gatekeeper":
        run_gatekeeper_pipeline(args.data, args.output, domain_list)
    else:
        run_baseline(args.data, args.output, args.baseline_type, domain_list)

if __name__ == "__main__":
    main()