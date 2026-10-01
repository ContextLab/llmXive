import argparse
import sys
import json
import os
import logging
import time
from pathlib import Path

# Fix relative import issue by ensuring we are running as a module or adjusting path
# However, per API surface, we must import as: from .logging_config import setup_logging
# To make this runnable as a script `python code/src/cli.py`, we need to handle imports carefully.
# The error "ImportError: attempted relative import with no known parent package" occurs when
# running the file directly. We will adjust the import logic to support both module execution
# and direct script execution for the CLI.

try:
    from .logging_config import setup_logging
    from .data_loader import load_public_dataset_with_fallback, calculate_gain_scores
    from .synthetic_gen import SyntheticDataGenerator, generate_mapping_log
    from .stats_engine import (
        run_ancova, run_t_test, calculate_effect_size, calculate_confidence_interval,
        apply_bonferroni_correction, check_collinearity, calculate_power, frame_inference,
        aggregate_stats_results, write_partial_results, finalize_results
    )
    from .sensitivity import run_sensitivity_sweep, check_robustness_warning
    from .models import DatasetRecord, AnalysisResult, SensitivitySweep
    from .utils import set_seed
except ImportError:
    # Fallback for direct script execution
    import logging_config
    import data_loader
    import synthetic_gen
    import stats_engine
    import sensitivity
    import models
    import utils
    from logging_config import setup_logging
    from data_loader import load_public_dataset_with_fallback, calculate_gain_scores
    from synthetic_gen import SyntheticDataGenerator, generate_mapping_log
    from stats_engine import (
        run_ancova, run_t_test, calculate_effect_size, calculate_confidence_interval,
        apply_bonferroni_correction, check_collinearity, calculate_power, frame_inference,
        aggregate_stats_results, write_partial_results, finalize_results
    )
    from sensitivity import run_sensitivity_sweep, check_robustness_warning
    from models import DatasetRecord, AnalysisResult, SensitivitySweep
    from utils import set_seed

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Embodied Curriculum Learning Analysis Pipeline")
    parser.add_argument("--mode", type=str, required=True, choices=["secondary_analysis", "synthetic"],
                        help="Analysis mode: secondary_analysis or synthetic")
    parser.add_argument("--input", type=str, help="Path to input CSV (for secondary_analysis)")
    parser.add_argument("--output", type=str, help="Path to output JSON/CSV")
    parser.add_argument("--sweep_thresholds", type=str, default="0.01,0.05,0.10",
                        help="Comma-separated list of thresholds for sensitivity sweep")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--n", type=int, default=1000, help="Number of synthetic samples")
    parser.add_argument("--n_participants", type=int, help="Alias for --n in synthetic mode")
    parser.add_argument("--effect_size", type=float, help="Effect size for synthetic data generation")
    parser.add_argument("--mean_diff_embodied", type=float, default=0.5, help="Mean diff for embodied group")
    parser.add_argument("--mean_diff_static", type=float, default=0.0, help="Mean diff for static group")
    return parser.parse_args()

def run_synthetic_generation(args):
    logger.info(f"Starting synthetic data generation with n={args.n_participants or args.n}")
    set_seed(args.seed)
    n = args.n_participants or args.n

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generator = SyntheticDataGenerator()
    df = generator.generate(n, args.seed, args.mean_diff_embodied, args.mean_diff_static)

    # Write CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic data written to {output_path}")

    # Generate mapping log for synthetic mode
    mapping_log = generate_mapping_log(
        n=n,
        seed=args.seed,
        mean_diff_embodied=args.mean_diff_embodied,
        mean_diff_static=args.mean_diff_static
    )
    mapping_log_path = output_path.parent / "mapping_log.json"
    with open(mapping_log_path, 'w') as f:
        json.dump(mapping_log, f, indent=2)
    logger.info(f"Mapping log written to {mapping_log_path}")

    return df

def run_secondary_analysis(args):
    logger.info("Starting secondary analysis")

    # Load data
    df = load_public_dataset_with_fallback(
        input_path=args.input,
        n=args.n,
        seed=args.seed,
        mean_diff_embodied=args.mean_diff_embodied,
        mean_diff_static=args.mean_diff_static
    )

    if df is None:
        logger.error("Data loading failed. Exiting.")
        sys.exit(1)

    # Calculate gain scores
    df['gain_score'] = calculate_gain_scores(df)

    # Prepare data for stats
    # Assume instruction_type is binary: 0=static, 1=embodied
    # Map string labels to 0/1 if necessary
    if df['instruction_type'].dtype == 'object':
        unique_types = df['instruction_type'].unique()
        mapping = {t: i for i, t in enumerate(unique_types)}
        df['group'] = df['instruction_type'].map(mapping)
    else:
        df['group'] = df['instruction_type']

    gain_scores = df['gain_score'].values
    groups = df['group'].values

    # Run ANCOVA (Primary)
    # Simple ANCOVA: post ~ pre + group
    try:
        model = ols('post_test_score ~ pre_test_score + C(group)', data=df).fit()
        ancova_table = model.summary2().tables[1]
        ancova_results = {
            "f_statistic": float(model.fvalue),
            "p_value": float(model.f_pvalue),
            "coefficients": model.params.to_dict(),
            "adjusted_means": {
                "static": float(model.predict(df.assign(group=0)).mean()),
                "embodied": float(model.predict(df.assign(group=1)).mean())
            }
        }
    except Exception as e:
        logger.warning(f"ANCOVA failed: {e}. Falling back to t-test only.")
        ancova_results = {"error": str(e)}

    # Run t-test (Secondary)
    t_stat, p_val = run_t_test(gain_scores, groups)

    # Bonferroni correction
    n_concepts = 1 # Default, T021b would detect this dynamically
    if 'concept' in df.columns:
        n_concepts = df['concept'].nunique()
    corrected_p = apply_bonferroni_correction(p_val, n_concepts)

    # Effect size
    effect_size = calculate_effect_size(gain_scores, groups)
    ci = calculate_confidence_interval(effect_size, len(groups[groups==0]), len(groups[groups==1]))

    # Collinearity
    collinearity = check_collinearity(df, ['pre_test_score', 'post_test_score'])

    # Power
    power = calculate_power(effect_size, len(groups[groups==0]), len(groups[groups==1]))

    # Aggregate
    stats_dict = aggregate_stats_results(
        ancova_results=ancova_results,
        t_statistic=t_stat,
        p_value=p_val,
        corrected_p_value=corrected_p,
        effect_size=effect_size,
        ci=ci,
        power=power,
        collinearity=collinearity
    )

    # Write partial results (T026b)
    output_path = Path(args.output)
    if not str(output_path).endswith('.json'):
        output_path = output_path.parent / "results_us2.json"

    write_partial_results(stats_dict, str(output_path))

    # Sensitivity Sweep (if thresholds provided)
    thresholds = [float(x) for x in args.sweep_thresholds.split(',')]
    if len(thresholds) > 0:
        sweep_results = run_sensitivity_sweep(df, thresholds)
        if sweep_results:
            final_report = finalize_results(stats_dict, sweep_results)
            # Overwrite or create full report
            final_report_path = output_path.parent / "results.json"
            write_partial_results(final_report, str(final_report_path))
            logger.info(f"Full report written to {final_report_path}")

    return stats_dict

def run_analysis_pipeline(args):
    if args.mode == "synthetic":
        return run_synthetic_generation(args)
    elif args.mode == "secondary_analysis":
        return run_secondary_analysis(args)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")

def main():
    args = parse_args()
    setup_logging()
    logger.info(f"CLI started with mode: {args.mode}")

    try:
        result = run_analysis_pipeline(args)
        logger.info("Analysis completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
