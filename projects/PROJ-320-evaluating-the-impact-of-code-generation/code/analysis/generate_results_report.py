import os
import json
import sys
from pathlib import Path
from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary

logger = None

def load_json_file(file_path: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def interpret_cohen_d(d: float) -> str:
    """
    Classify the magnitude of Cohen's d effect size.
    
    Thresholds (Cohen, 1988):
      |d| < 0.2  -> 'negligible'
      0.2 <= |d| < 0.5 -> 'small'
      0.5 <= |d| < 0.8 -> 'medium'
      |d| >= 0.8 -> 'large'
    
    Args:
        d: Cohen's d value (can be negative).
    
    Returns:
        A string label describing the magnitude.
    """
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def aggregate_results(results_dir: Path) -> dict:
    """
    Aggregate all statistical results from the analysis phase.
    Reads from data/processed/results.json (produced by T027) and
    data/audit/error_rate.json (produced by T019b).
    """
    results_file = results_dir / "results.json"
    error_rate_file = results_dir.parent / "audit" / "error_rate.json"
    
    if not results_file.exists():
        raise FileNotFoundError(f"Statistical results not found: {results_file}. "
                              "Ensure T027 (generate_results_report) has run.")
    
    stats_data = load_json_file(results_file)
    
    # Load error rate for gate checking
    if not error_rate_file.exists():
        raise FileNotFoundError(f"Audit error rate file not found: {error_rate_file}. "
                              "Ensure T019b (manual_validation) has run.")
    
    error_data = load_json_file(error_rate_file)
    
    return {
        "statistics": stats_data,
        "audit_error_rate": error_data.get("error_rate", None),
        "audit_threshold": error_data.get("threshold", 0.05),
        "audit_status": error_data.get("status", "unknown")
    }

def generate_results_report(aggregate_data: dict, output_path: Path) -> dict:
    """
    Generate the final results report JSON.
    
    This function implements the gate logic for T028 and T047:
    - Reads the error rate from audit results
    - Determines gate_status: 'passed' if error_rate <= 0.05, 'blocked' otherwise
    - Appends qualitative interpretation of Cohen's d effect sizes (T047)
    - Writes gate_status to data/processed/gate_status.json
    - Does NOT block Phase 4 execution, only final aggregation
    
    Returns the full report data including gate status and effect size interpretations.
    """
    audit_error_rate = aggregate_data.get("audit_error_rate")
    audit_threshold = aggregate_data.get("audit_threshold", 0.05)
    
    # Determine gate status
    if audit_error_rate is None:
        logger.warning("Error rate not found in audit results. Setting gate_status to 'blocked'.")
        gate_status = "blocked"
    elif audit_error_rate > audit_threshold:
        logger.warning(f"Error rate {audit_error_rate} exceeds threshold {audit_threshold}. Gate blocked.")
        gate_status = "blocked"
    else:
        logger.info(f"Error rate {audit_error_rate} is within threshold {audit_threshold}. Gate passed.")
        gate_status = "passed"
    
    # Write gate_status to data/processed/gate_status.json
    # Note: Schema requires 'status' key per T028 spec
    gate_status_file = output_path.parent / "gate_status.json"
    gate_status_data = {
        "status": gate_status,
        "error_rate": audit_error_rate,
        "threshold": audit_threshold
    }
    
    with open(gate_status_file, 'w', encoding='utf-8') as f:
        json.dump(gate_status_data, f, indent=2)
    
    logger.info(f"Gate status written to {gate_status_file}: {gate_status}")
    
    # Process statistical results to add effect size interpretations (T047)
    stats_data = aggregate_data.get("statistics", {})
    interpreted_stats = {}
    
    for metric_name, metric_results in stats_data.items():
        if isinstance(metric_results, dict):
            interpreted_results = metric_results.copy()
            # Check for effect_size key (Cohen's d)
            if "effect_size" in interpreted_results:
                d_value = interpreted_results["effect_size"]
                if isinstance(d_value, (int, float)):
                    magnitude = interpret_cohen_d(d_value)
                    interpreted_results["effect_size_magnitude"] = magnitude
                    logger.debug(f"Interpreted effect size for {metric_name}: {d_value} -> {magnitude}")
            interpreted_stats[metric_name] = interpreted_results
        else:
            interpreted_stats[metric_name] = metric_results
    
    # Return the full report data (for T037 to use)
    return {
        "status": gate_status,
        "error_rate": audit_error_rate,
        "threshold": audit_threshold,
        "statistics": interpreted_stats
    }

def main():
    """
    Main entry point for generating the results report.
    
    This script:
    1. Loads statistical results from data/processed/results.json
    2. Loads audit error rate from data/audit/error_rate.json
    3. Determines gate_status based on error rate threshold (0.05)
    4. Adds qualitative interpretation to effect sizes (T047)
    5. Writes gate_status to data/processed/gate_status.json
    6. Writes full report to data/processed/results.json (updated with interpretations)
    """
    global logger
    
    # Setup logging
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging("generate_results_report", log_dir / "generate_results_report.log")
    logger.info("Starting results report generation (T028 + T047)")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    results_dir = project_root / "data" / "processed"
    output_path = results_dir / "results.json"
    
    try:
        # Aggregate results
        logger.info("Aggregating statistical results...")
        aggregate_data = aggregate_results(results_dir)
        
        # Generate report with gate logic and effect size interpretations
        logger.info("Generating results report with gate status and effect size interpretations...")
        report_data = generate_results_report(aggregate_data, output_path)
        
        # Save full report (overwrites existing results.json with interpretations)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Results report saved to {output_path}")
        logger.info(f"Gate status: {report_data['status']}")
        
        # Log effect size interpretations
        stats = report_data.get("statistics", {})
        for metric, data in stats.items():
            if isinstance(data, dict) and "effect_size_magnitude" in data:
                logger.info(f"  {metric}: effect_size={data.get('effect_size')}, magnitude={data['effect_size_magnitude']}")
        
        # Exit with appropriate code
        if report_data['status'] == 'blocked':
            logger.warning("Gate is BLOCKED. Final report generation should not proceed.")
            sys.exit(0)  # Exit cleanly - gate status is recorded
        else:
            logger.info("Gate is PASSED. Final report generation can proceed.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()