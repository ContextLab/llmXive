import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt

def load_analysis_results(file_path: Path) -> Dict[str, Any]:
    """Load analysis results from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def load_effect_sizes_for_plotting(file_path: Path) -> List[Dict[str, Any]]:
    """Load effect sizes for plotting from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'studies' in data:
        return data['studies']
    return []

def create_forest_plot(studies: List[Dict[str, Any]], summary: Dict[str, float], output_path: Path) -> None:
    """Create a forest plot."""
    fig, ax = plt.subplots(figsize=(10, 6 + len(studies) * 0.3))
    
    effects = []
    cis = []
    
    for i, study in enumerate(studies):
        r = study.get('r', 0)
        n = study.get('n', 0)
        study_id = study.get('study_id', f'Study {i+1}')
        
        if n <= 2:
            continue
        
        # Fisher's z transformation
        z = 0.5 * math.log((1 + r) / (1 - r))
        se = 1 / math.sqrt(n - 3)
        
        effects.append(z)
        cis.append((z - 1.96 * se, z + 1.96 * se))
    
    if not effects:
        ax.text(0.5, 0.5, 'No studies to plot', transform=ax.transAxes, ha='center')
        plt.savefig(output_path, dpi=150, optimize=True)
        plt.close()
        return
    
    # Plot individual studies
    for i, (z, ci) in enumerate(zip(effects, cis)):
        ax.errorbar(z, [i], xerr=[[z - ci[0]], [ci[1] - z]], fmt='o', capsize=3, label=study_id if i == 0 else "")
    
    # Plot summary diamond
    summary_z = 0.5 * math.log((1 + summary.get('weighted_mean_r', 0)) / (1 - summary.get('weighted_mean_r', 0)))
    ci_lower = summary.get('ci_lower', 0)
    ci_upper = summary.get('ci_upper', 0)
    
    summary_ci_lower = 0.5 * math.log((1 + ci_lower) / (1 - ci_lower))
    summary_ci_upper = 0.5 * math.log((1 + ci_upper) / (1 - ci_upper))
    
    ax.plot([summary_z], [len(effects)], 'D', markersize=10, color='red', label='Summary')
    ax.vlines(summary_z, len(effects) - 0.2, len(effects) + 0.2, color='red', linewidth=2)
    
    # Vertical line at zero
    ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_xlabel('Fisher\'s z (effect size)')
    ax.set_ylabel('Study')
    ax.set_title('Forest Plot: Brain Connectivity and Music Preferences')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, optimize=True)
    plt.close()

def create_funnel_plot(studies: List[Dict[str, Any]], summary: Dict[str, float], output_path: Path) -> None:
    """Create a funnel plot."""
    fig, ax = plt.subplots(figsize=(8, 8))
    
    effects = []
    ses = []
    
    for study in studies:
        r = study.get('r', 0)
        n = study.get('n', 0)
        
        if n <= 2:
            continue
        
        z = 0.5 * math.log((1 + r) / (1 - r))
        se = 1 / math.sqrt(n - 3)
        
        effects.append(z)
        ses.append(se)
    
    if not effects:
        ax.text(0.5, 0.5, 'No studies to plot', transform=ax.transAxes, ha='center')
        plt.savefig(output_path, dpi=150, optimize=True)
        plt.close()
        return
    
    # Plot studies
    ax.scatter(ses, effects, alpha=0.6, label='Studies')
    
    # Plot pseudo 95% confidence limits
    summary_z = 0.5 * math.log((1 + summary.get('weighted_mean_r', 0)) / (1 - summary.get('weighted_mean_r', 0)))
    max_se = max(ses)
    
    se_range = [i * 0.01 for i in range(int(max_se * 100) + 1)]
    upper = [summary_z + 1.96 * se for se in se_range]
    lower = [summary_z - 1.96 * se for se in se_range]
    
    ax.plot(upper, se_range, 'r--', alpha=0.5, label='95% CI')
    ax.plot(lower, se_range, 'r--', alpha=0.5)
    
    # Vertical line at summary effect
    ax.axvline(x=summary_z, color='gray', linestyle='-', alpha=0.5)
    
    ax.set_xlabel('Standard Error')
    ax.set_ylabel('Fisher\'s z (effect size)')
    ax.set_title('Funnel Plot: Publication Bias Assessment')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, optimize=True)
    plt.close()

def create_correlation_summary_plot(studies: List[Dict[str, Any]], output_path: Path) -> None:
    """Create a correlation summary plot."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    tracts = {}
    for study in studies:
        tract = study.get('tract', 'Unknown')
        r = study.get('r', 0)
        
        if tract not in tracts:
            tracts[tract] = []
        tracts[tract].append(r)
    
    tract_names = list(tracts.keys())
    mean_r = [sum(vals) / len(vals) for vals in tracts.values()]
    
    ax.bar(tract_names, mean_r, alpha=0.7)
    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    
    ax.set_xlabel('Tract')
    ax.set_ylabel('Mean Correlation (r)')
    ax.set_title('Correlation Summary by Tract')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, optimize=True)
    plt.close()

def run_visualization_analysis(results_path: Path, output_dir: Path) -> None:
    """Run all visualization analyses."""
    results = load_analysis_results(results_path)
    
    # Load studies for plotting
    studies_path = output_dir.parent / "studies_for_analysis.json"
    if studies_path.exists():
        studies = load_effect_sizes_for_plotting(studies_path)
    else:
        studies = []
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Forest plot
    forest_path = output_dir / "forest_plot.png"
    create_forest_plot(studies, results.get('meta_analysis', {}), forest_path)
    
    # Funnel plot
    funnel_path = output_dir / "funnel_plot.png"
    create_funnel_plot(studies, results.get('meta_analysis', {}), funnel_path)
    
    # Correlation summary plot
    corr_path = output_dir / "correlation_summary.png"
    create_correlation_summary_plot(studies, corr_path)

def main() -> None:
    """Main entry point for visualization."""
    import argparse
    parser = argparse.ArgumentParser(description="Visualization tool")
    parser.add_argument("--results", type=str, required=True, help="Results JSON file")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    args = parser.parse_args()
    
    run_visualization_analysis(Path(args.results), Path(args.output))
    print(f"Visualization complete. Plots saved to {args.output}")

if __name__ == "__main__":
    main()