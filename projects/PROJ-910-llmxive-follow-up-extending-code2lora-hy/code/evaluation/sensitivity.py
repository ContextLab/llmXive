"""
Sensitivity analysis module for User Story 3.

Implements the sensitivity loop that sequentially calls the adapter generator
and evaluator for different feature subsets to determine the minimum required
feature set for acceptable performance.

Dependencies:
- T015 (adapter_generator.py): Generates adapters for specific feature subsets
- T021 (runner.py): Evaluates adapters and produces score CSVs

This module orchestrates the loop: for each subset -> generate adapter -> evaluate -> collect scores.
"""

import os
import sys
import time
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

# Import from sibling modules as per API surface
from utils.config import load_config
from utils.logging import get_logger
from utils.memory_monitor import run_step_with_memory_logging
from feature_extractor.ast_parser import get_feature_vector_size
from feature_extractor.graph_builder import get_graph_feature_vector_size

# Import hypernetwork components
from hypernetwork.adapter_generator import (
    generate_adapter, 
    MemoryLimitError, 
    CheckpointIncompatibilityError,
    AdapterGenerationError
)

# Import evaluation components
from evaluation.runner import run_evaluation, save_results

# Setup logging
logger = get_logger(__name__)

class FeatureSubset(Enum):
    """Enum defining available feature subsets for sensitivity analysis."""
    TOKENS_ONLY = "tokens_only"
    CYCLOMATIC_ONLY = "cyclomatic_only"
    INHERITANCE_ONLY = "inheritance_only"
    GRAPH_CENTRALITY = "graph_centrality"
    FULL_AST = "full_ast"
    COMBINED_SIMPLE = "combined_simple"

@dataclass
class FeatureSubsetConfig:
    """Configuration for a specific feature subset."""
    name: str
    features: List[str]
    description: str
    
def get_feature_subsets() -> List[FeatureSubsetConfig]:
    """
    Returns a list of feature subset configurations to test.
    
    These represent different combinations of AST features to evaluate
    their individual and combined impact on adapter performance.
    """
    return [
        FeatureSubsetConfig(
            name="tokens_only",
            features=["token_histogram"],
            description="Only token frequency histograms"
        ),
        FeatureSubsetConfig(
            name="cyclomatic_only",
            features=["cyclomatic_complexity"],
            description="Only cyclomatic complexity metrics"
        ),
        FeatureSubsetConfig(
            name="inheritance_only",
            features=["inheritance_depth"],
            description="Only inheritance depth metrics"
        ),
        FeatureSubsetConfig(
            name="graph_centrality",
            features=["graph_centrality"],
            description="Only import graph centrality metrics"
        ),
        FeatureSubsetConfig(
            name="full_ast",
            features=["token_histogram", "cyclomatic_complexity", "inheritance_depth", "graph_centrality"],
            description="Full set of AST features"
        ),
        FeatureSubsetConfig(
            name="combined_simple",
            features=["token_histogram", "cyclomatic_complexity"],
            description="Combined simple features"
        )
    ]

def get_subset_by_name(name: str) -> Optional[FeatureSubsetConfig]:
    """Retrieve a feature subset configuration by its name."""
    subsets = get_feature_subsets()
    for subset in subsets:
        if subset.name == name:
            return subset
    return None

def validate_subset_features(subset_config: FeatureSubsetConfig) -> bool:
    """
    Validate that the features in the subset are supported.
    
    Returns True if valid, False otherwise.
    """
    supported_features = {
        "token_histogram", "cyclomatic_complexity", 
        "inheritance_depth", "graph_centrality"
    }
    for feature in subset_config.features:
        if feature not in supported_features:
            logger.error(f"Unsupported feature in subset {subset_config.name}: {feature}")
            return False
    return True

def extract_features_for_subset(subset_config: FeatureSubsetConfig) -> Dict[str, Any]:
    """
    Extract features based on the subset configuration.
    
    This function prepares the feature extraction parameters for the adapter generator.
    In a real implementation, this would interface with the AST parser and graph builder
    to extract only the specified features.
    """
    # For now, we return the configuration which will be used by the adapter generator
    # The actual feature extraction happens inside generate_adapter based on this config
    return {
        "subset_name": subset_config.name,
        "features": subset_config.features,
        "description": subset_config.description
    }

def calculate_score_drop(base_score: float, current_score: float) -> float:
    """Calculate the percentage drop from the baseline score."""
    if base_score == 0:
        return 0.0
    return ((base_score - current_score) / base_score) * 100

def run_sensitivity_loop(
    feature_subsets: List[FeatureSubsetConfig],
    base_model_path: str,
    data_path: str,
    output_dir: Path,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Main sensitivity analysis loop.
    
    For each feature subset:
    1. Generate adapter using T015 (adapter_generator)
    2. Evaluate adapter using T021 (runner)
    3. Collect scores and metadata
    
    Returns a list of result dictionaries for each subset.
    """
    results = []
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting sensitivity loop with {len(feature_subsets)} subsets")
    logger.info(f"Base model: {base_model_path}")
    logger.info(f"Data path: {data_path}")
    logger.info(f"Output directory: {output_dir}")
    
    for idx, subset_config in enumerate(feature_subsets):
        subset_name = subset_config.name
        logger.info(f"\n--- Processing subset {idx+1}/{len(feature_subsets)}: {subset_name} ---")
        
        try:
            # Step 1: Prepare feature extraction for this subset
            feature_config = extract_features_for_subset(subset_config)
            logger.info(f"Feature configuration: {feature_config}")
            
            # Step 2: Generate adapter for this subset
            # This calls T015 functionality
            adapter_path = output_dir / f"adapter_{subset_name}.safetensors"
            generation_start = time.time()
            
            logger.info(f"Generating adapter for {subset_name}...")
            
            # We need to pass the feature configuration to the adapter generator
            # The generate_adapter function should handle subset-specific feature extraction
            generate_adapter(
                base_model_path=base_model_path,
                data_path=data_path,
                output_path=str(adapter_path),
                feature_subset=subset_config.name,
                features=subset_config.features,
                config=config
            )
            
            generation_time = time.time() - generation_start
            logger.info(f"Adapter generated in {generation_time:.2f}s: {adapter_path}")
            
            # Verify adapter file exists
            if not adapter_path.exists():
                logger.error(f"Adapter file not created: {adapter_path}")
                results.append({
                    "subset_name": subset_name,
                    "status": "failed",
                    "error": "Adapter file not created",
                    "generation_time": generation_time
                })
                continue
            
            # Step 3: Evaluate adapter using T021 (runner)
            logger.info(f"Evaluating adapter for {subset_name}...")
            
            # Run evaluation - this will produce scores
            evaluation_results = run_evaluation(
                adapter_path=str(adapter_path),
                data_path=data_path,
                output_dir=output_dir,
                subset_name=subset_name
            )
            
            # Extract the exact match score from evaluation results
            # The runner returns a dictionary with scores
            if "exact_match" in evaluation_results:
                score = evaluation_results["exact_match"]
            elif "scores" in evaluation_results and len(evaluation_results["scores"]) > 0:
                # Average exact match from multiple tasks
                scores = [s.get("exact_match", 0) for s in evaluation_results["scores"]]
                score = sum(scores) / len(scores) if scores else 0.0
            else:
                score = 0.0
                logger.warning(f"Could not extract exact_match score for {subset_name}")
            
            # Record results
            result = {
                "subset_name": subset_name,
                "features": subset_config.features,
                "description": subset_config.description,
                "exact_match": score,
                "generation_time": generation_time,
                "status": "success",
                "adapter_path": str(adapter_path),
                "evaluation_results": evaluation_results
            }
            results.append(result)
            
            logger.info(f"Subset {subset_name} completed. Score: {score:.4f}")
            
        except MemoryLimitError as e:
            logger.error(f"Memory limit exceeded for {subset_name}: {e}")
            results.append({
                "subset_name": subset_name,
                "status": "failed",
                "error": f"MemoryLimitError: {str(e)}",
                "features": subset_config.features
            })
        except CheckpointIncompatibilityError as e:
            logger.error(f"Checkpoint incompatibility for {subset_name}: {e}")
            results.append({
                "subset_name": subset_name,
                "status": "failed",
                "error": f"CheckpointIncompatibilityError: {str(e)}",
                "features": subset_config.features
            })
        except AdapterGenerationError as e:
            logger.error(f"Adapter generation error for {subset_name}: {e}")
            results.append({
                "subset_name": subset_name,
                "status": "failed",
                "error": f"AdapterGenerationError: {str(e)}",
                "features": subset_config.features
            })
        except Exception as e:
            logger.exception(f"Unexpected error processing {subset_name}: {e}")
            results.append({
                "subset_name": subset_name,
                "status": "failed",
                "error": f"UnexpectedError: {str(e)}",
                "features": subset_config.features
            })
    
    return results

def save_sensitivity_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save sensitivity analysis results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Sensitivity results saved to {output_path}")

def run_sensitivity_analysis(
    config_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Main entry point for sensitivity analysis.
    
    Loads configuration, runs the sensitivity loop, and saves results.
    """
    # Load configuration
    config = load_config(config_path) if config_path else load_config()
    
    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path(config.get("output_dir", "data/results"))
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get feature subsets
    feature_subsets = get_feature_subsets()
    logger.info(f"Will test {len(feature_subsets)} feature subsets")
    
    # Run the sensitivity loop
    results = run_sensitivity_loop(
        feature_subsets=feature_subsets,
        base_model_path=config.get("base_model_path", "TinyLlama-1.1B-Chat-hf"),
        data_path=config.get("repo_peft_bench_path", "data/raw"),
        output_dir=output_path,
        config=config
    )
    
    # Save results
    results_path = output_path / "sensitivity_results.json"
    save_sensitivity_results(results, results_path)
    
    return results

def main():
    """Command-line entry point for sensitivity analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on feature subsets")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--output", type=str, help="Output directory for results")
    parser.add_argument("--subsets", type=str, nargs="+", 
                      help="Specific subsets to test (default: all)")
    
    args = parser.parse_args()
    
    # If specific subsets requested, filter
    if args.subsets:
        all_subsets = get_feature_subsets()
        feature_subsets = [s for s in all_subsets if s.name in args.subsets]
        if not feature_subsets:
            logger.error(f"No valid subsets found: {args.subsets}")
            sys.exit(1)
        logger.info(f"Testing specific subsets: {args.subsets}")
    else:
        feature_subsets = get_feature_subsets()
    
    # Run analysis
    results = run_sensitivity_analysis(
        config_path=args.config,
        output_dir=args.output
    )
    
    # Print summary
    print("\n=== Sensitivity Analysis Summary ===")
    for r in results:
        if r["status"] == "success":
            print(f"{r['subset_name']}: {r['exact_match']:.4f} (time: {r['generation_time']:.2f}s)")
        else:
            print(f"{r['subset_name']}: FAILED - {r.get('error', 'Unknown error')}")
    
    print(f"\nResults saved to: data/results/sensitivity_results.json")

if __name__ == "__main__":
    main()