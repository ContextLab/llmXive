import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Import from existing API surface
from config.seeds import get_seed

def setup_review_logger(log_path: Optional[Path] = None) -> logging.Logger:
    """Setup a dedicated logger for the statistical power review."""
    logger = logging.getLogger("statistical_power_review")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

def load_statistical_results(results_path: Path) -> Dict[str, Any]:
    """Load the statistical test results from T028."""
    if not results_path.exists():
        raise FileNotFoundError(f"Statistical results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    required_keys = ['p_value', 'statistical_power', 'effect_size_cohens_d']
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        raise ValueError(f"Statistical results missing required keys: {missing_keys}")
    
    return data

def interpret_statistical_power(power: float, threshold: float = 0.8) -> str:
    """
    Interpret the statistical power value.
    
    Args:
        power: The calculated statistical power.
        threshold: The minimum acceptable power (default 0.8).
        
    Returns:
        A string interpretation of the power value.
    """
    if power >= threshold:
        return (
            f"Statistical power ({power:.4f}) exceeds the recommended threshold of {threshold}. "
            "The study has sufficient power to detect the observed effect size."
        )
    else:
        return (
            f"Statistical power ({power:.4f}) is below the recommended threshold of {threshold}. "
            "The study may be underpowered to reliably detect the observed effect size. "
            "Interpretation of significance should be made with caution, and future studies "
            "might require a larger sample size to increase power."
        )

def analyze_effect_size(cohens_d: float) -> Dict[str, Any]:
    """
    Analyze the effect size (Cohen's d) magnitude.
    
    Args:
        cohens_d: The calculated Cohen's d value.
        
    Returns:
        A dictionary with magnitude classification and interpretation.
    """
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        magnitude = "negligible"
        interpretation = "The effect size is negligible, suggesting little practical difference."
    elif abs_d < 0.5:
        magnitude = "small"
        interpretation = "The effect size is small, indicating a modest practical difference."
    elif abs_d < 0.8:
        magnitude = "medium"
        interpretation = "The effect size is medium, indicating a moderate practical difference."
    else:
        magnitude = "large"
        interpretation = "The effect size is large, indicating a substantial practical difference."
    
    return {
        "magnitude": magnitude,
        "interpretation": interpretation,
        "value": cohens_d
    }

def generate_power_review_report(
    stats_results: Dict[str, Any],
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Generate a comprehensive power analysis review report.
    
    Args:
        stats_results: The statistical test results from T028.
        threshold: The minimum acceptable power threshold.
        
    Returns:
        A dictionary containing the full review report.
    """
    power = stats_results['statistical_power']
    p_value = stats_results['p_value']
    cohens_d = stats_results['effect_size_cohens_d']
    
    power_interpretation = interpret_statistical_power(power, threshold)
    effect_analysis = analyze_effect_size(cohens_d)
    
    # Determine if limitation should be documented
    is_underpowered = power < threshold
    
    report = {
        "power_value": power,
        "threshold": threshold,
        "is_underpowered": is_underpowered,
        "power_interpretation": power_interpretation,
        "effect_size_analysis": effect_analysis,
        "p_value": p_value,
        "summary": (
            f"The statistical power analysis indicates a power of {power:.4f}. "
            f"{'The study is adequately powered.' if not is_underpowered else 'The study is underpowered.'} "
            f"The effect size (Cohen's d = {cohens_d:.4f}) is classified as {effect_analysis['magnitude']}. "
            f"The paired t-test yielded a p-value of {p_value:.6f}."
        )
    }
    
    if is_underpowered:
        report["limitation_note"] = (
            "LIMITATION: The statistical power is below the recommended threshold of 0.8. "
            "This suggests that the sample size (number of molecules in the ESOL dataset) may be insufficient "
            "to reliably detect the observed effect size between the Random Forest baseline and the GNN model. "
            "While the observed difference may be statistically significant (p < 0.05), the risk of Type II error "
            "(failing to detect a true effect) is elevated. Future studies with larger pharmaceutical datasets "
            "should be conducted to confirm these findings with higher statistical confidence."
        )
    
    return report

def save_review_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the power review report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def append_to_final_report(
    power_review_report: Dict[str, Any],
    final_report_path: Path
) -> None:
    """
    Append the power analysis summary section to the final report markdown.
    
    Args:
        power_review_report: The generated power review report.
        final_report_path: Path to the final report markdown file.
    """
    if not final_report_path.exists():
        logging.warning(f"Final report not found at {final_report_path}. Creating new file.")
        final_report_path.parent.mkdir(parents=True, exist_ok=True)
        content = "# Final Report: Predicting Solubility of Pharmaceutical Compounds\n\n"
        with open(final_report_path, 'w') as f:
            f.write(content)
    
    section_content = f"""
## Statistical Power Analysis

### Power Value
- **Calculated Power**: {power_review_report['power_value']:.4f}
- **Recommended Threshold**: {power_review_report['threshold']}
- **Status**: {'Adequately Powered' if not power_review_report['is_underpowered'] else 'Underpowered'}

### Interpretation
{power_review_report['power_interpretation']}

### Effect Size Analysis
- **Cohen's d**: {power_review_report['effect_size_analysis']['value']:.4f}
- **Magnitude**: {power_review_report['effect_size_analysis']['magnitude']}
- **Interpretation**: {power_review_report['effect_size_analysis']['interpretation']}

### Summary
{power_review_report['summary']}
"""
    
    if power_review_report.get('limitation_note'):
        section_content += f"\n### Limitations\n{power_review_report['limitation_note']}\n"
    
    with open(final_report_path, 'a') as f:
        f.write(section_content)

def main():
    """Main entry point for the statistical power review task (T049)."""
    parser = argparse.ArgumentParser(description="T049: Statistical Power Review & Reporting")
    parser.add_argument(
        "--stats-results",
        type=Path,
        default=Path("results/statistical_test.json"),
        help="Path to the statistical test results (from T028)"
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=Path("results/power_review_report.json"),
        help="Path to save the power review report"
    )
    parser.add_argument(
        "--final-report",
        type=Path,
        default=Path("docs/reports/final_report.md"),
        help="Path to the final report to append the power analysis section"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("data/logs/power_review.log"),
        help="Path to the log file"
    )
    
    args = parser.parse_args()
    
    logger = setup_review_logger(args.log_file)
    logger.info("Starting Statistical Power Review (T049)")
    
    try:
        # Load statistical results from T028
        logger.info(f"Loading statistical results from {args.stats_results}")
        stats_results = load_statistical_results(args.stats_results)
        
        # Generate power review report
        logger.info("Generating power analysis report")
        power_review_report = generate_power_review_report(stats_results)
        
        # Save the JSON report
        logger.info(f"Saving power review report to {args.output_report}")
        save_review_report(power_review_report, args.output_report)
        
        # Append to final report
        logger.info(f"Appending power analysis summary to {args.final_report}")
        append_to_final_report(power_review_report, args.final_report)
        
        logger.info("Statistical Power Review completed successfully")
        print(json.dumps(power_review_report, indent=2))
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()