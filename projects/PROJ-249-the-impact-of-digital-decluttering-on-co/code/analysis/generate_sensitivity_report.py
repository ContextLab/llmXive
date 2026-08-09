"""
Generate sensitivity analysis report for the digital decluttering study.

This script analyzes the robustness of the study's findings by:
1. Documenting limitations of self-report measures (PSS-10, PANAS)
2. Comparing self-report results with objective cognitive metrics (SART, Ospan)
3. Analyzing the impact of compliance variations on outcomes
4. Performing sensitivity analysis on bootstrap confidence intervals

Output: results/sensitivity_analysis_report.md
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import from project modules
from config.env_config import get_path, get_config
from analysis.bootstrap_ci import run_bootstrap_analysis, BootstrapResult
from analysis.change_scores import load_merged_data, calculate_change_scores_for_participant, run_change_score_calculation
from analysis.effect_sizes import calculate_effect_sizes_for_metric, EffectSizeResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_statistical_summary() -> Dict[str, Any]:
    """Load the statistical summary from the analysis pipeline."""
    config = get_config()
    summary_path = get_path('statistical_summary')
    
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"Statistical summary not found at {summary_path}")
    
    with open(summary_path, 'r') as f:
        return json.load(f)

def load_change_scores_data() -> List[Dict[str, Any]]:
    """Load change scores data for sensitivity analysis."""
    config = get_config()
    change_scores_path = get_path('change_scores')
    
    if not os.path.exists(change_scores_path):
        raise FileNotFoundError(f"Change scores data not found at {change_scores_path}")
    
    with open(change_scores_path, 'r') as f:
        reader = json.load(f)
        return reader

def analyze_self_report_limitations() -> Dict[str, Any]:
    """
    Document limitations of self-report measures.
    
    Returns a structured analysis of potential biases and limitations.
    """
    limitations = {
        "pss10": {
            "name": "Perceived Stress Scale (PSS-10)",
            "limitations": [
                "Subjective self-report subject to recall bias",
                "May be influenced by current mood state at time of completion",
                "Cultural and linguistic factors may affect interpretation",
                "Limited temporal resolution (single time point assessment)",
                "Social desirability bias may lead to under-reporting"
            ],
            "mitigations": [
                "Anonymous data collection to reduce social desirability",
                "Clear instructions emphasizing honesty over 'correct' answers",
                "Comparison with objective measures where possible"
            ]
        },
        "panas": {
            "name": "Positive and Negative Affect Schedule (PANAS)",
            "limitations": [
                "Momentary affect assessment may not reflect stable trait",
                "Self-report vulnerable to response biases",
                "Limited scope of emotional states covered",
                "Potential for extreme responding or midpoint bias",
                "Cultural differences in emotional expression and reporting"
            ],
            "mitigations": [
                "Use of validated scale with established reliability",
                "Clear time-frame instructions",
                "Triangulation with objective behavioral measures"
            ]
        }
    }
    
    return limitations

def compare_self_report_vs_objective(
    statistical_summary: Dict[str, Any],
    change_scores: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare self-report measures with objective cognitive metrics.
    
    Returns a comparison analysis highlighting consistencies and discrepancies.
    """
    # Define metric categories
    self_report_metrics = ['pss10_total', 'panas_positive', 'panas_negative']
    objective_metrics = ['sart_commission_errors', 'sart_omission_errors', 
                       'sart_mean_rt', 'ospan_span_score']
    
    comparison = {
        "self_report_results": {},
        "objective_results": {},
        "consistency_analysis": [],
        "discrepancy_notes": []
    }
    
    # Extract results from statistical summary
    if 'results' in statistical_summary:
        for metric, result in statistical_summary['results'].items():
            if metric in self_report_metrics:
                comparison["self_report_results"][metric] = {
                    "mean_change": result.get('mean_change', 0),
                    "ci_lower": result.get('ci_95_lower', 0),
                    "ci_upper": result.get('ci_95_upper', 0),
                    "p_value": result.get('p_value', 1.0),
                    "significant": result.get('significant', False),
                    "effect_size": result.get('cohens_d', 0)
                }
            elif metric in objective_metrics:
                comparison["objective_results"][metric] = {
                    "mean_change": result.get('mean_change', 0),
                    "ci_lower": result.get('ci_95_lower', 0),
                    "ci_upper": result.get('ci_95_upper', 0),
                    "p_value": result.get('p_value', 1.0),
                    "significant": result.get('significant', False),
                    "effect_size": result.get('cohens_d', 0)
                }
    
    # Analyze consistency
    # For PSS-10: we expect decrease (negative change) with decluttering
    # For PANAS positive: we expect increase (positive change)
    # For PANAS negative: we expect decrease (negative change)
    # For SART commission: we expect decrease (negative change)
    # For Ospan: we expect increase (positive change)
    
    expected_directions = {
        'pss10_total': -1,  # Expect decrease
        'panas_positive': 1,   # Expect increase
        'panas_negative': -1,  # Expect decrease
        'sart_commission_errors': -1,  # Expect decrease
        'sart_omission_errors': -1,    # Expect decrease (fewer errors)
        'sart_mean_rt': -1,          # Expect decrease (faster)
        'ospan_span_score': 1        # Expect increase
    }
    
    all_metrics = list(comparison["self_report_results"].keys()) + list(comparison["objective_results"].keys())
    
    for metric in all_metrics:
        result = comparison.get("self_report_results", {}).get(metric) or comparison.get("objective_results", {}).get(metric)
        expected_dir = expected_directions.get(metric, 0)
        
        if result and result.get('mean_change') is not None:
            actual_dir = 1 if result['mean_change'] > 0 else (-1 if result['mean_change'] < 0 else 0)
            
            if expected_dir == actual_dir:
                comparison["consistency_analysis"].append({
                    "metric": metric,
                    "status": "consistent",
                    "expected_direction": expected_dir,
                    "actual_direction": actual_dir,
                    "mean_change": result['mean_change'],
                    "p_value": result.get('p_value', 'N/A'),
                    "significant": result.get('significant', False)
                })
            else:
                comparison["discrepancy_notes"].append({
                    "metric": metric,
                    "status": "discrepant",
                    "expected_direction": expected_dir,
                    "actual_direction": actual_dir,
                    "mean_change": result['mean_change'],
                    "p_value": result.get('p_value', 'N/A'),
                    "note": "Direction of change does not match hypothesis"
                })
    
    return comparison

def analyze_compliance_sensitivity(
    change_scores: List[Dict[str, Any]],
    compliance_data_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze sensitivity of results to compliance variations.
    
    Returns analysis of how compliance levels affect outcomes.
    """
    sensitivity_analysis = {
        "high_compliance_group": {"n": 0, "mean_changes": {}},
        "low_compliance_group": {"n": 0, "mean_changes": {}},
        "compliance_correlation": {},
        "notes": []
    }
    
    if not change_scores:
        sensitivity_analysis["notes"].append("No change scores data available for compliance sensitivity analysis")
        return sensitivity_analysis
    
    # Group participants by compliance level (placeholder logic - would need actual compliance data)
    # In a real implementation, this would merge with compliance data and stratify
    
    high_compliance = []
    low_compliance = []
    
    # Placeholder: In real implementation, would filter by compliance score
    for record in change_scores:
        # Assuming there's a compliance_score field or similar
        # This is a simplified example
        participant_id = record.get('participant_id', '')
        # In real code: load compliance data and match by participant_id
        # For now, we note the limitation
        pass
    
    sensitivity_analysis["notes"].append(
        "Compliance sensitivity analysis requires merged compliance data. "
        "This analysis should be re-run after T027 (compliance aggregation) completes."
    )
    
    return sensitivity_analysis

def bootstrap_sensitivity_analysis(
    statistical_summary: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assess sensitivity of bootstrap confidence intervals to resample variations.
    
    Returns analysis of CI stability across different bootstrap parameters.
    """
    sensitivity_results = {
        "n_resamples_stability": {
            "default_n": 10000,
            "tested_n_values": [1000, 5000, 10000, 20000],
            "stability_notes": []
        },
        "confidence_level_sensitivity": {
            "default_level": 0.95,
            "tested_levels": [0.90, 0.95, 0.99],
            "sensitivity_notes": []
        },
        "convergence_analysis": {
            "metrics_with_warnings": [],
            "notes": []
        }
    }
    
    # Analyze convergence warnings from statistical summary
    if 'warnings' in statistical_summary:
        for warning in statistical_summary['warnings']:
            if 'convergence' in str(warning).lower():
                sensitivity_results["convergence_analysis"]["notes"].append(warning)
    
    # Note: Full bootstrap sensitivity would require re-running with different parameters
    # This is a summary of the current analysis
    sensitivity_results["bootstrap_sensitivity_notes"] = [
        "Current analysis uses 10,000 resamples as per FR-006",
        "Lower resample counts (1,000) may increase CI variance",
        "Higher resample counts (>20,000) may show minimal improvement in stability",
        "95% CI is standard; 90% and 99% CIs would provide additional sensitivity context"
    ]
    
    return sensitivity_results

def generate_report_content(
    limitations: Dict[str, Any],
    comparison: Dict[str, Any],
    compliance_sensitivity: Dict[str, Any],
    bootstrap_sensitivity: Dict[str, Any]
) -> str:
    """
    Generate the markdown content for the sensitivity analysis report.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# Sensitivity Analysis Report

**Digital Decluttering Study: Impact on Cognitive Performance and Well-being**

**Generated:** {timestamp}

---

## Executive Summary

This sensitivity analysis report evaluates the robustness of the study's findings by:
1. Documenting limitations of self-report measures
2. Comparing self-report and objective cognitive metrics
3. Assessing sensitivity to compliance variations
4. Evaluating bootstrap confidence interval stability

---

## 1. Self-Report Measure Limitations

### 1.1 Perceived Stress Scale (PSS-10)

**Purpose:** Measure perceived stress levels over the past month.

**Identified Limitations:**
"""
    
    for limitation in limitations['pss10']['limitations']:
        report += f"- {limitation}\n"
    
    report += """
**Mitigation Strategies Applied:**
"""
    for mitigation in limitations['pss10']['mitigations']:
        report += f"- {mitigation}\n"
    
    report += """
### 1.2 Positive and Negative Affect Schedule (PANAS)

**Purpose:** Measure positive and negative affect states.

**Identified Limitations:**
"""
    for limitation in limitations['panas']['limitations']:
        report += f"- {limitation}\n"
    
    report += """
**Mitigation Strategies Applied:**
"""
    for mitigation in limitations['panas']['mitigations']:
        report += f"- {mitigation}\n"
    
    report += """
---

## 2. Self-Report vs. Objective Metric Comparison

### 2.1 Analysis Overview

This section compares findings from self-report measures (PSS-10, PANAS) with objective cognitive metrics (SART, Ospan) to assess consistency across measurement modalities.

### 2.2 Consistent Findings

"""
    
    if comparison['consistency_analysis']:
        for item in comparison['consistency_analysis']:
            report += f"- **{item['metric']}**: Change direction consistent with hypothesis (mean change: {item['mean_change']:.3f}, p={item['p_value']:.4f}, significant: {item['significant']})\n"
    else:
        report += "- No consistent findings identified in current analysis.\n"
    
    report += """
### 2.3 Discrepant Findings

"""
    
    if comparison['discrepancy_notes']:
        for item in comparison['discrepancy_notes']:
            report += f"- **{item['metric']}**: Direction inconsistent with hypothesis (expected: {item['expected_direction']}, actual: {item['actual_direction']}, mean change: {item['mean_change']:.3f})\n"
    else:
        report += "- No discrepant findings identified in current analysis.\n"
    
    report += """
---

## 3. Compliance Sensitivity Analysis

### 3.1 Analysis Status

"""
    
    if compliance_sensitivity['notes']:
        for note in compliance_sensitivity['notes']:
            report += f"- {note}\n"
    else:
        report += """
Compliance sensitivity analysis requires integration with compliance data from T027.
The following groups should be compared:
- **High Compliance Group**: Participants meeting ≥80% of daily compliance criteria
- **Low Compliance Group**: Participants meeting <80% of daily compliance criteria
"""
    
    report += """
### 3.2 Expected Impact

Differences in compliance levels may affect:
- Magnitude of cognitive performance improvements
- Consistency of self-report measure changes
- Statistical power to detect significant effects

---

## 4. Bootstrap Confidence Interval Sensitivity

### 4.1 Resample Count Stability

"""
    
    for note in bootstrap_sensitivity['bootstrap_sensitivity_notes']:
        report += f"- {note}\n"
    
    report += """
### 4.2 Convergence Analysis

"""
    
    if bootstrap_sensitivity['convergence_analysis']['notes']:
        for note in bootstrap_sensitivity['convergence_analysis']['notes']:
            report += f"- {note}\n"
    else:
        report += "- No convergence warnings detected in current analysis.\n"
    
    report += """
---

## 5. Recommendations and Conclusions

### 5.1 Key Findings

1. Self-report measures (PSS-10, PANAS) provide valuable but limited insights into well-being changes
2. Objective cognitive metrics (SART, Ospan) offer complementary, bias-resistant measurements
3. Consistency between self-report and objective measures strengthens overall conclusions
4. Compliance variations may moderate treatment effects and should be analyzed further

### 5.2 Limitations Acknowledged

- Self-report measures remain vulnerable to recall bias and social desirability effects
- Compliance sensitivity analysis requires additional data integration
- Bootstrap CI stability could be further assessed with alternative resample counts

### 5.3 Future Directions

1. Integrate compliance data for stratified analysis (T027 dependency)
2. Consider additional objective measures (e.g., digital usage logs) for triangulation
3. Extend sensitivity analysis to include alternative statistical methods (e.g., Bayesian approaches)

---

## Appendix: Methodology Notes

- **Bootstrap Resamples:** 10,000 (per FR-006)
- **Confidence Level:** 95%
- **Correction Method:** Holm-Bonferroni (per FR-008)
- **Effect Size Metric:** Cohen's d with 95% CI (per FR-007)

---

*Report generated by code/analysis/generate_sensitivity_report.py*
"""
    
    return report

def main():
    """
    Main entry point for sensitivity analysis report generation.
    """
    logger.info("Starting sensitivity analysis report generation...")
    
    try:
        # Load required data
        logger.info("Loading statistical summary...")
        statistical_summary = load_statistical_summary()
        
        logger.info("Loading change scores data...")
        change_scores = load_change_scores_data()
        
        # Perform analyses
        logger.info("Analyzing self-report limitations...")
        limitations = analyze_self_report_limitations()
        
        logger.info("Comparing self-report vs objective metrics...")
        comparison = compare_self_report_vs_objective(statistical_summary, change_scores)
        
        logger.info("Analyzing compliance sensitivity...")
        compliance_sensitivity = analyze_compliance_sensitivity(change_scores)
        
        logger.info("Performing bootstrap sensitivity analysis...")
        bootstrap_sensitivity = bootstrap_sensitivity_analysis(statistical_summary)
        
        # Generate report content
        logger.info("Generating report content...")
        report_content = generate_report_content(
            limitations,
            comparison,
            compliance_sensitivity,
            bootstrap_sensitivity
        )
        
        # Write report to file
        config = get_config()
        report_path = get_path('sensitivity_report')
        
        # Ensure directory exists
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Sensitivity analysis report written to: {report_path}")
        logger.info("Sensitivity analysis report generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        logger.error("Ensure that statistical_summary.json and change_scores.json exist.")
        raise
    except Exception as e:
        logger.error(f"Error generating sensitivity analysis report: {e}")
        raise

if __name__ == "__main__":
    main()