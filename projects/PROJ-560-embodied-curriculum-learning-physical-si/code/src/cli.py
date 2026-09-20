import argparse
import sys
import json
import os
import logging
from typing import List, Optional
from .logging_config import setup_logging
from .data_loader import load_public_dataset, calculate_gain_scores, write_processed_data
from .synthetic_gen import SyntheticDataGenerator, generate_mapping_log
from .stats_engine import run_t_test, calculate_effect_size, calculate_confidence_interval, aggregate_results, frame_inference, calculate_power, check_collinearity
from .sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_results_for_report
from .models import AnalysisResult, SensitivitySweep
from .utils import set_seed


logger = logging.getLogger(__name__)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Args:
        args: Optional list of arguments.
        
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(description="Embodied Curriculum Learning Analysis")
    parser.add_argument(
        '--mode', 
        type=str, 
        choices=['secondary_analysis', 'synthetic'], 
        default='synthetic',
        help='Analysis mode'
    )
    parser.add_argument(
        '--input', 
        type=str, 
        default=None,
        help='Input data file path'
    )
    parser.add_argument(
        '--sweep_thresholds', 
        type=float, 
        nargs='+', 
        default=[0.01, 0.05, 0.1],
        help='Significance thresholds for sensitivity sweep'
    )
    parser.add_argument(
        '--seed', 
        type=int, 
        default=42,
        help='Random seed'
    )
    parser.add_argument(
        '--concept_definition', 
        type=str, 
        default=None,
        help='JSON string of concept definition for synthetic data'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/processed/results.json',
        help='Output file path'
    )
    
    return parser.parse_args(args)


def run_secondary_analysis(input_path: str, output_path: str) -> None:
    """
    Run secondary analysis on public data.
    
    Args:
        input_path: Path to input data.
        output_path: Path to output results.
    """
    logger.info("Running secondary analysis...")
    records = load_public_dataset(input_path)
    records = calculate_gain_scores(records)
    
    if len(records) < 2:
        logger.error("Insufficient data for analysis.")
        return
        
    # Group by instruction type
    groups: Dict[str, List[float]] = {}
    for r in records:
        if r.instruction_type not in groups:
            groups[r.instruction_type] = []
        gain = r.post_test_score - r.pre_test_score
        groups[r.instruction_type].append(gain)
        
    if len(groups) < 2:
        logger.error("Need at least two instruction types for comparison.")
        return
        
    g1_keys = list(groups.keys())
    g1 = groups[g1_keys[0]]
    g2 = groups[g1_keys[1]]
    
    t_stat, p_val = run_t_test(g1, g2)
    effect = calculate_effect_size(g1, g2)
    ci = calculate_confidence_interval(g1, g2)
    power = calculate_power(effect, len(g1), len(g2))
    collinearity = check_collinearity([{k: v for k, v in r.covariates.items()} for r in records if r.covariates])
    
    result = aggregate_results(t_stat, p_val, effect, ci, "t-test", power, collinearity)
    framed = frame_inference(result)
    
    # Write results
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(framed, f, indent=2)
        
    logger.info(f"Results written to {output_path}")


def run_synthetic_generation(output_path: str, concept_def: Optional[str], thresholds: List[float]) -> None:
    """
    Run synthetic data generation and analysis.
    
    Args:
        output_path: Path to output results.
        concept_def: JSON string of concept definition.
        thresholds: Sensitivity thresholds.
    """
    logger.info("Running synthetic generation...")
    
    concept_dict = json.loads(concept_def) if concept_def else None
    generator = SyntheticDataGenerator()
    records = generator.generate(
        n_samples=1000,
        mean_diff=0.5,
        std_dev=1.0,
        instruction_types=["embodied", "static"]
    )
    
    # Generate mapping log
    mapping_log_path = "data/synthetic/mapping_log.json"
    generate_mapping_log(records, mapping_log_path, physics_params={"gravity": 9.8, "friction": 0.1})
    
    # Analyze
    records = calculate_gain_scores(records)
    
    groups: Dict[str, List[float]] = {}
    for r in records:
        if r.instruction_type not in groups:
            groups[r.instruction_type] = []
        gain = r.post_test_score - r.pre_test_score
        groups[r.instruction_type].append(gain)
        
    if len(groups) < 2:
        logger.error("Insufficient groups.")
        return
        
    g1_keys = list(groups.keys())
    g1 = groups[g1_keys[0]]
    g2 = groups[g1_keys[1]]
    
    t_stat, p_val = run_t_test(g1, g2)
    effect = calculate_effect_size(g1, g2)
    ci = calculate_confidence_interval(g1, g2)
    power = calculate_power(effect, len(g1), len(g2))
    
    result = aggregate_results(t_stat, p_val, effect, ci, "synthetic_t-test", power)
    
    # Sensitivity
    sweep_results = run_sensitivity_sweep(records, thresholds)
    robust = check_robustness_warning(sweep_results)
    result.robustness_warning = robust
    
    framed = frame_inference(result)
    framed["sensitivity_sweep"] = aggregate_results_for_report(sweep_results)
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(framed, f, indent=2)
        
    logger.info(f"Results written to {output_path}")


def main() -> None:
    """Main entry point."""
    args = parse_args()
    setup_logging(log_level=logging.INFO, log_file="data/derivation_logs/cli.log")
    set_seed(args.seed)
    
    if args.mode == 'secondary_analysis':
        if not args.input:
            logger.error("Input path required for secondary analysis.")
            sys.exit(1)
        run_secondary_analysis(args.input, args.output)
    elif args.mode == 'synthetic':
        run_synthetic_generation(args.output, args.concept_definition, args.sweep_thresholds)
    else:
        logger.error("Invalid mode.")
        sys.exit(1)


if __name__ == "__main__":
    main()
