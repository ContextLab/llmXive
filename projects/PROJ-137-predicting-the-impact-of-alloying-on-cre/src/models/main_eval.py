"""
Orchestration script for User Story 2: Comparative Model Training and Evaluation.

This script:
1. Loads the preprocessed dataset from data/outputs/processed_data.csv.
2. Invokes training (src/models/train.py) to build Thermodynamic and Composition-Only GBR models.
3. Invokes evaluation (src/models/evaluate.py) to compute metrics, CI, and significance tests.
4. Prints a final comparison table to stdout.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.models.train import train_models
from src.models.evaluate import evaluate_models

logger = get_logger(__name__)

def main():
    logger.info("Starting Model Evaluation Orchestration (T025)")
    
    # Configuration paths relative to project root
    data_path = project_root / "data" / "outputs" / "processed_data.csv"
    output_dir = project_root / "data" / "outputs"
    
    if not data_path.exists():
        logger.error(f"Processed data not found at {data_path}. Run the data pipeline first.")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Train Models
    logger.info("Training Gradient Boosting models...")
    try:
        results = train_models(data_path=str(data_path), output_dir=str(output_dir))
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)
    
    # 2. Evaluate Models
    logger.info("Evaluating models (Nested CV, Permutation Test, Bootstrap CI)...")
    try:
        eval_results = evaluate_models(
            thermodynamic_model_path=results["thermodynamic_model_path"],
            composition_model_path=results["composition_model_path"],
            data_path=str(data_path),
            output_dir=str(output_dir)
        )
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)
    
    # 3. Print Final Comparison Table
    logger.info("Final Comparison Results:")
    print("\n" + "="*80)
    print("MODEL COMPARISON SUMMARY")
    print("="*80)
    
    r2_thermo = eval_results["r2_thermodynamic"]
    r2_comp = eval_results["r2_composition"]
    r2_delta = r2_thermo - r2_comp
    
    print(f"{'Metric':<30} | {'Thermodynamic':<15} | {'Composition':<15}")
    print("-" * 80)
    print(f"{'R² (Mean)':<30} | {r2_thermo:<15.4f} | {r2_comp:<15.4f}")
    print(f"{'RMSE (Mean)':<30} | {eval_results['rmse_thermodynamic']:<15.4f} | {eval_results['rmse_composition']:<15.4f}")
    print("-" * 80)
    print(f"{'R² Delta (Thermo - Comp)':<30} | {r2_delta:<30.4f}")
    
    # Statistical Significance
    test_type = eval_results.get("test_type", "Unknown")
    p_value = eval_results.get("p_value", None)
    ci_bounds = eval_results.get("ci_bounds", None)
    
    print(f"\nStatistical Significance Test ({test_type}):")
    if p_value is not None:
        sig_str = "SIGNIFICANT (p < 0.05)" if p_value < 0.05 else "NOT SIGNIFICANT (p >= 0.05)"
        print(f"  P-value: {p_value:.6f} -> {sig_str}")
    
    if ci_bounds:
        print(f"  95% Confidence Interval: [{ci_bounds[0]:.4f}, {ci_bounds[1]:.4f}]")
    
    print("="*80 + "\n")
    
    logger.info("Evaluation orchestration completed successfully.")
    return eval_results

if __name__ == "__main__":
    main()