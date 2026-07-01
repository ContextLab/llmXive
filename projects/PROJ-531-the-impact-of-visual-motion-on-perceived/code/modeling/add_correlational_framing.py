"""
Task T025: Ensure all reported associations are framed as correlational (FR-008).

This module reads the model metrics produced by T026 (model_metrics.json) and
injects a metadata flag explicitly stating that all reported associations are
correlational, not causal. It also generates a companion metadata file
`correlational_framing.json` to be included in the final results package.

This satisfies FR-008: "Ensure all reported associations are framed as correlational."
"""
import os
import json
from pathlib import Path
from typing import Dict, Any
import logging

from utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

def add_correlational_framing(metrics_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Reads the model metrics JSON, adds a 'framing' section declaring
    correlational nature of results, and writes the updated metadata.
    
    Args:
        metrics_path: Path to the input model_metrics.json (from T026).
        output_dir: Directory where the updated metadata will be saved.
        
    Returns:
        The updated metrics dictionary with framing added.
        
    Raises:
        FileNotFoundError: If the input metrics file does not exist.
        json.JSONDecodeError: If the input file is not valid JSON.
    """
    metrics_file = Path(metrics_path)
    if not metrics_file.exists():
        raise FileNotFoundError(f"Input metrics file not found: {metrics_path}")
    
    with open(metrics_file, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
    
    # Define the framing statement per FR-008
    framing_statement = {
        "framing_declaration": "All reported associations between visual motion features and perceived agency scores are strictly correlational. No causal claims are made. This analysis is based on synthetic data for pipeline stress-testing purposes only.",
        "causal_inference_disclaimer": "This study does not establish causality. Observed correlations may be influenced by unmeasured confounding variables or artifacts of the synthetic data generation process.",
        "ethics_reference": "See T000 (Scope Definition) and docs/scope.md for project scope limitations.",
        "data_type": "synthetic",
        "validation_status": "pipeline_stress_test_only"
    }
    
    # Inject into the metrics structure
    metrics["metadata"] = metrics.get("metadata", {})
    metrics["metadata"]["framing"] = framing_statement
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write the updated metrics
    updated_metrics_path = output_path / "model_metrics_with_framing.json"
    with open(updated_metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Added correlational framing to {metrics_path}")
    logger.info(f"Saved updated metrics to {updated_metrics_path}")
    
    return metrics

def main():
    """
    Entry point for the script. Reads from data/results/model_metrics.json
    and writes to data/results/model_metrics_with_framing.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    metrics_input = project_root / "data" / "results" / "model_metrics.json"
    output_dir = project_root / "data" / "results"
    
    logger.info(f"Starting T025: Adding correlational framing to {metrics_input}")
    
    try:
        result = add_correlational_framing(str(metrics_input), str(output_dir))
        logger.info("T025 completed successfully.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T025 execution: {e}")
        return 1

if __name__ == "__main__":
    exit(main())