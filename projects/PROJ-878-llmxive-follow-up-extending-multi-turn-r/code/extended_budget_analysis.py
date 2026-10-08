"""
Extended Budget Analysis (Task T036)

Compares short-horizon failures (50-turn timeouts) vs long-horizon convergences (1000-turn results)
to quantify the rate of budget exhaustion.

Reads:
  - data/processed/extended_budget_log.csv (1000-turn results)
  - data/processed/execution_log.csv (50-turn results)

Outputs:
  - results/extended_budget_analysis.md (Markdown report with percentage)
"""
import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a CSV file and return a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    data = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    logger.info(f"Loaded {len(data)} rows from {file_path}")
    return data

def analyze_budget_exhaustion(
    primary_log_path: Path,
    extended_log_path: Path
) -> Dict[str, Any]:
    """
    Calculate the rate of budget exhaustion.
    
    Formula:
      rate = (count of instances in extended_log with convergence_status='success' 
              AND turns_to_converge <= 1000) 
             / (count of instances in primary_log with convergence_status='timeout') 
             * 100
    """
    # Load data
    try:
        primary_data = load_csv_file(primary_log_path)
        extended_data = load_csv_file(extended_log_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # Count primary log timeouts
    primary_timeouts = [
        row for row in primary_data 
        if row.get('convergence_status') == 'timeout'
    ]
    count_primary_timeouts = len(primary_timeouts)
    
    logger.info(f"Primary log timeouts (50-turn limit): {count_primary_timeouts}")

    if count_primary_timeouts == 0:
        logger.warning("No timeouts found in primary log. Rate cannot be calculated (division by zero).")
        return {
            'count_primary_timeouts': 0,
            'count_extended_successes': 0,
            'rate': 0.0,
            'message': "No timeouts in primary log to compare against."
        }

    # Count extended log successes within budget (<= 1000 turns)
    extended_successes = [
        row for row in extended_data
        if row.get('convergence_status') == 'success' 
        and int(row.get('turns_to_converge', 0)) <= 1000
    ]
    count_extended_successes = len(extended_successes)
    
    logger.info(f"Extended log successes (<= 1000 turns): {count_extended_successes}")

    # Calculate rate
    rate = (count_extended_successes / count_primary_timeouts) * 100

    return {
        'count_primary_timeouts': count_primary_timeouts,
        'count_extended_successes': count_extended_successes,
        'rate': rate,
        'message': "Calculation complete."
    }

def write_report(results: Dict[str, Any], output_path: Path) -> None:
    """Write the analysis results to a Markdown file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Extended Budget Analysis Report\n\n")
        f.write("## Overview\n")
        f.write("This report quantifies the rate of budget exhaustion by comparing short-horizon failures \n")
        f.write("(50-turn timeouts) against long-horizon convergences (1000-turn results).\n\n")
        
        f.write("## Methodology\n")
        f.write("The rate of budget exhaustion is calculated as:\n")
        f.write("```\n")
        f.write("Rate = (Count of extended_log successes with turns <= 1000) / ")
        f.write("(Count of primary_log timeouts) * 100\n")
        f.write("```\n\n")
        
        f.write("## Results\n\n")
        f.write(f"- **Primary Log Timeouts (50-turn limit)**: {results['count_primary_timeouts']}\n")
        f.write(f"- **Extended Log Successes (<= 1000 turns)**: {results['count_extended_successes']}\n")
        f.write(f"- **Rate of Budget Exhaustion**: **{results['rate']:.2f}%**\n\n")
        
        if results['count_primary_timeouts'] == 0:
            f.write("## Note\n")
            f.write("No timeouts were found in the primary log. The rate calculation is not applicable.\n")
        else:
            f.write("## Interpretation\n")
            if results['rate'] >= 90:
                f.write("A high rate (>90%) indicates that most timeouts were due to insufficient budget rather \n")
                f.write("than inherent reasoning failure. Extending the turn limit allows the model to converge.\n")
            elif results['rate'] >= 50:
                f.write("A moderate rate (50-90%) suggests a mix of budget exhaustion and genuine reasoning failure.\n")
            else:
                f.write("A low rate (<50%) indicates that even with extended budget, many instances fail to converge, \n")
                f.write("suggesting inherent reasoning limitations.\n")

def main():
    """Main entry point for the analysis."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    primary_log_path = project_root / "data" / "processed" / "execution_log.csv"
    extended_log_path = project_root / "data" / "processed" / "extended_budget_log.csv"
    output_path = project_root / "results" / "extended_budget_analysis.md"

    logger.info(f"Primary log path: {primary_log_path}")
    logger.info(f"Extended log path: {extended_log_path}")
    logger.info(f"Output path: {output_path}")

    try:
        results = analyze_budget_exhaustion(primary_log_path, extended_log_path)
        write_report(results, output_path)
        logger.info(f"Report written to {output_path}")
        print(f"Analysis complete. Rate of budget exhaustion: {results['rate']:.2f}%")
    except FileNotFoundError as e:
        logger.error(f"Failed to run analysis: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
