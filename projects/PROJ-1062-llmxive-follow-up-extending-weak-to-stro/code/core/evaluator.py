"""
Evaluator module for log-probability improvement calculation and statistical testing.

This module provides functionality to:
1. Calculate log-probability improvements between baseline and Direct-OPD models
2. Perform statistical significance testing (paired t-test, Wilcoxon signed-rank)
3. Apply multiple-comparison corrections (Bonferroni, Holm-Bonferroni)
4. Integrate human-verified labels for validation
"""
import json
import logging
import math
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.stats import ttest_rel, wilcoxon

# Import from existing project modules
from core.reward_computation import compute_implicit_reward
from data.human_labels_loader import load_human_labels

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Evaluator:
    """
    Evaluates model performance using log-probability improvements and statistical testing.
    
    Attributes:
        epsilon: Smoothing constant for numerical stability in log calculations
        human_labels_path: Path to human-verified labels file
    """
    
    def __init__(self, epsilon: float = 1e-8, human_labels_path: Optional[str] = None):
        """
        Initialize the evaluator.
        
        Args:
            epsilon: Small constant for numerical stability (default: 1e-8)
            human_labels_path: Path to human-verified labels JSONL file
        """
        self.epsilon = epsilon
        self.human_labels_path = human_labels_path
        self.human_labels = None
        
        if human_labels_path and os.path.exists(human_labels_path):
            try:
                self.human_labels = load_human_labels(human_labels_path)
                logger.info(f"Loaded human labels from {human_labels_path}")
            except Exception as e:
                logger.warning(f"Failed to load human labels: {e}")
                self.human_labels = None
        elif human_labels_path:
            logger.warning(f"Human labels file not found at {human_labels_path}")
    
    def calculate_log_probability(
        self, 
        logits: np.ndarray, 
        target_ids: np.ndarray
    ) -> float:
        """
        Calculate the log-probability of target sequence given logits.
        
        Args:
            logits: Model output logits of shape (seq_len, vocab_size)
            target_ids: Target token IDs of shape (seq_len,)
            
        Returns:
            Sum of log-probabilities for the target sequence
        """
        # Apply softmax with epsilon smoothing
        logits_shifted = logits - np.max(logits, axis=-1, keepdims=True)
        exp_logits = np.exp(logits_shifted)
        probs = exp_logits / (np.sum(exp_logits, axis=-1, keepdims=True) + self.epsilon)
        
        # Get probabilities for target tokens
        target_probs = probs[np.arange(len(target_ids)), target_ids]
        
        # Clip to avoid log(0)
        target_probs = np.clip(target_probs, self.epsilon, 1.0)
        
        # Return sum of log probabilities
        return float(np.sum(np.log(target_probs)))
    
    def calculate_improvement(
        self,
        baseline_log_probs: List[float],
        direct_opd_log_probs: List[float],
        human_labels: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Calculate log-probability improvement between baseline and Direct-OPD models.
        
        Args:
            baseline_log_probs: List of log-probabilities from baseline model
            direct_opd_log_probs: List of log-probabilities from Direct-OPD model
            human_labels: Optional dict mapping problem_id to correctness label
            
        Returns:
            Dictionary containing improvement metrics
        """
        if len(baseline_log_probs) != len(direct_opd_log_probs):
            raise ValueError(
                f"Baseline and Direct-OPD log-probability lists must have same length. "
                f"Got {len(baseline_log_probs)} vs {len(direct_opd_log_probs)}"
            )
        
        if len(baseline_log_probs) == 0:
            return {
                "mean_improvement": 0.0,
                "std_improvement": 0.0,
                "min_improvement": 0.0,
                "max_improvement": 0.0,
                "n_samples": 0,
                "filtered_by_human": False
            }
        
        improvements = [
            opd - baseline 
            for baseline, opd in zip(baseline_log_probs, direct_opd_log_probs)
        ]
        
        result = {
            "mean_improvement": float(np.mean(improvements)),
            "std_improvement": float(np.std(improvements)),
            "min_improvement": float(np.min(improvements)),
            "max_improvement": float(np.max(improvements)),
            "median_improvement": float(np.median(improvements)),
            "n_samples": len(improvements),
            "filtered_by_human": False
        }
        
        # Filter by human labels if available
        if human_labels is not None and len(human_labels) > 0:
            filtered_improvements = []
            for i, improvement in enumerate(improvements):
                if i < len(human_labels):
                    # Assuming human_labels is ordered or mapped by index
                    if human_labels.get(f"problem_{i}", True):  # Default to include if not found
                        filtered_improvements.append(improvement)
                else:
                    filtered_improvements.append(improvement)
            
            if len(filtered_improvements) > 0:
                result["mean_improvement_filtered"] = float(np.mean(filtered_improvements))
                result["std_improvement_filtered"] = float(np.std(filtered_improvements))
                result["filtered_by_human"] = True
                result["n_filtered_samples"] = len(filtered_improvements)
        
        return result
    
    def perform_statistical_tests(
        self,
        baseline_log_probs: List[float],
        direct_opd_log_probs: List[float],
        correction_method: str = "bonferroni",
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Perform statistical significance tests on log-probability improvements.
        
        Args:
            baseline_log_probs: List of log-probabilities from baseline model
            direct_opd_log_probs: List of log-probabilities from Direct-OPD model
            correction_method: Method for multiple comparison correction 
                             ("bonferroni", "holm", "none")
            alpha: Significance level (default: 0.05)
            
        Returns:
            Dictionary containing test results and p-values
        """
        if len(baseline_log_probs) < 2:
            return {
                "paired_ttest": {
                    "statistic": None,
                    "p_value": None,
                    "significant": False,
                    "error": "Insufficient samples for t-test (need >= 2)"
                },
                "wilcoxon": {
                    "statistic": None,
                    "p_value": None,
                    "significant": False,
                    "error": "Insufficient samples for Wilcoxon test (need >= 2)"
                },
                "correction_applied": correction_method,
                "alpha": alpha
            }
        
        improvements = np.array(direct_opd_log_probs) - np.array(baseline_log_probs)
        
        # Paired t-test
        try:
            t_stat, t_pvalue = ttest_rel(direct_opd_log_probs, baseline_log_probs)
            t_significant = t_pvalue < alpha
        except Exception as e:
            logger.warning(f"T-test failed: {e}")
            t_stat, t_pvalue, t_significant = None, None, False
        
        # Wilcoxon signed-rank test
        try:
            w_stat, w_pvalue = wilcoxon(direct_opd_log_probs, baseline_log_probs)
            w_significant = w_pvalue < alpha
        except Exception as e:
            logger.warning(f"Wilcoxon test failed: {e}")
            w_stat, w_pvalue, w_significant = None, None, False
        
        # Apply multiple comparison correction
        p_values = [t_pvalue, w_pvalue] if t_pvalue is not None and w_pvalue is not None else []
        corrected_pvalues = p_values
        correction_applied = "none"
        
        if len(p_values) > 0:
            if correction_method == "bonferroni":
                corrected_pvalues = [p * len(p_values) for p in p_values]
                corrected_pvalues = [min(p, 1.0) for p in corrected_pvalues]
                correction_applied = "bonferroni"
            elif correction_method == "holm":
                # Holm-Bonferroni method
                sorted_indices = np.argsort(p_values)
                sorted_pvalues = [p_values[i] for i in sorted_indices]
                corrected = []
                for i, p in enumerate(sorted_pvalues):
                    corrected_p = p * (len(p_values) - i)
                    corrected.append(min(corrected_p, 1.0))
                
                # Restore original order
                corrected_pvalues = [0.0] * len(p_values)
                for i, idx in enumerate(sorted_indices):
                    corrected_pvalues[idx] = corrected[i]
                correction_applied = "holm"
        
        # Determine significance with correction
        t_corrected_pvalue = corrected_pvalues[0] if len(corrected_pvalues) > 0 else t_pvalue
        w_corrected_pvalue = corrected_pvalues[1] if len(corrected_pvalues) > 1 else w_pvalue
        
        t_corrected_significant = t_corrected_pvalue is not None and t_corrected_pvalue < alpha
        w_corrected_significant = w_corrected_pvalue is not None and w_corrected_pvalue < alpha
        
        return {
            "paired_ttest": {
                "statistic": float(t_stat) if t_stat is not None else None,
                "p_value": float(t_pvalue) if t_pvalue is not None else None,
                "corrected_p_value": float(t_corrected_pvalue) if t_corrected_pvalue is not None else None,
                "significant": bool(t_significant),
                "corrected_significant": bool(t_corrected_significant)
            },
            "wilcoxon": {
                "statistic": float(w_stat) if w_stat is not None else None,
                "p_value": float(w_pvalue) if w_pvalue is not None else None,
                "corrected_p_value": float(w_corrected_pvalue) if w_corrected_pvalue is not None else None,
                "significant": bool(w_significant),
                "corrected_significant": bool(w_corrected_significant)
            },
            "correction_method": correction_applied,
            "alpha": alpha,
            "n_samples": len(improvements)
        }
    
    def evaluate_model_comparison(
        self,
        baseline_results_path: str,
        direct_opd_results_path: str,
        output_path: str,
        correction_method: str = "bonferroni"
    ) -> Dict[str, Any]:
        """
        Evaluate and compare baseline and Direct-OPD model results.
        
        Args:
            baseline_results_path: Path to baseline model results JSON file
            direct_opd_results_path: Path to Direct-OPD model results JSON file
            output_path: Path to save evaluation results
            correction_method: Method for multiple comparison correction
            
        Returns:
            Dictionary containing complete evaluation results
        """
        # Load results
        try:
            with open(baseline_results_path, 'r') as f:
                baseline_results = json.load(f)
        except Exception as e:
            raise FileNotFoundError(f"Failed to load baseline results: {e}")
        
        try:
            with open(direct_opd_results_path, 'r') as f:
                direct_opd_results = json.load(f)
        except Exception as e:
            raise FileNotFoundError(f"Failed to load Direct-OPD results: {e}")
        
        # Extract log-probabilities
        baseline_log_probs = baseline_results.get("log_probabilities", [])
        direct_opd_log_probs = direct_opd_results.get("log_probabilities", [])
        
        if not baseline_log_probs or not direct_opd_log_probs:
            raise ValueError("No log-probabilities found in result files")
        
        # Calculate improvements
        improvement_metrics = self.calculate_improvement(
            baseline_log_probs,
            direct_opd_log_probs,
            human_labels=self.human_labels
        )
        
        # Perform statistical tests
        statistical_results = self.perform_statistical_tests(
            baseline_log_probs,
            direct_opd_log_probs,
            correction_method=correction_method
        )
        
        # Compile final results
        evaluation_results = {
            "baseline_file": baseline_results_path,
            "direct_opd_file": direct_opd_results_path,
            "improvement_metrics": improvement_metrics,
            "statistical_tests": statistical_results,
            "summary": {
                "mean_improvement": improvement_metrics["mean_improvement"],
                "statistically_significant": (
                    statistical_results["paired_ttest"]["corrected_significant"] or
                    statistical_results["wilcoxon"]["corrected_significant"]
                ),
                "correction_method": correction_method
            }
        }
        
        # Save results
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(evaluation_results, f, indent=2)
        
        logger.info(f"Evaluation results saved to {output_path}")
        return evaluation_results


def main():
    """
    Main function to run evaluator on example data.
    This demonstrates the evaluator's functionality with sample data.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate model performance")
    parser.add_argument("--baseline", type=str, required=True, help="Path to baseline results")
    parser.add_argument("--direct-opd", type=str, required=True, help="Path to Direct-OPD results")
    parser.add_argument("--output", type=str, required=True, help="Path to output file")
    parser.add_argument("--human-labels", type=str, default=None, help="Path to human labels")
    parser.add_argument("--correction", type=str, default="bonferroni", 
                      choices=["bonferroni", "holm", "none"],
                      help="Multiple comparison correction method")
    
    args = parser.parse_args()
    
    evaluator = Evaluator(human_labels_path=args.human_labels)
    results = evaluator.evaluate_model_comparison(
        args.baseline,
        args.direct_opd,
        args.output,
        args.correction
    )
    
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
