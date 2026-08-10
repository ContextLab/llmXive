"""
Pipeline orchestration for Gatekeeper and Baseline evaluations.

Implements entry points: run_gatekeeper(), run_baseline(), and main().
"""
import os
import json
import logging
import time
import argparse
import random
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import from project API surface
from code.utils.data_loader import fetch_gatemem, validate_fields, load_from_jsonl
from code.utils.profiling import start_profiling, stop_profiling, get_peak_memory_mb
from code.logging_config import setup_logging, pin_random_seed
from code.gatekeeper.classifiers import run_intent_classification
from code.gatekeeper.rules import check_access_policy, load_deletion_logs, load_role_definitions

logger = setup_logging(__name__)


def load_prompt_templates(template_path: str = "templates/prompts.yaml") -> Dict[str, Any]:
    """Load prompt templates from YAML file."""
    try:
        import yaml
        with open(template_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Template file {template_path} not found. Using defaults.")
        return {
            "retrieval": "Retrieve relevant memories for: {query}",
            "long_context": "Given the following context: {context}\nAnswer: {query}",
            "gatekeeper": "Analyze intent for: {query}"
        }


def run_retrieval_baseline(episodes: List[Dict[str, Any]], templates: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute Retrieval-only baseline.
    Simulates retrieval without long-context or gatekeeping.
    """
    results = []
    for episode in episodes:
        start_profiling()
        start_time = time.time()
        
        # Simulate retrieval logic (placeholder for actual retrieval implementation)
        # In a full implementation, this would query a vector store
        query = episode.get("covariates", {}).get("query", "")
        retrieved = [query[:50]] if query else [] # Mock retrieval
        
        end_time = time.time()
        stop_profiling()
        peak_ram = get_peak_memory_mb()
        
        results.append({
            "episode_id": episode.get("id"),
            "method": "retrieval_baseline",
            "latency_ms": (end_time - start_time) * 1000,
            "peak_ram_mb": peak_ram,
            "output": retrieved
        })
    return results


def run_long_context_baseline(episodes: List[Dict[str, Any]], templates: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute Long-Context baseline.
    Processes full context without filtering.
    """
    results = []
    for episode in episodes:
        start_profiling()
        start_time = time.time()
        
        # Simulate long context processing
        context = episode.get("predictors", {}).get("context", "")
        query = episode.get("covariates", {}).get("query", "")
        
        # Mock LLM response based on context length
        output_len = len(context) + len(query)
        output = f"Processed {output_len} tokens"
        
        end_time = time.time()
        stop_profiling()
        peak_ram = get_peak_memory_mb()
        
        results.append({
            "episode_id": episode.get("id"),
            "method": "long_context_baseline",
            "latency_ms": (end_time - start_time) * 1000,
            "peak_ram_mb": peak_ram,
            "output": output
        })
    return results


def run_gatekeeper(episodes: List[Dict[str, Any]], templates: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute Gatekeeper pipeline with intent classification and rule enforcement.
    """
    results = []
    deletion_logs = load_deletion_logs("data/raw/deletion_logs.jsonl")
    role_definitions = load_role_definitions("data/raw/role_definitions.json")

    for episode in episodes:
        start_profiling()
        start_time = time.time()
        
        query = episode.get("covariates", {}).get("query", "")
        roles = episode.get("roles", [])
        domains = episode.get("domains", [])
        
        # 1. Intent Classification
        intent_result = run_intent_classification([{"query": query}])
        intent = intent_result[0].get("intent", "unknown") if intent_result else "unknown"
        
        # 2. Rule Enforcement
        is_authorized = check_access_policy(
            roles=roles,
            domains=domains,
            query=query,
            deletion_logs=deletion_logs,
            role_definitions=role_definitions
        )
        
        # 3. Decision
        if is_authorized and intent != "deny":
            # Simulate allowed processing
            output = f"Allowed: {query}"
        else:
            output = "Blocked"
        
        end_time = time.time()
        stop_profiling()
        peak_ram = get_peak_memory_mb()
        
        results.append({
            "episode_id": episode.get("id"),
            "method": "gatekeeper",
            "latency_ms": (end_time - start_time) * 1000,
            "peak_ram_mb": peak_ram,
            "intent": intent,
            "authorized": is_authorized,
            "output": output
        })
    return results


def run_gatekeeper_pipeline(
    data_path: str,
    output_path: str,
    domains: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main orchestration for Gatekeeper evaluation.
    """
    logger.info(f"Starting Gatekeeper pipeline for {data_path}")
    
    # Load Data
    episodes = load_from_jsonl(data_path)
    if domains:
        episodes = [e for e in episodes if any(d in domains for d in e.get("domains", []))]
    
    if not episodes:
        logger.error("No episodes found matching criteria.")
        return {}

    templates = load_prompt_templates()
    results = run_gatekeeper(episodes, templates)
    
    # Save Results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Gatekeeper pipeline complete. Saved to {output_path}")
    return {"count": len(results), "path": output_path}


def run_baseline(
    data_path: str,
    output_path: str,
    baseline_type: str = "long_context",
    domains: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main orchestration for Baseline evaluation.
    """
    logger.info(f"Starting Baseline pipeline ({baseline_type}) for {data_path}")
    
    # Load Data
    episodes = load_from_jsonl(data_path)
    if domains:
        episodes = [e for e in episodes if any(d in domains for d in e.get("domains", []))]
    
    if not episodes:
        logger.error("No episodes found matching criteria.")
        return {}

    templates = load_prompt_templates()
    
    if baseline_type == "retrieval":
        results = run_retrieval_baseline(episodes, templates)
    elif baseline_type == "long_context":
        results = run_long_context_baseline(episodes, templates)
    else:
        raise ValueError(f"Unknown baseline type: {baseline_type}")
    
    # Save Results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Baseline pipeline complete. Saved to {output_path}")
    return {"count": len(results), "path": output_path}


def main():
    """CLI entry point for pipeline execution."""
    parser = argparse.ArgumentParser(description="Gatekeeper/Baseline Evaluation Pipeline")
    parser.add_argument("--mode", choices=["gatekeeper", "baseline"], required=True,
                      help="Mode: gatekeeper or baseline")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSONL data")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON results")
    parser.add_argument("--baseline-type", choices=["retrieval", "long_context"], default="long_context",
                      help="Type of baseline to run")
    parser.add_argument("--domains", type=str, default=None,
                      help="Comma-separated list of domains to filter (e.g., 'medical,office')")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Setup
    pin_random_seed(args.seed)
    domains = [d.strip() for d in args.domains.split(",")] if args.domains else None
    
    if args.mode == "gatekeeper":
        run_gatekeeper_pipeline(args.input, args.output, domains)
    else:
        run_baseline(args.input, args.output, args.baseline_type, domains)


if __name__ == "__main__":
    main()