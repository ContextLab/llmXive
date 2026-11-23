"""
Modular runner for T037: Code cleanup and refactoring of `code/` into modular runners.
This script refactors the evaluation pipeline (T034) into a clean, modular runner.
It orchestrates: Baseline Evaluation -> Dynamic Evaluation -> Metrics -> Timing ->
Statistical Tests -> Final Report.
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from existing API surface
from config import Config
from evaluation.metrics import compute_metrics_batch, save_metrics_to_json, load_metrics_from_json
from evaluation.timing import load_prompts_for_timing, run_static_inference, run_dynamic_inference, compute_statistics, save_timing_results
from analysis.statistical_test import run_statistical_tests, save_results as save_stats_results
from analysis.router import EntropyRouter
from quantization.w2a4_engine import W2A4Engine
from quantization.static_baseline import StaticRotationBaseline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EvaluationRunner:
    """
    Modular runner for the full evaluation pipeline.
    Encapsulates logic for T030, T031, T032, T034 refactoring.
    """
    def __init__(self, config: Config):
        self.config = config
        self.metrics_engine = None # Placeholder for metrics logic
        self.timing_engine = None
        self.router = None
        self.w2a4_engine = None
        self.baseline = None

    def load_prompts(self, split: str = "test") -> List[Dict[str, Any]]:
        """Load prompts for evaluation."""
        if split == "test":
            path = Path(self.config.paths.processed_data) / "prompts_test.csv"
        elif split == "train":
            path = Path(self.config.paths.processed_data) / "prompts_train.csv"
        else:
            raise ValueError(f"Unknown split: {split}")
        
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")
        
        prompts = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prompts.append({"id": row.get('id', ''), "text": row.get('text', '')})
        return prompts

    def run_baseline_evaluation(self, prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run static baseline inference and compute metrics."""
        logger.info("Running Baseline Evaluation (Static Rotation)...")
        if not self.baseline:
            self.baseline = StaticRotationBaseline(self.config)
        
        # Generate images and compute metrics
        # This calls the baseline engine which uses a fixed rotation matrix
        metrics = self.baseline.run_inference_and_evaluate(prompts)
        return metrics

    def run_dynamic_evaluation(self, prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run dynamic router inference and compute metrics."""
        logger.info("Running Dynamic Evaluation (Router-based)...")
        if not self.router:
            self.router = EntropyRouter(self.config)
        if not self.w2a4_engine:
            self.w2a4_engine = W2A4Engine(self.config)
        
        # Generate images with dynamic rotation selection
        metrics = self.w2a4_engine.run_inference_with_router(prompts, self.router)
        return metrics

    def run_timing_analysis(self, prompts: List[Dict[str, Any]]) -> Dict[str, float]:
        """Measure wall-clock inference time for both methods."""
        logger.info("Running Timing Analysis...")
        # Static timing
        static_time = run_static_inference(prompts, self.config)
        # Dynamic timing
        dynamic_time = run_dynamic_inference(prompts, self.config, self.router)
        
        results = {
            "static_inference_time": static_time,
            "dynamic_inference_time": dynamic_time,
            "overhead_percentage": (dynamic_time - static_time) / static_time * 100
        }
        return results

    def run_statistical_comparison(self, baseline_metrics: Dict[str, float], 
                                   dynamic_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Perform paired t-tests and Bonferroni correction."""
        logger.info("Running Statistical Comparison...")
        results = run_statistical_tests(baseline_metrics, dynamic_metrics, self.config)
        return results

    def generate_final_report(self, baseline_metrics: Dict[str, float],
                              dynamic_metrics: Dict[str, float],
                              timing_results: Dict[str, float],
                              stats_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compile all results into a final report."""
        logger.info("Generating Final Evaluation Report...")
        report = {
            "timestamp": time.time(),
            "baseline_metrics": baseline_metrics,
            "dynamic_metrics": dynamic_metrics,
            "timing_results": timing_results,
            "statistical_tests": stats_results,
            "summary": {
                "baseline_avg_mse": baseline_metrics.get("mse", {}).get("mean", 0),
                "dynamic_avg_mse": dynamic_metrics.get("mse", {}).get("mean", 0),
                "improvement_mse": (baseline_metrics.get("mse", {}).get("mean", 0) - dynamic_metrics.get("mse", {}).get("mean", 0)),
                "overhead_time": timing_results.get("overhead_percentage", 0)
            }
        }
        return report

    def run(self, split: str = "test"):
        """Run the full evaluation pipeline."""
        logger.info("Starting Evaluation Runner...")
        
        # 1. Load Prompts
        prompts = self.load_prompts(split)
        logger.info(f"Loaded {len(prompts)} prompts for evaluation.")
        
        # 2. Baseline Evaluation
        baseline_metrics = self.run_baseline_evaluation(prompts)
        
        # 3. Dynamic Evaluation
        dynamic_metrics = self.run_dynamic_evaluation(prompts)
        
        # 4. Timing Analysis
        timing_results = self.run_timing_analysis(prompts)
        
        # 5. Statistical Comparison
        stats_results = self.run_statistical_comparison(baseline_metrics, dynamic_metrics)
        
        # 6. Final Report
        final_report = self.generate_final_report(
            baseline_metrics, dynamic_metrics, timing_results, stats_results
        )
        
        # Save Report
        output_path = Path(self.config.paths.processed_data) / "final_evaluation_report.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"Final report saved to {output_path}")
        return final_report

def main():
    """Entry point for the modular evaluation runner."""
    config = Config()
    runner = EvaluationRunner(config)
    
    try:
        report = runner.run()
        logger.info("Evaluation Runner completed successfully.")
        logger.info(f"Summary: MSE Improvement = {report['summary']['improvement_mse']:.4f}, "
                    f"Time Overhead = {report['summary']['overhead_time']:.2f}%")
    except Exception as e:
        logger.error(f"Evaluation pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
