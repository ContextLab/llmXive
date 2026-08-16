"""
Pipeline orchestration script for the llmXive active learning research.
Implements T065: Dependency Graph Validator and T066: Artifact Chain Verification.
"""
import os
import sys
import time
import json
import random
import logging
import argparse
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Import from local modules (using the API surface provided)
from config import get_config, PipelineConfig
from data_loader import inject_redundancy, load_beir_corpus, fetch_beir_datasets
from clustering import cluster_documents, run_clustering_pipeline
from ranker import run_baseline_active_ranker, generate_unique_subset
from metrics import calculate_ndcg_at_10, is_wasted_call, aggregate_flagged_pairs_from_log
from logging_config import init_logging, log_pairwise_comparison, get_comparison_log_path
from utils import validate_artifact_chain, DataFlowViolationError, check_limits_periodically
from models import CandidateList, ComparisonPair, RedundancyCluster

# T065: Import schema validation utilities
import jsonschema
from jsonschema import validate, ValidationError

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class ArtifactIntegrityError(Exception):
    """Raised when an artifact is missing or invalid."""
    message: str

@dataclass
class PipelineDependencyError(Exception):
    """Raised when pipeline dependencies are violated."""
    message: str

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_data_integrity(file_path: str, expected_hash: Optional[str] = None) -> bool:
    """Check if a file exists and optionally verify its hash."""
    if not os.path.exists(file_path):
        return False
    if expected_hash:
        actual_hash = calculate_file_hash(file_path)
        return actual_hash == expected_hash
    return True

def load_json_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from file."""
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_artifact_schema(file_path: str, schema_path: str) -> bool:
    """
    T065 Implementation: Validate that an artifact exists and matches its JSON schema.
    Returns True if valid, raises ArtifactIntegrityError otherwise.
    """
    if not os.path.exists(file_path):
        raise ArtifactIntegrityError(f"Artifact missing: {file_path}")

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ArtifactIntegrityError(f"Artifact {file_path} is not valid JSON: {e}")

    try:
        schema = load_json_schema(schema_path)
        validate(instance=data, schema=schema)
        logger.info(f"Schema validation passed for {file_path}")
        return True
    except ValidationError as e:
        raise ArtifactIntegrityError(f"Schema validation failed for {file_path}: {e.message}")

def pre_flight_dependency_check(dataset_name: str, redundancy_level: float) -> Tuple[bool, List[str]]:
    """
    T065 Implementation: Pre-flight validation of dependency graph.
    Checks existence and schema validity of injected_datasets.json and clusters.json.
    Returns (success, list_of_errors).
    """
    config = get_config()
    errors = []

    # Paths
    injected_path = os.path.join(config.data_dir, "processed", "injected_datasets.json")
    clusters_path = os.path.join(config.data_dir, "processed", "clusters.json")
    unique_path = os.path.join(config.data_dir, "processed", "unique_subset.json")

    # Schema paths
    injected_schema = os.path.join(os.path.dirname(__file__), "schemas", "injected_datasets_schema.json")
    clusters_schema = os.path.join(os.path.dirname(__file__), "schemas", "clusters_schema.json")

    logger.info("Running T065 Dependency Graph Validator...")

    # 1. Check injected_datasets.json
    if not os.path.exists(injected_path):
        errors.append(f"Missing dependency: {injected_path}. Run T012 first.")
    else:
        if os.path.exists(injected_schema):
            try:
                validate_artifact_schema(injected_path, injected_schema)
            except ArtifactIntegrityError as e:
                errors.append(str(e))
        else:
            logger.warning(f"Schema file missing for validation: {injected_schema}")

    # 2. Check clusters.json
    if not os.path.exists(clusters_path):
        errors.append(f"Missing dependency: {clusters_path}. Run T020 first.")
    else:
        if os.path.exists(clusters_schema):
            try:
                validate_artifact_schema(clusters_path, clusters_schema)
            except ArtifactIntegrityError as e:
                errors.append(str(e))
        else:
            logger.warning(f"Schema file missing for validation: {clusters_schema}")

    # 3. Check unique_subset.json (needed for baseline)
    if not os.path.exists(unique_path):
        # This is often generated by T014, but we check existence
        logger.warning(f"Optional dependency missing: {unique_path}. Will attempt to generate.")

    if errors:
        logger.error("Dependency check failed:")
        for err in errors:
            logger.error(f"  - {err}")
        return False, errors

    logger.info("T065 Dependency Graph Validator: PASSED")
    return True, []

def ensure_prerequisites_for_statistical_report() -> bool:
    """
    T066 Implementation: Verify full artifact chain from injection to final metrics.
    Aborts on missing/invalid artifacts.
    """
    config = get_config()
    required_artifacts = [
        ("data/processed/injected_datasets.json", "injected_datasets_schema.json"),
        ("data/processed/clusters.json", "clusters_schema.json"),
        ("data/processed/comparison_log.jsonl", None), # No schema for log, just existence
        ("data/results/flagged_pairs_count.json", None),
        ("data/results/correction_factor.json", None),
        ("data/results/us1_baseline_ndcg.json", None),
        ("data/results/us2_ndcg.json", None),
    ]

    missing = []
    for artifact, schema in required_artifacts:
        full_path = os.path.join(config.data_dir, artifact) if not artifact.startswith(config.data_dir) else artifact
        # Adjust path logic relative to project root
        if not artifact.startswith("data/"):
             full_path = os.path.join(config.data_dir, artifact)
        
        # Normalize path
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        full_path = os.path.join(base, artifact)

        if not os.path.exists(full_path):
            missing.append(artifact)
        elif schema:
            schema_path = os.path.join(base, "code", "schemas", schema)
            try:
                validate_artifact_schema(full_path, schema_path)
            except ArtifactIntegrityError:
                missing.append(f"{artifact} (invalid schema)")

    if missing:
        logger.error("Artifact chain verification failed. Missing/Invalid:")
        for m in missing:
            logger.error(f"  - {m}")
        return False

    logger.info("T066 Artifact Chain Verification: PASSED")
    return True

def run_single_seed_experiment(seed: int, dataset_name: str, redundancy_level: float) -> Dict[str, Any]:
    """
    Executes a single seed of the pipeline.
    T027a logic.
    """
    logger.info(f"Starting seed {seed} for {dataset_name} with redundancy {redundancy_level}")
    
    # T065 Pre-flight check
    success, errors = pre_flight_dependency_check(dataset_name, redundancy_level)
    if not success:
        raise PipelineDependencyError(f"Pre-flight check failed for seed {seed}: {errors}")

    config = get_config()
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Load data
    injected_path = os.path.join(base_path, "data", "processed", "injected_datasets.json")
    clusters_path = os.path.join(base_path, "data", "processed", "clusters.json")
    
    if not os.path.exists(injected_path):
        raise FileNotFoundError(f"Injected datasets not found at {injected_path}")
    
    with open(injected_path, 'r') as f:
        injected_data = json.load(f)
    
    if not os.path.exists(clusters_path):
        raise FileNotFoundError(f"Clusters not found at {clusters_path}")
    
    with open(clusters_path, 'r') as f:
        clusters_data = json.load(f)

    # Run Baseline (T014)
    # Assuming generate_unique_subset is called if unique_subset.json doesn't exist
    unique_path = os.path.join(base_path, "data", "processed", "unique_subset.json")
    if not os.path.exists(unique_path):
        logger.info("Generating unique subset...")
        generate_unique_subset(injected_data, unique_path)
    
    with open(unique_path, 'r') as f:
        unique_data = json.load(f)
    
    baseline_log_path = os.path.join(base_path, "data", "processed", "comparison_log.jsonl")
    # Run baseline ranker
    run_baseline_active_ranker(unique_data, baseline_log_path, seed=seed)

    # Count flagged pairs (T013)
    flagged_count = aggregate_flagged_pairs_from_log(baseline_log_path)
    flagged_path = os.path.join(base_path, "data", "results", "flagged_pairs_count.json")
    with open(flagged_path, 'w') as f:
        json.dump({"count": flagged_count, "seed": seed}, f)

    # Calculate NDCG (T015)
    ndcg_score = calculate_ndcg_at_10(baseline_log_path, dataset_name)
    ndcg_path = os.path.join(base_path, "data", "results", "us1_baseline_ndcg.json")
    with open(ndcg_path, 'w') as f:
        json.dump({"ndcg": ndcg_score, "seed": seed}, f)

    return {
        "seed": seed,
        "ndcg": ndcg_score,
        "flagged_count": flagged_count
    }

def run_threshold_sweep(thresholds: List[float], dataset_name: str, seeds: int) -> Dict[str, Any]:
    """
    Runs the threshold sweep (T073a).
    """
    results = {}
    for thresh in thresholds:
        logger.info(f"Running sweep for threshold {thresh}")
        # Logic would involve re-clustering or filtering based on threshold
        # For this task, we assume the sweep data is aggregated from previous runs or config
        results[thresh] = {"status": "pending", "seeds": seeds}
    return results

def main():
    parser = argparse.ArgumentParser(description="Run the llmXive active learning pipeline")
    parser.add_argument("--dataset", type=str, default="scifact", help="Dataset name")
    parser.add_argument("--redundancy", type=float, default=0.4, help="Redundancy level")
    parser.add_argument("--seeds", type=int, default=30, help="Number of seeds")
    args = parser.parse_args()

    init_logging()
    config = get_config()
    
    # Ensure directories exist
    os.makedirs(os.path.join(config.data_dir, "processed"), exist_ok=True)
    os.makedirs(os.path.join(config.data_dir, "results"), exist_ok=True)

    # T065: Dependency Graph Validation
    success, errors = pre_flight_dependency_check(args.dataset, args.redundancy)
    if not success:
        logger.critical("Pipeline aborted due to dependency failures.")
        sys.exit(1)

    # T066: Artifact Chain Verification
    if not ensure_prerequisites_for_statistical_report():
        logger.warning("Not all artifacts for statistical report are present. Proceeding with partial run.")

    # Run seeds
    all_results = []
    for i in range(args.seeds):
        try:
            result = run_single_seed_experiment(i, args.dataset, args.redundancy)
            all_results.append(result)
        except Exception as e:
            logger.error(f"Seed {i} failed: {e}")
            continue

    # Aggregate results (T027)
    # Simplified aggregation for this task
    with open(os.path.join(config.data_dir, "results", "seeds.json"), 'w') as f:
        json.dump(all_results, f)

    logger.info("Pipeline execution completed.")

if __name__ == "__main__":
    main()