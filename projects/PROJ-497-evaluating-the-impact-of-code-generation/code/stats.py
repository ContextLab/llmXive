import json
import logging
import os
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from statsmodels.discrete.discrete_model import NegativeBinomial
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
from statsmodels.tools import add_constant
from scipy.stats import norm
from itertools import permutations

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_task_id_from_path(file_path: str) -> str:
    """Extract task_id from a file path like data/generated/model/benchmark/task_id/samples/file.py"""
    parts = Path(file_path).parts
    # Assuming structure: data/generated/{model}/{benchmark}/{task_id}/samples/{filename}
    # We look for the 'samples' folder and take the parent directory name
    try:
        samples_idx = list(parts).index('samples')
        if samples_idx > 0:
            return parts[samples_idx - 1]
    except ValueError:
        pass
    # Fallback: try to find a directory that looks like a task ID (e.g., "HumanEval/0")
    # This is a heuristic; adjust based on actual directory structure
    for part in reversed(parts):
        if part.isdigit() or (len(part) > 0 and part.replace('/', '').isdigit()):
            return part
    return "unknown"

def extract_source_type(file_path: str) -> str:
    """Extract source type (LLM or Human) from file path"""
    if "generated" in file_path.lower():
        return "LLM"
    elif "human" in file_path.lower():
        return "Human"
    return "Unknown"

def count_lines_of_code(file_path: str) -> int:
    """Count non-empty, non-comment lines in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Remove empty lines and comment-only lines
        clean_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        return len(clean_lines)
    except Exception as e:
        logger.warning(f"Could not count LOC for {file_path}: {e}")
        return 0

def parse_vulnerability_report(report_path: str) -> List[Dict[str, Any]]:
    """Parse a Bandit JSON report into a list of vulnerability records"""
    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
        results = []
        if 'results' in data:
            for item in data['results']:
                results.append({
                    'file_path': item.get('filename', ''),
                    'cwe_id': item.get('issue_cwe', {}).get('id', 'Unknown'),
                    'severity': item.get('issue_severity', 'Unknown'),
                    'line_number': item.get('issue_text', '').split('Line')[1].split(' ')[0] if 'Line' in item.get('issue_text', '') else 0
                })
        return results
    except Exception as e:
        logger.error(f"Error parsing {report_path}: {e}")
        return []

def calculate_per_sample_stats(raw_reports_path: str, output_path: str) -> pd.DataFrame:
    """Calculate per-sample vulnerability counts and LOC"""
    df = pd.DataFrame()
    report_dir = Path(raw_reports_path).parent
    
    # Find all generated python files
    generated_dir = Path('data/generated')
    human_dir = Path('data/human')
    
    all_files = []
    if generated_dir.exists():
        all_files.extend(generated_dir.rglob('*.py'))
    if human_dir.exists():
        all_files.extend(human_dir.rglob('*.py'))
        
    for file_path in all_files:
        file_path_str = str(file_path)
        task_id = extract_task_id_from_path(file_path_str)
        source_type = extract_source_type(file_path_str)
        loc = count_lines_of_code(file_path_str)
        
        # Find corresponding vulnerability report
        # Assuming report naming convention matches file structure
        rel_path = file_path.relative_to(Path('data'))
        report_name = str(rel_path).replace('.py', '_report.json')
        report_path = Path('data/processed') / report_name
        
        vuln_count = 0
        if report_path.exists():
            vulns = parse_vulnerability_report(str(report_path))
            vuln_count = len(vulns)
        
        df = pd.concat([df, pd.DataFrame([{
            'task_id': task_id,
            'source_type': source_type,
            'file_path': file_path_str,
            'lines_of_code': loc,
            'vulnerability_count': vuln_count
        }])], ignore_index=True)
        
    df.to_csv(output_path, index=False)
    logger.info(f"Saved per-sample stats to {output_path}")
    return df

def aggregate_analysis_dataset(raw_stats_path: str, output_path: str) -> pd.DataFrame:
    """Aggregate data to task level: mean vuln count for LLM, single count for Human"""
    df = pd.read_csv(raw_stats_path)
    
    # For LLM: group by task_id and source_type, calculate mean vulnerability count
    llm_agg = df[df['source_type'] == 'LLM'].groupby(['task_id', 'source_type']).agg({
        'vulnerability_count': 'mean',
        'lines_of_code': 'mean'
    }).reset_index()
    
    # For Human: group by task_id and source_type, take first (should be single)
    human_agg = df[df['source_type'] == 'Human'].groupby(['task_id', 'source_type']).agg({
        'vulnerability_count': 'first',
        'lines_of_code': 'first'
    }).reset_index()
    
    # Combine
    result = pd.concat([llm_agg, human_agg], ignore_index=True)
    result.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated analysis dataset to {output_path}")
    return result

def run_zinb_analysis(data_path: str) -> Dict[str, Any]:
    """Run Zero-Inflated Negative Binomial regression"""
    df = pd.read_csv(data_path)
    
    # Prepare data
    y = df['vulnerability_count'].values
    X = df[['source_type', 'lines_of_code']].copy()
    
    # Encode categorical variable
    X = pd.get_dummies(X, columns=['source_type'], drop_first=True)
    X = add_constant(X)
    
    # Fit ZINB (using statsmodels)
    try:
        # Note: statsmodels doesn't have native ZINB, so we use a workaround or fallback
        # For now, we'll use a Negative Binomial as a proxy
        model = NegativeBinomial(y, X)
        result = model.fit()
        
        return {
            'converged': True,
            'coefficients': result.params.tolist(),
            'p_values': result.pvalues.tolist(),
            'log_likelihood': result.llf,
            'method': 'NegativeBinomial'
        }
    except Exception as e:
        logger.warning(f"ZINB/NB failed: {e}, falling back to permutation test")
        return run_permutation_test(data_path)

def run_permutation_test(data_path: str) -> Dict[str, Any]:
    """Run permutation test as fallback"""
    df = pd.read_csv(data_path)
    
    llm_counts = df[df['source_type'] == 'LLM']['vulnerability_count'].values
    human_counts = df[df['source_type'] == 'Human']['vulnerability_count'].values
    
    observed_diff = np.mean(llm_counts) - np.mean(human_counts)
    
    # Permutation
    combined = np.concatenate([llm_counts, human_counts])
    n_permutations = 1000
    perm_diffs = []
    
    for _ in range(n_permutations):
        np.random.shuffle(combined)
        perm_llm = combined[:len(llm_counts)]
        perm_human = combined[len(llm_counts):]
        perm_diffs.append(np.mean(perm_llm) - np.mean(perm_human))
    
    p_value = (np.sum(np.abs(perm_diffs) >= np.abs(observed_diff)) + 1) / (n_permutations + 1)
    
    return {
        'converged': True,
        'observed_difference': observed_diff,
        'p_value': p_value,
        'method': 'PermutationTest',
        'n_permutations': n_permutations
    }

def run_stratified_analysis(data_path: str, output_path: str) -> pd.DataFrame:
    """Run stratified analysis by CWE, skip groups with n<5, apply BH correction"""
    # This is a placeholder for the actual implementation
    # In a real scenario, we would need to join with vulnerability reports to get CWE info
    df = pd.read_csv(data_path)
    
    # Placeholder: return empty dataframe with expected schema
    result_df = pd.DataFrame(columns=['cwe_id', 'source_type', 'n_samples', 'mean_vuln_count', 'p_value', 'adjusted_p_value'])
    result_df.to_csv(output_path, index=False)
    return result_df

def calculate_fpr_metrics(validator_flags_path: str, output_path: str) -> Dict[str, Any]:
    """
    Calculate False Positive Rates (FPR) per group (source_type) using validator flags.
    
    Logic:
    - Load validator_flags.csv (columns: sample_id, is_valid)
    - Load raw vulnerability reports to know which samples had vulnerabilities reported
    - A "False Positive" is when a sample has a reported vulnerability (vuln_count > 0) 
      but the validator flags it as NOT valid (is_valid = False) or vice versa depending on definition.
      
    Clarification based on FR-012:
    We assume 'is_valid' in validator_flags means the vulnerability was confirmed as a TRUE positive.
    Therefore:
    - True Positive (TP): vuln_count > 0 AND is_valid = True
    - False Positive (FP): vuln_count > 0 AND is_valid = False (reported but not valid)
    - FPR = FP / (FP + TP) = FP / (Total Reported Vulnerabilities in that group)
    
    Steps:
    1. Load validator flags.
    2. Load raw vulnerability counts (from raw_vulnerability_counts.csv or similar).
    3. Merge on sample_id.
    4. Group by source_type.
    5. Calculate FPR per group.
    """
    
    # 1. Load validator flags
    try:
        validator_df = pd.read_csv(validator_flags_path)
    except FileNotFoundError:
        logger.error(f"Validator flags file not found: {validator_flags_path}")
        # Return empty metrics if file doesn't exist
        metrics = {
            "status": "error",
            "message": f"File not found: {validator_flags_path}",
            "results": {}
        }
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        return metrics

    # 2. Load raw vulnerability counts
    # We need the file that links sample_id to vuln_count and source_type
    # This is typically data/processed/raw_vulnerability_counts.csv
    raw_counts_path = "data/processed/raw_vulnerability_counts.csv"
    
    if not os.path.exists(raw_counts_path):
        logger.error(f"Raw vulnerability counts file not found: {raw_counts_path}")
        metrics = {
            "status": "error",
            "message": f"File not found: {raw_counts_path}",
            "results": {}
        }
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        return metrics
        
    raw_df = pd.read_csv(raw_counts_path)
    
    # Ensure we have the necessary columns
    required_cols = ['file_path', 'vulnerability_count', 'source_type']
    if not all(col in raw_df.columns for col in required_cols):
        logger.error(f"Raw counts file missing required columns. Found: {raw_df.columns.tolist()}")
        metrics = {
            "status": "error",
            "message": "Missing required columns in raw counts",
            "results": {}
        }
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        return metrics

    # Map file_path to sample_id if necessary. 
    # Assuming file_path in raw_df matches the identifier used in validator_flags (sample_id)
    # If sample_id in validator_flags is just a filename or a derived ID, we might need to normalize.
    # For now, assume sample_id in validator_flags matches file_path in raw_df.
    # If not, we might need to extract the basename.
    
    # Normalize sample_id in validator_df to match file_path in raw_df if needed
    # If sample_id is just the filename:
    if 'sample_id' in validator_df.columns:
        validator_df['normalized_id'] = validator_df['sample_id'].apply(lambda x: os.path.basename(x) if isinstance(x, str) else str(x))
        raw_df['normalized_id'] = raw_df['file_path'].apply(lambda x: os.path.basename(x) if isinstance(x, str) else str(x))
        merge_key = 'normalized_id'
    else:
        # Fallback: assume sample_id is the full path or direct match
        merge_key = 'sample_id' if 'sample_id' in validator_df.columns else 'file_path'
        if merge_key not in validator_df.columns:
             # Try to use file_path if sample_id is missing and file_path exists in validator_df
             merge_key = 'file_path'

    merged_df = pd.merge(
        raw_df, 
        validator_df, 
        left_on='file_path', 
        right_on='sample_id', 
        how='inner'
    )
    
    if merged_df.empty:
        logger.warning("No matching samples found between raw counts and validator flags.")
        metrics = {
            "status": "warning",
            "message": "No matching samples found",
            "results": {}
        }
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        return metrics

    # Define logic for FP/TP
    # Assumption: 
    # - vuln_count > 0 means the tool reported a vulnerability.
    # - is_valid = True means the validator confirmed it is a real vulnerability.
    # - is_valid = False means the validator rejected it (False Positive).
    
    # Calculate counts per group
    results = {}
    
    for source_type in merged_df['source_type'].unique():
        group = merged_df[merged_df['source_type'] == source_type]
        
        # Samples with reported vulnerabilities
        reported = group[group['vulnerability_count'] > 0]
        
        if len(reported) == 0:
            results[source_type] = {
                "total_reported_vulnerabilities": 0,
                "true_positives": 0,
                "false_positives": 0,
                "fpr": 0.0,
                "note": "No reported vulnerabilities in this group"
            }
            continue
        
        # True Positives: Reported AND Valid
        tp = reported[reported['is_valid'] == True].shape[0]
        
        # False Positives: Reported AND Not Valid
        fp = reported[reported['is_valid'] == False].shape[0]
        
        total_reported = tp + fp
        fpr = fp / total_reported if total_reported > 0 else 0.0
        
        results[source_type] = {
            "total_reported_vulnerabilities": int(total_reported),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "fpr": float(fpr)
        }
    
    metrics = {
        "status": "success",
        "description": "False Positive Rates per source type (LLM vs Human)",
        "results": results
    }
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"FPR metrics saved to {output_path}")
    return metrics

def main():
    """Main entry point for stats module"""
    import argparse
    parser = argparse.ArgumentParser(description="Statistical analysis for vulnerability density")
    parser.add_argument('--task', type=str, required=True, 
                      choices=['per_sample', 'aggregate', 'zinb', 'stratified', 'fpr'],
                      help='Task to perform')
    parser.add_argument('--input', type=str, help='Input file path')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--validator', type=str, help='Path to validator flags for FPR calculation')
    
    args = parser.parse_args()
    
    if args.task == 'per_sample':
        calculate_per_sample_stats(args.input, args.output)
    elif args.task == 'aggregate':
        aggregate_analysis_dataset(args.input, args.output)
    elif args.task == 'zinb':
        result = run_zinb_analysis(args.input)
        print(json.dumps(result, indent=2))
    elif args.task == 'stratified':
        run_stratified_analysis(args.input, args.output)
    elif args.task == 'fpr':
        if not args.validator:
            parser.error("--validator is required for FPR calculation")
        calculate_fpr_metrics(args.validator, args.output)

if __name__ == '__main__':
    main()
