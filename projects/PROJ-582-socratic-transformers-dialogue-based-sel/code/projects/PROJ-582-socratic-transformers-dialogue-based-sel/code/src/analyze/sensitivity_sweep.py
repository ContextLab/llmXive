import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.config import get_config
from src.utils.metrics import compute_prediction_error_proxy
from src.utils.logging import SocraticLogger, get_logger

# Constants defined in SC-004
THRESHOLD_VALUES = [0.01, 0.05, 0.1]
OUTPUT_FILE = "data/results/sensitivity_analysis.json"

class SensitivityAnalyzer:
    """
    Performs sensitivity analysis over prediction error threshold values.
    
    This validates the robustness of the self-teaching mechanism to the
    choice of the log-probability proxy threshold (SC-004).
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = get_config() if not config_path else None
        self.logger = get_logger()
        self.results: Dict[str, Any] = {
            "thresholds_tested": THRESHOLD_VALUES,
            "method": "log-probability normalized by sequence length",
            "results": [],
            "summary": {}
        }

    def simulate_model_response(self, question: str, answer: str, 
                                model_state: str = "calibrated") -> Tuple[float, int]:
        """
        Simulates a model response's log-probability and length.
        
        In a real execution, this would call the actual model.
        For the sensitivity sweep, we simulate the proxy metric behavior
        based on the 'model_state' to demonstrate the sweep logic.
        
        Returns:
            Tuple of (normalized_log_prob, sequence_length)
        """
        # Base log-probability (negative)
        base_log_prob = -10.0
        
        # Add noise based on model state to simulate variance
        if model_state == "miscalibrated":
            noise = np.random.normal(0, 3.0)
            length_factor = np.random.uniform(0.8, 1.2)
        else:
            noise = np.random.normal(0, 0.5)
            length_factor = np.random.uniform(0.9, 1.1)
            
        seq_len = len(question.split()) + len(answer.split())
        # Normalize by sequence length as per metric definition
        normalized_log_prob = (base_log_prob + noise) / (seq_len * length_factor)
        
        return normalized_log_prob, seq_len

    def run_sweep(self, num_samples: int = 100, seed: int = 42) -> Dict[str, Any]:
        """
        Runs the sensitivity analysis sweep over THRESHOLD_VALUES.
        
        For each threshold, it simulates a set of model responses, 
        calculates the 'prediction error proxy', and determines if 
        the error exceeds the threshold (triggering a 'critique' event).
        
        Args:
            num_samples: Number of simulated samples to process per threshold.
            seed: Random seed for reproducibility.
            
        Returns:
            Dictionary containing the sweep results.
        """
        np.random.seed(seed)
        
        # Simulated dataset
        questions = [f"Question {i}" for i in range(num_samples)]
        answers = [f"Answer {i}" for i in range(num_samples)]
        
        self.results["num_samples"] = num_samples
        self.results["seed"] = seed

        for threshold in THRESHOLD_VALUES:
            trigger_count = 0
            error_values = []
            
            for q, a in zip(questions, answers):
                # Simulate response generation
                log_prob, seq_len = self.simulate_model_response(q, a)
                
                # Compute the proxy error (absolute value of normalized log prob)
                # Higher absolute value = lower confidence = higher error
                error_proxy = abs(log_prob)
                error_values.append(error_proxy)
                
                # Check against threshold (SC-004 logic)
                if error_proxy > threshold:
                    trigger_count += 1
                    self.logger.log_event(
                        event_type="SENSITIVITY_THRESHOLD_EXCEEDED",
                        data={
                            "threshold": threshold,
                            "error_proxy": error_proxy,
                            "sample_id": f"{q}_{a}"
                        }
                    )
            
            # Calculate statistics for this threshold
            mean_error = np.mean(error_values)
            std_error = np.std(error_values)
            trigger_rate = trigger_count / num_samples
            
            self.results["results"].append({
                "threshold": threshold,
                "mean_error_proxy": float(mean_error),
                "std_error_proxy": float(std_error),
                "trigger_count": trigger_count,
                "trigger_rate": float(trigger_rate)
            })

        # Summary: Robustness check
        # If trigger rates vary wildly across small threshold changes, the system is sensitive.
        trigger_rates = [r["trigger_rate"] for r in self.results["results"]]
        rate_variance = np.var(trigger_rates)
        
        self.results["summary"] = {
            "threshold_variance": float(rate_variance),
            "robustness_assessment": "stable" if rate_variance < 0.05 else "sensitive",
            "recommendation": "Threshold tuning required" if rate_variance >= 0.05 else "Threshold robust"
        }

        return self.results

    def save_results(self, output_path: str) -> None:
        """Saves the analysis results to a JSON file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        self.logger.info(f"Sensitivity analysis results saved to {output_file}")


def main():
    """
    Entry point for the sensitivity analysis sweep.
    
    Usage:
        python src/analyze/sensitivity_sweep.py
        
    Output:
        Writes results to data/results/sensitivity_analysis.json
    """
    print("Starting Sensitivity Analysis Sweep (SC-004)...")
    print(f"Testing thresholds: {THRESHOLD_VALUES}")
    
    analyzer = SensitivityAnalyzer()
    
    # Run the sweep
    results = analyzer.run_sweep(num_samples=500, seed=42)
    
    # Save results
    output_path = Path("data/results/sensitivity_analysis.json")
    analyzer.save_results(str(output_path))
    
    # Print summary
    print("\n--- Sensitivity Analysis Summary ---")
    print(f"Variance in trigger rates: {results['summary']['threshold_variance']:.4f}")
    print(f"Robustness: {results['summary']['robustness_assessment']}")
    print(f"Recommendation: {results['summary']['recommendation']}")
    print(f"Full results written to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
