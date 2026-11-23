"""
Gatekeeper Pipeline Implementation.

Orchestrates the execution of Gatekeeper and Baseline evaluation pipelines.
Provides entry points for running Gatekeeper logic, baseline comparisons,
and CLI argument parsing.
"""

import os
import json
import logging
import time
import argparse
import random
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from existing API surface
from code.utils.data_loader import fetch_dataset, validate_episode, extract_fields
from code.utils.profiling import profile_execution
from code.gatekeeper.classifiers import run_inference, FrozenDistilBERTClassifier
from code.gatekeeper.rules import check_access_policy, parse_deletion_log, parse_role_definitions
from code.logging_config import setup_logging, pin_random_seed

# Configure logging
logger = setup_logging("pipeline")

# Constants
PROMPT_TEMPLATES_PATH = "templates/prompts.yaml"
RESULTS_DIR = Path("data/processed")
LOGS_DIR = Path("logs")


def load_prompt_templates() -> Dict[str, str]:
    """
    Load prompt templates from the YAML configuration file.
    Ensures identical prompts are used for Gatekeeper and Baselines.
    """
    if not os.path.exists(PROMPT_TEMPLATES_PATH):
        logger.warning(f"Prompt templates file not found at {PROMPT_TEMPLATES_PATH}. Using defaults.")
        return {
            "gatekeeper_prompt": "You are a helpful assistant. Answer the query based on the retrieved context.",
            "retrieval_only_prompt": "You are a helpful assistant. Answer the query based on the retrieved context.",
            "long_context_prompt": "You are a helpful assistant. Answer the query based on the retrieved context."
        }

    try:
        import yaml
        with open(PROMPT_TEMPLATES_PATH, 'r') as f:
            templates = yaml.safe_load(f)
        logger.info(f"Loaded prompt templates from {PROMPT_TEMPLATES_PATH}")
        return templates
    except Exception as e:
        logger.error(f"Failed to load prompt templates: {e}")
        return {
            "gatekeeper_prompt": "You are a helpful assistant. Answer the query based on the retrieved context.",
            "retrieval_only_prompt": "You are a helpful assistant. Answer the query based on the retrieved context.",
            "long_context_prompt": "You are a helpful assistant. Answer the query based on the retrieved context."
        }


def run_gatekeeper_episode(episode: Dict[str, Any], prompt_templates: Dict[str, str]) -> Dict[str, Any]:
    """
    Execute the Gatekeeper logic for a single episode.
    1. Extract fields.
    2. Check rules (deletion log, role authorization).
    3. Run classifier for intent.
    4. Combine results (AND logic) to decide access.
    5. Generate response if allowed.
    6. Profile execution.
    """
    profile_start = time.time()
    tracemalloc_start = None
    try:
        import tracemalloc
        tracemalloc.start()
        tracemalloc_start = tracemalloc.get_traced_memory()[0]
    except Exception:
        pass

    result = {
        "episode_id": episode.get("episode_id", "unknown"),
        "method": "gatekeeper",
        "score": 0.0,  # Placeholder for actual metric calculation
        "access_decision": "unknown",
        "latency_ms": 0.0,
        "peak_ram_mb": 0.0
    }

    try:
        # Extract fields
        fields = extract_fields(episode)
        if not fields:
            logger.warning(f"Episode {episode.get('episode_id')} missing required fields.")
            result["access_decision"] = "deny"
            result["score"] = 0.0
            return result

        # Rule Engine Check
        # Check deletion logs
        deletion_log = episode.get("deletion_log", [])
        role_def = episode.get("role_definitions", [])
        
        is_deleted = False
        if deletion_log:
            parsed_log = parse_deletion_log(deletion_log)
            # Check if target is deleted
            if parsed_log and is_target_deleted(parsed_log, fields.get("target_id")):
                is_deleted = True

        is_authorized = True
        if role_def:
            parsed_roles = parse_role_definitions(role_def)
            if parsed_roles:
                is_authorized = is_role_authorized(parsed_roles, fields.get("user_role"), fields.get("target_id"))

        # Classifier Check
        classifier = FrozenDistilBERTClassifier(device='cpu')
        inference_result = run_inference(episode.get("query", ""), classifier)
        intent_score = inference_result.get("score", 0.0)
        intent_label = inference_result.get("label", "unknown")

        # AND Logic: Must be authorized AND NOT deleted AND intent must be allowed
        # Simplified logic for skeleton: if authorized and not deleted, allow
        if is_authorized and not is_deleted:
            result["access_decision"] = "allow"
            # In a full implementation, we would generate the response here
            result["score"] = 1.0  # Placeholder
        else:
            result["access_decision"] = "deny"
            result["score"] = 0.0

    except Exception as e:
        logger.error(f"Error processing Gatekeeper episode {episode.get('episode_id')}: {e}")
        result["access_decision"] = "error"
        result["score"] = 0.0

    # Profiling
    if tracemalloc_start is not None:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result["peak_ram_mb"] = peak / (1024 * 1024)
    
    profile_end = time.time()
    result["latency_ms"] = (profile_end - profile_start) * 1000

    return result


def run_baseline_episode(episode: Dict[str, Any], baseline_type: str = "retrieval") -> Dict[str, Any]:
    """
    Execute the Baseline logic for a single episode.
    Baselines do not use the Gatekeeper classifier or rules.
    They simply attempt to answer the query.
    """
    profile_start = time.time()
    tracemalloc_start = None
    try:
        import tracemalloc
        tracemalloc.start()
        tracemalloc_start = tracemalloc.get_traced_memory()[0]
    except Exception:
        pass

    result = {
        "episode_id": episode.get("episode_id", "unknown"),
        "method": f"baseline_{baseline_type}",
        "score": 0.0,
        "latency_ms": 0.0,
        "peak_ram_mb": 0.0
    }

    try:
        # Baseline logic: Just attempt to answer (simulated here)
        # In a full implementation, this would call the LLM directly
        result["score"] = 1.0 # Placeholder for successful baseline response
    except Exception as e:
        logger.error(f"Error processing Baseline episode {episode.get('episode_id')}: {e}")
        result["score"] = 0.0

    # Profiling
    if tracemalloc_start is not None:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result["peak_ram_mb"] = peak / (1024 * 1024)
    
    profile_end = time.time()
    result["latency_ms"] = (profile_end - profile_start) * 1000

    return result


def run_gatekeeper(domains: List[str], output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run the full Gatekeeper pipeline for specified domains.
    Fetches data, processes episodes, and writes results.
    """
    logger.info(f"Starting Gatekeeper pipeline for domains: {domains}")
    prompt_templates = load_prompt_templates()
    
    results = []
    try:
        # Fetch dataset (streaming)
        dataset = fetch_dataset(config="default", split="test", streaming=True)
        
        for episode in dataset:
            # Filter by domain if necessary (assuming episode has 'domain' field)
            if "domain" in episode and episode["domain"] not in domains:
                continue
            
            episode_result = run_gatekeeper_episode(episode, prompt_templates)
            results.append(episode_result)
            
    except Exception as e:
        logger.error(f"Critical error in Gatekeeper pipeline: {e}")
        raise

    # Write results
    if output_path is None:
        output_path = RESULTS_DIR / "gatekeeper_results.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Gatekeeper results written to {output_path}")
    return results


def run_baseline(domains: List[str], baseline_type: str = "retrieval", output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run the Baseline pipeline for specified domains.
    """
    logger.info(f"Starting Baseline pipeline ({baseline_type}) for domains: {domains}")
    
    results = []
    try:
        dataset = fetch_dataset(config="default", split="test", streaming=True)
        
        for episode in dataset:
            if "domain" in episode and episode["domain"] not in domains:
                continue
            
            episode_result = run_baseline_episode(episode, baseline_type)
            results.append(episode_result)
            
    except Exception as e:
        logger.error(f"Critical error in Baseline pipeline: {e}")
        raise

    if output_path is None:
        output_path = RESULTS_DIR / f"baseline_{baseline_type}_results.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Baseline results written to {output_path}")
    return results


def main():
    """
    CLI entry point for the pipeline.
    Parses arguments and dispatches to run_gatekeeper or run_baseline.
    """
    parser = argparse.ArgumentParser(description="Gatekeeper and Baseline Evaluation Pipeline")
    parser.add_argument("--mode", choices=["gatekeeper", "baseline"], required=True,
                      help="Execution mode: 'gatekeeper' or 'baseline'")
    parser.add_argument("--domains", type=str, default="medical,office",
                      help="Comma-separated list of domains to evaluate (e.g., 'medical,office')")
    parser.add_argument("--baseline-type", type=str, choices=["retrieval", "longcontext"], default="retrieval",
                      help="Type of baseline to run (only for mode=baseline)")
    parser.add_argument("--output", type=str, default=None,
                      help="Custom output path for results")
    
    args = parser.parse_args()
    
    # Pin random seed for reproducibility
    pin_random_seed(42)
    
    domains = [d.strip() for d in args.domains.split(",")]
    
    if args.mode == "gatekeeper":
        run_gatekeeper(domains, args.output)
    elif args.mode == "baseline":
        run_baseline(domains, args.baseline_type, args.output)


if __name__ == "__main__":
    main()