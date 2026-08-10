"""
Report generation module for User Story 3.

Implements T035: Generate final statistical results JSON and analysis report.md.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, info, error, warning
from utils.config import get_artifacts_dir

logger = get_logger(__name__)


def load_json_artifact(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON artifact file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        warning(f"Failed to load {path}: {str(e)}")
        return None


def generate_final_report(
    anova_results_path: Optional[str] = None,
    correlation_results_path: Optional[str] = None,
    human_eval_results_path: Optional[str] = None,
    wikitext2_results_path: Optional[str] = None,
    power_analysis_results_path: Optional[str] = None,
    output_json_path: Optional[str] = None,
    output_md_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate final statistical results JSON and analysis report.
    
    Implements T035: Output statistical_results.json and analysis/report.md
    with explicit pass/fail logic for SC-002 (|r| >= 0.5).
    
    Args:
        anova_results_path: Path to ANOVA results
        correlation_results_path: Path to correlation results
        human_eval_results_path: Path to HumanEval results
        wikitext2_results_path: Path to WikiText-2 results
        power_analysis_results_path: Path to power analysis results
        output_json_path: Path to save final JSON results
        output_md_path: Path to save markdown report
        
    Returns:
        Dictionary containing the final report data
    """
    logger.info("Generating final analysis report")
    
    # Load all results
    anova_results = load_json_artifact(
        anova_results_path or str(get_artifacts_dir() / "statistical_results.json")
    )
    correlation_results = load_json_artifact(
        correlation_results_path or str(get_artifacts_dir() / "correlation_results.json")
    )
    human_eval_results = load_json_artifact(
        human_eval_results_path or str(get_artifacts_dir() / "human_eval_results.json")
    )
    wikitext2_results = load_json_artifact(
        wikitext2_results_path or str(get_artifacts_dir() / "wikitext2_results.json")
    )
    power_results = load_json_artifact(
        power_analysis_results_path or str(get_artifacts_dir() / "power_analysis_results.json")
    )
    
    # Compile final results
    final_results = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "pipeline_version": "1.0.0",
            "user_story": "US3 - Analyze Overfitting Trajectories"
        },
        "statistical_analysis": anova_results,
        "correlation_analysis": correlation_results,
        "benchmark_results": {
            "human_eval": human_eval_results,
            "wikitext2": wikitext2_results
        },
        "power_analysis": power_results,
        "success_criteria": {
            "sc_002_correlation": {
                "description": "Pearson correlation |r| >= 0.5 between gap slope and HumanEval score",
                "threshold": 0.5,
                "observed_r": correlation_results.get("r") if correlation_results else None,
                "threshold_met": correlation_results.get("threshold_met", False) if correlation_results else False
            },
            "sc_003_power": {
                "description": "Statistical power >= 0.8",
                "threshold": 0.8,
                "observed_power": power_results.get("results", {}).get("anova_power") if power_results else None,
                "threshold_met": power_results.get("interpretation", {}).get("sufficient_power", False) if power_results else False
            },
            "sc_004_exclusion": {
                "description": "HumanEval exclusion from Micro-Corpus verified",
                "threshold_met": human_eval_results.get("exclusion_verification", {}).get("exclusion_verified", False) if human_eval_results else False
            }
        },
        "overall_summary": {
            "all_criteria_met": False,
            "criteria_passed": [],
            "criteria_failed": []
        }
    }
    
    # Evaluate success criteria
    criteria = final_results["success_criteria"]
    for name, criterion in criteria.items():
        if criterion["threshold_met"]:
            final_results["overall_summary"]["criteria_passed"].append(name)
        else:
            final_results["overall_summary"]["criteria_failed"].append(name)
    
    final_results["overall_summary"]["all_criteria_met"] = (
        len(final_results["overall_summary"]["criteria_failed"]) == 0
    )
    
    # Save JSON results
    if output_json_path is None:
        output_json_path = str(get_artifacts_dir() / "statistical_results.json")
    
    output_json_path = Path(output_json_path)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_json_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    info(f"Final statistical results saved to {output_json_path}")
    
    # Generate markdown report
    md_report = generate_markdown_report(final_results)
    
    if output_md_path is None:
        output_md_path = str(get_artifacts_dir().parent / "analysis" / "report.md")
    
    output_md_path = Path(output_md_path)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_md_path, 'w') as f:
        f.write(md_report)
    
    info(f"Markdown report saved to {output_md_path}")
    
    return final_results


def generate_markdown_report(results: Dict[str, Any]) -> str:
    """
    Generate a markdown report from the results dictionary.
    
    Args:
        results: Final results dictionary
        
    Returns:
        Markdown formatted report string
    """
    report_lines = [
        "# llmXive Analysis Report: Overfitting Trajectories",
        "",
        f"**Generated:** {results['report_metadata']['generated_at']}",
        f"**Pipeline Version:** {results['report_metadata']['pipeline_version']}",
        "",
        "## Executive Summary",
        "",
        f"**All Success Criteria Met:** {'✅ Yes' if results['overall_summary']['all_criteria_met'] else '❌ No'}",
        "",
        "### Criteria Status",
        ""
    ]
    
    # Success criteria table
    report_lines.append("| Criterion | Status | Details |")
    report_lines.append("|-----------|--------|---------|")
    
    for name, criterion in results['success_criteria'].items():
        status = "✅ PASS" if criterion['threshold_met'] else "❌ FAIL"
        details = f"Observed: {criterion.get('observed_r', criterion.get('observed_power', 'N/A'))}"
        report_lines.append(f"| {name.replace('_', ' ').title()} | {status} | {details} |")
    
    report_lines.extend([
        "",
        "## Statistical Analysis (ANOVA)",
        ""
    ])
    
    if results.get('statistical_analysis'):
        stat = results['statistical_analysis']
        report_lines.extend([
            f"**Method:** {stat.get('method', 'N/A')}",
            f"**Sample Size:** {stat.get('sample_size', 'N/A')} records",
            f"**Subjects:** {stat.get('num_subjects', 'N/A')}",
            f"**Interaction Significant:** {'Yes' if stat.get('interaction_significant') else 'No'}",
            ""
        ])
        
        if stat.get('summary'):
            summary = stat['summary']
            report_lines.append("### Effect Summary")
            report_lines.append("")
            report_lines.append("| Effect | F-Statistic | p-value |")
            report_lines.append("|--------|-------------|---------|")
            
            for effect_name, effect_data in summary.items():
                f_stat = effect_data.get('f_statistic', 'N/A')
                p_val = effect_data.get('p_value', 'N/A')
                report_lines.append(f"| {effect_name.replace('_', ' ').title()} | {f_stat} | {p_val} |")
    
    report_lines.extend([
        "",
        "## Correlation Analysis",
        ""
    ])
    
    if results.get('correlation_analysis'):
        corr = results['correlation_analysis']
        r_val = corr.get('r', 'N/A')
        threshold_met = "✅ Yes" if corr.get('threshold_met') else "❌ No"
        
        report_lines.extend([
            f"**Correlation Coefficient (r):** {r_val}",
            f"**SC-002 Threshold Met (|r| >= 0.5):** {threshold_met}",
            f"**Data Points:** {corr.get('data_points', 'N/A')}",
            f"**Early Window:** {corr.get('early_window_epochs', 'N/A')} epochs"
        ])
    
    report_lines.extend([
        "",
        "## Benchmark Results",
        "",
        "### HumanEval",
        ""
    ])
    
    if results.get('benchmark_results', {}).get('human_eval'):
        he = results['benchmark_results']['human_eval']
        exclusion = he.get('exclusion_verification', {})
        report_lines.extend([
            f"**Exclusion Verified:** {'✅ Yes' if exclusion.get('exclusion_verified') else '❌ No'}",
            f"**HumanEval Samples:** {exclusion.get('humaneval_count', 'N/A')}",
            f"**Corpus Samples Checked:** {exclusion.get('corpus_count', 'N/A')}",
            f"**Matches Found:** {exclusion.get('matches_found', 'N/A')}"
        ])
    
    report_lines.extend([
        "",
        "### WikiText-2 Cross-Domain Validation",
        ""
    ])
    
    if results.get('benchmark_results', {}).get('wikitext2'):
        wt2 = results['benchmark_results']['wikitext2']
        model_results = wt2.get('model_results', [])
        
        if model_results:
            report_lines.append("| Model Checkpoint | Validation PPL | Test PPL |")
            report_lines.append("|------------------|----------------|----------|")
            
            for mr in model_results:
                if mr.get('status') == 'evaluated':
                    report_lines.append(
                        f"| {mr.get('checkpoint', 'N/A')} | "
                        f"{mr.get('validation_perplexity', 'N/A')} | "
                        f"{mr.get('test_perplexity', 'N/A')} |"
                    )
        else:
            report_lines.append("No model evaluations available.")
    
    report_lines.extend([
        "",
        "## Power Analysis",
        ""
    ])
    
    if results.get('power_analysis'):
        power = results['power_analysis']
        info_section = power.get('results', {})
        interp = power.get('interpretation', {})
        
        report_lines.extend([
            f"**ANOVA Power:** {info_section.get('anova_power', 'N/A')}",
            f"**Power Threshold Met (>=0.8):** {'✅ Yes' if interp.get('sufficient_power') else '❌ No'}",
            f"**Design:** {power.get('design', {}).get('n_groups', 'N/A')} groups x {power.get('design', {}).get('n_per_group', 'N/A')} seeds"
        ])
    
    report_lines.extend([
        "",
        "## Conclusions",
        "",
        "This report summarizes the statistical analysis of overfitting trajectories",
        "comparing autoregressive and diffusion language models trained on the",
        "llmXive Micro-Corpus.",
        "",
        f"**Overall Result:** {'All success criteria met.' if results['overall_summary']['all_criteria_met'] else 'Some success criteria not met.'}",
        ""
    ])
    
    if results['overall_summary']['criteria_passed']:
        report_lines.append("### Passed Criteria")
        for criterion in results['overall_summary']['criteria_passed']:
            report_lines.append(f"- ✅ {criterion.replace('_', ' ').title()}")
        report_lines.append("")
    
    if results['overall_summary']['criteria_failed']:
        report_lines.append("### Failed Criteria")
        for criterion in results['overall_summary']['criteria_failed']:
            report_lines.append(f"- ❌ {criterion.replace('_', ' ').title()}")
        report_lines.append("")
    
    report_lines.extend([
        "---",
        "",
        "*Report generated by llmXive Analysis Pipeline*"
    ])
    
    return "\n".join(report_lines)


def main():
    """Main entry point for report generation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate final analysis report")
    parser.add_argument("--anova", type=str, help="Path to ANOVA results")
    parser.add_argument("--correlation", type=str, help="Path to correlation results")
    parser.add_argument("--human-eval", type=str, help="Path to HumanEval results")
    parser.add_argument("--wikitext2", type=str, help="Path to WikiText-2 results")
    parser.add_argument("--power", type=str, help="Path to power analysis results")
    parser.add_argument("--output-json", type=str, help="Path to output JSON file")
    parser.add_argument("--output-md", type=str, help="Path to output markdown file")
    
    args = parser.parse_args()
    
    try:
        results = generate_final_report(
            anova_results_path=args.anova,
            correlation_results_path=args.correlation,
            human_eval_results_path=args.human_eval,
            wikitext2_results_path=args.wikitext2,
            power_analysis_results_path=args.power,
            output_json_path=args.output_json,
            output_md_path=args.output_md
        )
        
        info("Report generation completed")
        info(f"All criteria met: {results['overall_summary']['all_criteria_met']}")
        
    except Exception as e:
        error(f"Report generation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()