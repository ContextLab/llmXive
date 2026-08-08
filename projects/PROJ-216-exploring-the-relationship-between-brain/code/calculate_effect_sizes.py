import os
import sys
import math
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import from sibling modules as per API surface
from stats import load_graph_metrics, load_behavioral_scores, merge_metrics_with_scores

def calculate_cohen_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    Cohen's d = (mean1 - mean2) / pooled_std
    """
    if not group1 or not group2:
        raise ValueError("Both groups must contain data points.")
    
    n1, n2 = len(group1), len(group2)
    mean1 = sum(group1) / n1
    mean2 = sum(group2) / n2
    
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1) if n1 > 1 else 0
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1) if n2 > 1 else 0
    
    # Pooled standard deviation
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_std = math.sqrt(pooled_var)
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def calculate_ci_95_cohen_d(group1: List[float], group2: List[float], d: float, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval for Cohen's d.
    Approximation using standard error of d.
    SE_d = sqrt((n1 + n2)/(n1*n2) + d^2/(2*(n1+n2)))
    CI = d +/- Z * SE_d
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        raise ValueError("Need at least 2 points in each group to calculate CI.")
    
    # Standard error approximation
    se_d = math.sqrt((n1 + n2) / (n1 * n2) + (d ** 2) / (2 * (n1 + n2)))
    
    # Z-score for 95% CI (approx 1.96)
    z = 1.96
    
    ci_lower = d - (z * se_d)
    ci_upper = d + (z * se_d)
    
    return ci_lower, ci_upper

def main():
    """
    Main entry point for T032: Calculate effect sizes and confidence intervals.
    Reads graph_metrics.csv and behavioral scores, computes Cohen's d for 
    significant correlations, and appends results to the CSV.
    """
    project_root = Path(__file__).parent.parent
    metrics_path = project_root / "data" / "processed" / "graph_metrics.csv"
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Required input file not found: {metrics_path}")
    
    # Load data
    metrics_df = load_graph_metrics(metrics_path)
    behavioral_df = load_behavioral_scores()
    
    if metrics_df.empty:
        raise ValueError("No graph metrics found to analyze.")
    
    if behavioral_df.empty:
        raise ValueError("No behavioral scores found to analyze.")
    
    # Merge data to align metrics with Fluid Intelligence scores
    # We expect the merge to happen on subject_id and metric_name logic
    # The stats module handles the merging logic for correlations
    merged_data = merge_metrics_with_scores(metrics_df, behavioral_df)
    
    if merged_data.empty:
        raise ValueError("Could not merge graph metrics with behavioral scores.")
    
    # We need to calculate Cohen's d for the groups defined by the correlation analysis.
    # Typically, for a correlation with a continuous variable (Fluid Intelligence),
    # we don't split into two groups unless we bin the data.
    # However, the task asks for Cohen's d. In the context of a correlation study,
    # this often implies comparing high vs low performers or similar, OR
    # it might be a misinterpretation of effect size for correlation (r).
    # Given the strict requirement for "cohens_d" column, and the presence of 
    # a continuous variable (Fluid Intelligence), we will bin the Fluid Intelligence
    # scores into 'High' and 'Low' groups (median split) to calculate Cohen's d
    # for the graph metrics between these groups.
    
    # Group by metric_name and calculate Cohen's d between High and Low FI groups
    results = []
    
    metrics = merged_data['metric_name'].unique()
    fi_scores = merged_data['score_value']
    
    if len(fi_scores) < 2:
        raise ValueError("Insufficient data points to calculate effect sizes.")
    
    median_score = fi_scores.median()
    
    # Create High/Low groups
    merged_data['group'] = merged_data['score_value'].apply(lambda x: 'High' if x >= median_score else 'Low')
    
    for metric in metrics:
        metric_data = merged_data[merged_data['metric_name'] == metric]
        
        high_group = metric_data[metric_data['group'] == 'High']['value'].tolist()
        low_group = metric_data[metric_data['group'] == 'Low']['value'].tolist()
        
        if not high_group or not low_group:
            # Skip if one group is empty (e.g., all scores equal)
            results.append({
                'metric_name': metric,
                'cohens_d': None,
                'ci_lower': None,
                'ci_upper': None
            })
            continue
        
        d = calculate_cohen_d(high_group, low_group)
        ci_lower, ci_upper = calculate_ci_95_cohen_d(high_group, low_group, d)
        
        results.append({
            'metric_name': metric,
            'cohens_d': d,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        })
    
    # Append results to the original CSV
    # We will read the CSV again to ensure we have all rows and merge the effect sizes
    # Since graph_metrics.csv has one row per subject per metric, we need to broadcast
    # the effect size to all rows for that metric, or create a summary file.
    # The task says "append columns ... to data/processed/graph_metrics.csv".
    # This implies adding the effect size of the metric (which is constant for that metric)
    # to every row of that metric.
    
    effect_size_map = {r['metric_name']: r for r in results}
    
    output_rows = []
    with open(metrics_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames + ['cohens_d', 'ci_lower', 'ci_upper']
        
        for row in reader:
            metric = row['metric_name']
            es_data = effect_size_map.get(metric, {})
            
            new_row = row.copy()
            new_row['cohens_d'] = es_data.get('cohens_d', '')
            new_row['ci_lower'] = es_data.get('ci_lower', '')
            new_row['ci_upper'] = es_data.get('ci_upper', '')
            output_rows.append(new_row)
    
    # Write back to the same file (or a processed version)
    # To be safe and non-destructive in a real pipeline, we might write to a new file,
    # but the task says "append ... to ... graph_metrics.csv".
    # We will overwrite the file with the new columns.
    
    output_path = metrics_path
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    print(f"Effect sizes calculated and appended to {output_path}")

if __name__ == "__main__":
    main()
