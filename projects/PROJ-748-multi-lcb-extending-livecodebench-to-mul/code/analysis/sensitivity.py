"""
Temperature-sensitivity analysis module.

Sweeps temperatures (0.2, 0.6, 1.0) and reports variance of correlation coefficients.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    logger = logging.getLogger("sensitivity_analysis")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def load_execution_log(execution_log_path: Path) -> Dict[str, Any]:
    if not execution_log_path.exists():
        raise FileNotFoundError(f"Execution log not found at {execution_log_path}")
    with open(execution_log_path, 'r') as f:
        return json.load(f)

def extract_pass_k_by_temperature(
    execution_log: Dict[str, Any],
    pass_k: int = 1
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Extract Pass@k scores grouped by model, language, and temperature.
    
    Returns:
        Dict[Model][Language][Temperature] -> score
    """
    data = {}
    tasks = execution_log.get("tasks", [])
    
    for task in tasks:
        model = task.get("model")
        language = task.get("language")
        temperature = task.get("temperature", 0.2)
        pass_k_value = task.get(f"pass_{pass_k}", 0.0)
        
        if model not in data:
            data[model] = {}
        if language not in data[model]:
            data[model][language] = {}
        
        # Average scores if multiple runs exist for same model/lang/temp
        if temperature not in data[model][language]:
            data[model][language][temperature] = []
        data[model][language][temperature].append(pass_k_value)
    
    # Average the runs
    for model in data:
        for lang in data[model]:
            for temp in data[model][lang]:
                scores = data[model][lang][temp]
                data[model][lang][temp] = np.mean(scores)
                
    return data

def compute_correlation_across_temperatures(
    pass_k_data: Dict[str, Dict[str, Dict[str, float]]],
    reference_language: str = "python"
) -> Dict[str, List[float]]:
    """
    Compute correlation between reference language and others for each temperature.
    
    Returns:
        Dict[Temperature] -> List of correlation coefficients
    """
    temperatures = set()
    for model in pass_k_data:
        for lang in pass_k_data[model]:
            temperatures.update(pass_k_data[model][lang].keys())
    
    results = {temp: [] for temp in temperatures}
    
    # Flatten data for correlation calculation
    for temp in temperatures:
        ref_scores = []
        other_scores = []
        
        for model in pass_k_data:
            if reference_language in pass_k_data[model]:
                ref_score = pass_k_data[model][reference_language].get(temp, np.nan)
                if not np.isnan(ref_score):
                    ref_scores.append(ref_score)
                    for lang in pass_k_data[model]:
                        if lang != reference_language:
                            other_score = pass_k_data[model][lang].get(temp, np.nan)
                            if not np.isnan(other_score):
                                other_scores.append(other_score)
        
        if len(ref_scores) > 1 and len(other_scores) > 1:
            # Compute correlation
            corr, _ = np.corrcoef(ref_scores, other_scores)
            results[temp].append(corr)
    
    # Average correlations per temperature
    final_results = {}
    for temp, corrs in results.items():
        if corrs:
            final_results[temp] = float(np.mean(corrs))
        else:
            final_results[temp] = float(np.nan)
            
    return final_results

def calculate_variance(results: Dict[str, float]) -> Dict[str, Any]:
    """Calculate variance and stability metrics."""
    values = [v for v in results.values() if not np.isnan(v)]
    if len(values) < 2:
        return {
            "variance": float('nan'),
            "std_dev": float('nan'),
            "range": float('nan'),
            "stability_score": float('nan')
        }
    
    variance = np.var(values)
    std_dev = np.std(values)
    range_val = max(values) - min(values)
    # Stability score: 1 / (1 + variance)
    stability_score = 1.0 / (1.0 + variance)
    
    return {
        "variance": float(variance),
        "std_dev": float(std_dev),
        "range": float(range_val),
        "stability_score": float(stability_score),
        "correlations_by_temperature": results
    }

def run_sensitivity_pipeline(
    execution_log: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full sensitivity analysis pipeline.
    
    Args:
        execution_log: The execution log data.
        output_dir: Directory to save intermediate results.
        
    Returns:
        Dictionary containing sensitivity analysis results.
    """
    logger = setup_logging()
    logger.info("Starting sensitivity analysis pipeline...")
    
    # Extract Pass@1 scores by temperature
    pass_k_data = extract_pass_k_by_temperature(execution_log, pass_k=1)
    
    # Compute correlations across temperatures
    correlations = compute_correlation_across_temperatures(pass_k_data)
    
    # Calculate variance metrics
    variance_metrics = calculate_variance(correlations)
    
    results = {
        "metadata": {
            "analysis_type": "temperature_sensitivity",
            "reference_language": "python",
            "pass_k": 1
        },
        "correlations_by_temperature": correlations,
        "variance_metrics": variance_metrics,
        "conclusion": "Sensitivity analysis completed."
    }
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "sensitivity_analysis.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Sensitivity results saved to {output_path}")
    
    return results

def main():
    """Entry point for sensitivity analysis."""
    from config import get_results_path, get_data_path
    import json
    
    execution_log_path = get_results_path() / "artifacts" / "execution_log.json"
    if not execution_log_path.exists():
        print(f"Error: Execution log not found at {execution_log_path}")
        sys.exit(1)
        
    with open(execution_log_path, 'r') as f:
        execution_log = json.load(f)
        
    results = run_sensitivity_pipeline(execution_log)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
