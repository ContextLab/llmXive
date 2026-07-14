import json
import os
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from config import get_config

def compute_bayes_factor(evidence_model_1: float, evidence_model_2: float) -> float:
    """
    Compute the Bayes factor K = Z1 / Z2.
    
    Args:
        evidence_model_1: Log-evidence (ln Z) for model 1.
        evidence_model_2: Log-evidence (ln Z) for model 2.
        
    Returns:
        Bayes factor K (linear scale).
    """
    # Handle log-evidence to linear conversion carefully to avoid overflow
    # K = exp(ln Z1 - ln Z2)
    log_k = evidence_model_1 - evidence_model_2
    
    # Clip to avoid overflow in exp if log_k is too large
    if log_k > 700:
        return float('inf')
    elif log_k < -700:
        return 0.0
    else:
        return np.exp(log_k)

def interpret_bayes_factor(K: float) -> str:
    """
    Interpret the Bayes factor K according to standard thresholds.
    
    Thresholds (Jeffreys scale):
    K > 10: Strong evidence for model 1
    K > 3.2: Moderate evidence
    1 < K < 3.2: Weak evidence
    K = 1: Equal evidence
    K < 1: Evidence for model 2 (inverse)
    
    Args:
        K: Bayes factor (Z1/Z2).
        
    Returns:
        Interpretation string.
    """
    if K > 10:
        return "Strong evidence for model 1 (K > 10)"
    elif K > 3.2:
        return "Moderate evidence for model 1 (3.2 < K <= 10)"
    elif K > 1:
        return "Weak evidence for model 1 (1 < K <= 3.2)"
    elif K >= 1/3.2:
        return "Inconclusive (1/3.2 <= K <= 1)"
    elif K >= 1/10:
        return "Weak evidence for model 2 (1/10 <= K < 1/3.2)"
    else:
        return "Strong evidence for model 2 (K < 1/10)"

def compare_models(
    model_results: Dict[str, Dict[str, Any]],
    reference_model: str = "Null"
) -> Dict[str, Any]:
    """
    Compare all models against a reference model (default: Null).
    
    Args:
        model_results: Dictionary mapping model names to their results,
                       expected to contain 'log_evidence' key.
        reference_model: Name of the model to use as the denominator.
        
    Returns:
        Dictionary containing Bayes factors and interpretations.
    """
    if reference_model not in model_results:
        raise ValueError(f"Reference model '{reference_model}' not found in results.")
        
    ref_evidence = model_results[reference_model].get('log_evidence')
    if ref_evidence is None:
        raise ValueError(f"Reference model '{reference_model}' missing 'log_evidence'.")
        
    comparisons = {}
    
    for model_name, results in model_results.items():
        if model_name == reference_model:
            continue
            
        model_evidence = results.get('log_evidence')
        if model_evidence is None:
            continue
            
        K = compute_bayes_factor(model_evidence, ref_evidence)
        interpretation = interpret_bayes_factor(K)
        
        comparisons[model_name] = {
            "bayes_factor": round(K, 2),
            "log_evidence_diff": round(model_evidence - ref_evidence, 4),
            "interpretation": interpretation,
            "exceeds_threshold": K > 10
        }
        
    return comparisons

def save_model_comparison_results(
    comparisons: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save model comparison results to a JSON file.
    
    Args:
        comparisons: Dictionary of comparison results.
        output_path: Path to save the JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(comparisons, f, indent=2)

def main() -> None:
    """
    Main entry point for model comparison.
    
    Loads results from inference runs, computes Bayes factors,
    and saves the comparison report.
    """
    config = get_config()
    
    # Expected paths based on project structure
    # These should be populated by previous inference runs
    results_dir = Path("data/derived")
    output_path = results_dir / "model_comparison_results.json"
    
    # Load individual model results
    model_files = {
        "Inflation": results_dir / "inflation_results.json",
        "PhaseTransition": results_dir / "phase_transition_results.json",
        "Null": results_dir / "null_results.json"
    }
    
    model_results = {}
    for model_name, file_path in model_files.items():
        if file_path.exists():
            with open(file_path, 'r') as f:
                model_results[model_name] = json.load(f)
        else:
            print(f"Warning: {file_path} not found. Skipping {model_name}.")
    
    if not model_results:
        raise FileNotFoundError("No model result files found in data/derived/.")
        
    # Ensure we have a reference model (Null is preferred)
    if "Null" not in model_results and len(model_results) > 0:
        # Use the first available model as reference if Null is missing
        reference = list(model_results.keys())[0]
        print(f"Warning: Null model not found. Using '{reference}' as reference.")
    else:
        reference = "Null"
        
    # Perform comparisons
    comparisons = compare_models(model_results, reference_model=reference)
    
    # Add reference model info
    comparisons["_metadata"] = {
        "reference_model": reference,
        "threshold": 10,
        "precision": 2
    }
    
    # Save results
    save_model_comparison_results(comparisons, str(output_path))
    print(f"Model comparison results saved to {output_path}")
    
    # Print summary
    print("\nBayes Factor Summary:")
    print("-" * 50)
    for model_name, data in comparisons.items():
        if model_name == "_metadata":
            continue
        print(f"{model_name} vs {reference}:")
        print(f"  K = {data['bayes_factor']:.2f}")
        print(f"  Decision: {'> 10 (Strong)' if data['exceeds_threshold'] else '< 10 (Inconclusive/Weak)'}")
        print(f"  Interpretation: {data['interpretation']}")
        print()

if __name__ == "__main__":
    main()