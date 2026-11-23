import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Ensure imports work relative to project root if run as module
try:
    from benchmark.analyze_failures import classify_failure
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from benchmark.analyze_failures import classify_failure

from config import Config

def load_jsonl(file_path: str) -> list:
    """Load a JSONL file into a list of dictionaries."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def load_json(file_path: str) -> dict:
    """Load a JSON file into a dictionary."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_csv_as_dict(file_path: str) -> dict:
    """Load a CSV file into a dictionary keyed by scene_id."""
    import csv
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    data = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'scene_id' in row:
                data[row['scene_id']] = row
    return data

def generate_report(
    benchmark_results_path: str,
    failure_classification_path: str,
    output_path: str
):
    """
    Generate a Markdown report summarizing failure analysis.
    
    Args:
        benchmark_results_path: Path to data/results/benchmark_results.csv
        failure_classification_path: Path to data/derived/failure_classification.json
        output_path: Path to write the markdown report
    """
    # Load data
    try:
        benchmark_data = load_csv_as_dict(benchmark_results_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    try:
        failure_data = load_json(failure_classification_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # If failure_data is a list (as per T021 spec), ensure we can process it
    if isinstance(failure_data, list):
        # Check if it has the summary key or if we need to compute it
        # Assuming the list contains the detailed failures and maybe a summary object at the end or separate
        # T021 spec says: "The summary object (if separate) or the aggregate calculation MUST include the key semantic_gap_proportion"
        # Let's assume the list is the detailed entries, and we look for a summary or compute it.
        # However, the task says T021 generates `failure_classification.json`. 
        # Let's assume the file might be a list of failures + a summary, or just a list.
        # We will iterate the list to count types.
        detailed_failures = [item for item in failure_data if isinstance(item, dict) and 'scene_id' in item]
        
        # Check for a summary object in the list (sometimes appended)
        summary_obj = next((item for item in failure_data if isinstance(item, dict) and 'semantic_gap_proportion' in item), None)
        
        if summary_obj:
            semantic_gap_proportion = summary_obj.get('semantic_gap_proportion', 0.0)
        else:
            # Compute from detailed failures if summary is missing
            total_symbolic_fail = len(detailed_failures)
            if total_symbolic_fail == 0:
                semantic_gap_proportion = 0.0
            else:
                # Count VLM_correct AND Symbolic_fail (which is what detailed_failures represents if it's only failures)
                # Actually, the detailed list is usually just the failures.
                # The proportion is count(VLM_correct AND Symbolic_fail) / count(Symbolic_fail)
                # If the list contains all symbolic failures, we check VLM status in each.
                vlm_correct_count = 0
                for item in detailed_failures:
                    # Check if VLM was correct in this failure case
                    # We need to cross-reference with benchmark results if VLM status isn't in the failure item
                    scene_id = item.get('scene_id')
                    if scene_id in benchmark_data:
                        # In benchmark_results, we have symbolic_pred, vlm_pred, ground_truth
                        # If symbolic_pred != ground_truth, it's a failure.
                        # If vlm_pred == ground_truth, then VLM was correct.
                        b_row = benchmark_data[scene_id]
                        try:
                            s_pred = int(b_row['symbolic_pred'])
                            v_pred = int(b_row['vlm_pred'])
                            gt = int(b_row['ground_truth'])
                            if s_pred != gt and v_pred == gt:
                                vlm_correct_count += 1
                        except (ValueError, KeyError):
                            pass
                semantic_gap_proportion = vlm_correct_count / total_symbolic_fail if total_symbolic_fail > 0 else 0.0

        failure_list = detailed_failures
    elif isinstance(failure_data, dict):
        # If it's a dict with a 'failures' key or similar
        if 'failures' in failure_data:
            failure_list = failure_data['failures']
        else:
            failure_list = []
        semantic_gap_proportion = failure_data.get('semantic_gap_proportion', 0.0)
    else:
        failure_list = []
        semantic_gap_proportion = 0.0

    # Count categories
    geometric_ambiguity_count = 0
    semantic_gap_count = 0
    
    # Also collect representative examples
    geo_examples = []
    sem_examples = []
    
    for item in failure_list:
        classification = item.get('classification', 'Unknown')
        if classification == 'Geometric Ambiguity':
            geometric_ambiguity_count += 1
            if len(geo_examples) < 3:
                geo_examples.append(item)
        elif classification == 'Semantic Gap':
            semantic_gap_count += 1
            if len(sem_examples) < 3:
                sem_examples.append(item)
        else:
            # Could be other or unknown
            pass

    total_failures = geometric_ambiguity_count + semantic_gap_count

    # Generate Report
    report_lines = []
    report_lines.append("# Failure Analysis Report")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("## Summary")
    report_lines.append("")
    report_lines.append(f"- **Total Symbolic Failures:** {total_failures}")
    report_lines.append(f"- **Geometric Ambiguity:** {geometric_ambiguity_count}")
    report_lines.append(f"- **Semantic Gap:** {semantic_gap_count}")
    report_lines.append(f"- **Semantic Gap Proportion:** {semantic_gap_proportion:.4f}")
    report_lines.append("")
    report_lines.append("## Representative Failure Cases")
    report_lines.append("")

    if geometric_ambiguity_count > 0:
        report_lines.append("### Geometric Ambiguity")
        report_lines.append("")
        report_lines.append("| Scene ID | Explanation |")
        report_lines.append("|---|---|")
        for ex in geo_examples:
            scene_id = ex.get('scene_id', 'N/A')
            reason = ex.get('reason', 'No explanation provided.')
            # Clean up reason for markdown table
            reason = reason.replace('\n', ' ').replace('|', '\\|')
            report_lines.append(f"| {scene_id} | {reason} |")
        report_lines.append("")

    if semantic_gap_count > 0:
        report_lines.append("### Semantic Gap")
        report_lines.append("")
        report_lines.append("| Scene ID | Explanation |")
        report_lines.append("|---|---|")
        for ex in sem_examples:
            scene_id = ex.get('scene_id', 'N/A')
            reason = ex.get('reason', 'No explanation provided.')
            reason = reason.replace('\n', ' ').replace('|', '\\|')
            report_lines.append(f"| {scene_id} | {reason} |")
        report_lines.append("")

    # Write to file
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Report generated at: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate failure analysis report.")
    parser.add_argument("--results", type=str, required=True, help="Path to benchmark_results.csv")
    parser.add_argument("--classification", type=str, required=True, help="Path to failure_classification.json")
    parser.add_argument("--output", type=str, required=True, help="Path to output markdown report")
    
    args = parser.parse_args()
    
    generate_report(
        benchmark_results_path=args.results,
        failure_classification_path=args.classification,
        output_path=args.output
    )

if __name__ == "__main__":
    main()
