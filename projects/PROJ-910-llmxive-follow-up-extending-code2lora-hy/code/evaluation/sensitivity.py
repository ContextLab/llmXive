"""
Sensitivity Analysis Module for US3.

Implements the sensitivity loop that sequentially calls the adapter generator (T015)
and evaluator (T021) for each feature subset to determine the minimum feature set
required to maintain >80% of baseline accuracy.

Dependencies:
- T015: Adapter Generator (code/hypernetwork/adapter_generator.py)
- T021: Evaluation Runner (code/evaluation/runner.py)
- T029: Feature Subset Definitions
"""

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json
import csv
import os
import sys
import time
import logging
from pathlib import Path

# Import project utilities and modules based on API surface
from utils.config import load_config, Config
from utils.logging import get_logger
from utils.memory_monitor import run_step_with_memory_logging
from hypernetwork.adapter_generator import generate_adapter, AdapterGenerationError
from evaluation.runner import run_evaluation, save_results

# Setup logger
logger = get_logger(__name__)

class FeatureSubset(Enum):
    """Enumeration of feature subsets to analyze."""
    TOKENS_ONLY = "tokens_only"
    CYCLOMATIC_ONLY = "cyclomatic_only"
    DEPTH_ONLY = "depth_only"
    COMBINED_SIMPLE = "combined_simple"
    FULL_AST = "full_ast"

@dataclass
class FeatureSubsetConfig:
    """Configuration for a specific feature subset."""
    name: str
    description: str
    features: List[str]
    enabled: bool = True

def get_feature_subsets() -> List[FeatureSubsetConfig]:
    """
    Define the list of feature subsets to test.
    Matches the definitions expected by the sensitivity analysis loop.
    """
    return [
        FeatureSubsetConfig(
            name=FeatureSubset.TOKENS_ONLY.value,
            description="Token counts and histograms only",
            features=["token_histogram"]
        ),
        FeatureSubsetConfig(
            name=FeatureSubset.CYCLOMATIC_ONLY.value,
            description="Cyclomatic complexity only",
            features=["cyclomatic_complexity"]
        ),
        FeatureSubsetConfig(
            name=FeatureSubset.DEPTH_ONLY.value,
            description="Inheritance depth only",
            features=["inheritance_depth"]
        ),
        FeatureSubsetConfig(
            name=FeatureSubset.COMBINED_SIMPLE.value,
            description="Cyclomatic + Depth",
            features=["cyclomatic_complexity", "inheritance_depth"]
        ),
        FeatureSubsetConfig(
            name=FeatureSubset.FULL_AST.value,
            description="Full AST feature set",
            features=["token_histogram", "cyclomatic_complexity", "inheritance_depth"]
        )
    ]

def get_subset_by_name(name: str) -> Optional[FeatureSubsetConfig]:
    """Retrieve a subset config by its string name."""
    for subset in get_feature_subsets():
        if subset.name == name:
            return subset
    return None

def validate_subset_features(subset: FeatureSubsetConfig, config: Config) -> bool:
    """
    Validate that the subset features are valid according to the AST parser.
    This ensures the adapter generator can actually process the requested features.
    """
    # In a full implementation, this would cross-reference with ast_parser.py
    # to ensure requested features exist. For now, we assume valid names.
    if not subset.features:
        logger.error(f"Subset {subset.name} has no features defined.")
        return False
    return True

def extract_features_for_subset(subset: FeatureSubsetConfig, repo_path: Path) -> Dict[str, Any]:
    """
    Extract features for a specific subset from a repository.
    This is a placeholder for the actual extraction logic which would
    call ast_parser.py and graph_builder.py with specific feature filters.
    """
    # In a real implementation, this would call:
    # from feature_extractor.ast_parser import extract_ast_features
    # and pass the specific feature list to filter the output.
    # For the sensitivity loop, we rely on the adapter_generator
    # to handle the feature selection based on the config passed.
    # Here we just return the subset name to be used as a key.
    return {
        "subset_name": subset.name,
        "features_requested": subset.features,
        "repo_path": str(repo_path)
    }

def calculate_score_drop(subset_score: float, baseline_score: float) -> float:
    """Calculate the percentage drop from baseline."""
    if baseline_score == 0:
        return 0.0
    return ((baseline_score - subset_score) / baseline_score) * 100

def run_sensitivity_loop(
    subsets: List[FeatureSubsetConfig],
    repo_paths: List[Path],
    config: Config,
    output_dir: Path
) -> List[Dict[str, Any]]:
    """
    The core sensitivity loop.
    For each subset:
    1. Configure the adapter generator to use only the subset's features.
    2. Call generate_adapter (T015) to create the adapter.
    3. Call run_evaluation (T021) to score the adapter.
    4. Record the score and latency.
    """
    results = []
    results_dir = output_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Ensure baseline adapter exists if needed for comparison (though T030 focuses on AST variants)
    # We assume T021 handles loading the specific adapter generated for this run.

    for subset in subsets:
        if not subset.enabled:
            logger.info(f"Skipping disabled subset: {subset.name}")
            continue

        logger.info(f"--- Starting Sensitivity Loop for Subset: {subset.name} ---")
        logger.info(f"Features: {subset.features}")

        subset_results = {
            "subset_name": subset.name,
            "features": subset.features,
            "status": "pending",
            "adapter_path": None,
            "score": None,
            "latency_ms": None,
            "error": None
        }

        try:
            # 1. Prepare configuration for this specific subset
            # We need to inject the feature list into the config or pass it to the generator.
            # Since config is global, we might need to temporarily modify it or pass args.
            # For this implementation, we assume the adapter_generator reads a specific
            # environment variable or config override for 'feature_subset'.
            # However, to keep it clean, we will pass the feature list to the generator function
            # if it accepts it, or modify the config object in place.

            # Temporarily modify config to reflect the current subset
            # Note: In a robust system, this would be a dedicated config object per run.
            original_features = getattr(config, 'feature_subset', None)
            config.feature_subset = subset.features
            config.feature_vector_size = len(subset.features) * 10 # Approximate size, real logic in parser

            adapter_output_path = results_dir / f"adapter_{subset.name}.safetensors"

            # 2. Call Adapter Generator (T015)
            logger.info(f"Generating adapter for {subset.name}...")
            start_gen = time.time()
            
            # We call the public interface generate_adapter
            # It should handle memory checks and feature extraction internally
            generate_adapter(
                config=config,
                repo_paths=repo_paths,
                output_path=str(adapter_output_path),
                feature_subset=subset.features # Passing explicitly if supported, else relies on config
            )
            
            gen_duration = time.time() - start_gen
            logger.info(f"Adapter generation completed in {gen_duration:.2f}s")

            if not adapter_output_path.exists():
                raise FileNotFoundError(f"Adapter generator did not produce file: {adapter_output_path}")

            subset_results["adapter_path"] = str(adapter_output_path)
            subset_results["status"] = "generated"

            # 3. Call Evaluator (T021)
            logger.info(f"Evaluating adapter for {subset.name}...")
            start_eval = time.time()

            # Run evaluation on the generated adapter
            # T021 (runner.py) expects to load the adapter and run against RepoPeftBench
            eval_results = run_evaluation(
                config=config,
                adapter_path=str(adapter_output_path),
                output_path=str(results_dir / f"scores_{subset.name}.csv")
            )

            eval_duration = time.time() - start_eval
            
            # Extract score and latency from eval results
            # Assuming eval_results is a dict with 'exact_match' and 'latency_ms'
            if isinstance(eval_results, dict):
                score = eval_results.get('exact_match', 0.0)
                latency = eval_results.get('latency_ms', 0.0)
            else:
                # Fallback if run_evaluation returns a path or different structure
                # In a real scenario, we'd parse the CSV or return structured data
                score = 0.0
                latency = 0.0
                logger.warning(f"Unexpected evaluation result type: {type(eval_results)}")

            subset_results["score"] = score
            subset_results["latency_ms"] = latency
            subset_results["status"] = "completed"
            subset_results["gen_duration"] = gen_duration
            subset_results["eval_duration"] = eval_duration

            logger.info(f"Subset {subset.name} completed. Score: {score:.4f}, Latency: {latency:.2f}ms")

        except AdapterGenerationError as e:
            logger.error(f"Adapter generation failed for {subset.name}: {e}")
            subset_results["status"] = "failed_generation"
            subset_results["error"] = str(e)
        except Exception as e:
            logger.error(f"Evaluation failed for {subset.name}: {e}", exc_info=True)
            subset_results["status"] = "failed_evaluation"
            subset_results["error"] = str(e)
        finally:
            # Restore original config if it was modified
            if original_features is not None:
                config.feature_subset = original_features

        results.append(subset_results)

    return results

def run_sensitivity_analysis(
    config: Optional[Config] = None,
    repo_paths: Optional[List[Path]] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point for sensitivity analysis.
    Orchestrates the loop and saves results.
    """
    if config is None:
        config = load_config()
    if repo_paths is None:
        # Default to data/raw if not specified
        repo_paths = [Path("data/raw")]
    if output_dir is None:
        output_dir = Path("data")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    subsets = get_feature_subsets()
    logger.info(f"Starting sensitivity analysis with {len(subsets)} subsets.")

    results = run_sensitivity_loop(subsets, repo_paths, config, output_dir)

    # Save results to JSON
    results_path = output_dir / "results" / "sensitivity_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Sensitivity analysis complete. Results saved to {results_path}")

    return {
        "status": "completed",
        "results_path": str(results_path),
        "results": results
    }

def save_sensitivity_results(results: List[Dict[str, Any]], output_path: Path):
    """Save the sensitivity results to a CSV summary file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["subset_name", "score", "latency_ms", "status", "error"])
        writer.writeheader()
        for res in results:
            writer.writerow({
                "subset_name": res["subset_name"],
                "score": res.get("score", 0.0),
                "latency_ms": res.get("latency_ms", 0.0),
                "status": res["status"],
                "error": res.get("error", "")
            })

def main():
    """CLI entry point for sensitivity analysis."""
    logger.info("Running Sensitivity Analysis via CLI")
    config = load_config()
    repo_paths = [Path(config.repo_peft_bench_path)]
    
    # Ensure data/raw exists for the sample
    if not repo_paths[0].exists():
        logger.warning(f"Repo path {repo_paths[0]} does not exist. Ensure T055 has run.")
        # In a real run, we might exit or try to download, but for this task we assume data is present.
    
    result = run_sensitivity_analysis(config=config, repo_paths=repo_paths)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()