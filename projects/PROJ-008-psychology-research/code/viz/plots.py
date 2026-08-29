import logging
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from code.utils.logging import get_logger
from code.utils.config import get_data_path

logger = get_logger(__name__)

def create_forest_plot(
    effect_sizes: List[float],
    standard_errors: List[float],
    study_labels: List[str],
    pooled_effect: Optional[float] = None,
    pooled_se: Optional[float] = None,
    output_path: Optional[str] = None
) -> None:
    """
    Create a forest plot displaying study-specific effect sizes and confidence intervals.
    
    Args:
        effect_sizes: List of effect sizes (e.g., Hedges' g).
        standard_errors: List of standard errors.
        study_labels: List of study labels (e.g., "Author (Year)").
        pooled_effect: Optional pooled effect size for the summary diamond.
        pooled_se: Optional standard error of the pooled effect.
        output_path: Optional path to save the plot.
    """
    n = len(effect_sizes)
    if n == 0:
        logger.warning("No effect sizes provided for forest plot.")
        return
        
    fig, ax = plt.subplots(figsize=(10, 6 + n * 0.3))
    
    # Calculate confidence intervals
    ci_lower = [es - 1.96 * se for es, se in zip(effect_sizes, standard_errors)]
    ci_upper = [es + 1.96 * se for es, se in zip(effect_sizes, standard_errors)]
    
    # Plot study CIs
    y_positions = range(n)
    ax.errorbar(
        effect_sizes, y_positions,
        xerr=[[es - cl for es, cl in zip(effect_sizes, ci_lower)],
              [cu - es for es, cu in zip(effect_sizes, ci_upper)]],
        fmt='o', ecolor='gray', capsize=3, markersize=6,
        color='steelblue', alpha=0.7
    )
    
    # Plot vertical line at effect size = 0
    ax.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Plot pooled effect diamond if provided
    if pooled_effect is not None and pooled_se is not None:
        diamond_width = 1.96 * pooled_se
        ax.plot(
            [pooled_effect - diamond_width, pooled_effect + diamond_width],
            [n, n], 'D-', color='darkred', markersize=10, linewidth=2
        )
        # Draw diamond shape
        ax.add_patch(
            mpatches.Polygon(
                [
                    (pooled_effect, n),
                    (pooled_effect + diamond_width, n),
                    (pooled_effect, n + 0.3),
                    (pooled_effect - diamond_width, n)
                ],
                color='darkred', alpha=0.3
            )
        )
        
    # Labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels(study_labels, fontsize=9)
    ax.set_xlabel('Effect Size (Hedges\' g)', fontsize=11)
    ax.set_title('Forest Plot: Mindfulness Interventions for ASD Social Skills', fontsize=12, fontweight='bold')
    
    # Grid
    ax.grid(True, axis='x', linestyle=':', alpha=0.3)
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Forest plot saved to {output_path}")
    else:
        plt.show()
    
    plt.close(fig)

def create_funnel_plot(
    effect_sizes: List[float],
    standard_errors: List[float],
    study_labels: List[str],
    output_path: Optional[str] = None
) -> None:
    """
    Create a funnel plot to assess publication bias.
    
    NOTE: This function should only be called when N >= 10 per FR-014.
    
    Args:
        effect_sizes: List of effect sizes.
        standard_errors: List of standard errors.
        study_labels: List of study labels.
        output_path: Optional path to save the plot.
    """
    n = len(effect_sizes)
    if n == 0:
        logger.warning("No effect sizes provided for funnel plot.")
        return
        
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Calculate pseudo 95% confidence limits
    max_se = max(standard_errors)
    se_range = np.linspace(0, max_se * 1.1, 100)
    
    # Assuming a pooled effect of 0 for the pseudo lines (symmetric funnel)
    # In practice, you might use the pooled effect from meta-analysis
    pooled_effect = np.mean(effect_sizes) if effect_sizes else 0
    
    upper_limit = [pooled_effect + 1.96 * se for se in se_range]
    lower_limit = [pooled_effect - 1.96 * se for se in se_range]
    
    ax.fill_between(se_range, lower_limit, upper_limit, color='lightgray', alpha=0.3, label='95% CI')
    
    # Plot studies
    ax.scatter(standard_errors, effect_sizes, c='steelblue', alpha=0.7, s=50, edgecolors='black')
    
    # Label a few studies if N is small enough
    if n <= 15:
        for i, label in enumerate(study_labels):
            ax.annotate(
                label,
                (standard_errors[i], effect_sizes[i]),
                fontsize=8,
                xytext=(5, 5),
                textcoords='offset points'
            )
    
    ax.set_xlabel('Standard Error', fontsize=11)
    ax.set_ylabel('Effect Size (Hedges\' g)', fontsize=11)
    ax.set_title('Funnel Plot: Publication Bias Assessment', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, linestyle=':', alpha=0.3)
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Funnel plot saved to {output_path}")
    else:
        plt.show()
    
    plt.close(fig)

def main() -> None:
    """
    Main entry point for generating visualization plots.
    Loads effect sizes and generates forest/funnel plots.
    """
    from code.analysis.effect_sizes import calculate_effect_sizes_from_studies
    from code.data.models import Study
    from code.utils.config import get_data_path
    from code.analysis.meta_analysis import run_random_effects_meta_analysis
    
    config = get_data_path()
    studies_path = config / "processed" / "cleaned_studies.csv"
    forest_output = config / "processed" / "forest_plot.png"
    funnel_output = config / "processed" / "funnel_plot.png"
    
    if not studies_path.exists():
        logger.error(f"Cleaned studies file not found: {studies_path}")
        return
        
    df = pd.read_csv(studies_path)
    
    # Convert DataFrame rows to Study objects
    studies = []
    for _, row in df.iterrows():
        study = Study(
            study_id=row['study_id'],
            author=row['author'],
            year=int(row['year']),
            n_total=int(row['n_total']),
            intervention_n=int(row['intervention_n']),
            control_n=int(row['control_n']),
            mean_intervention=row['mean_intervention'],
            sd_intervention=row['sd_intervention'],
            mean_control=row['mean_control'],
            sd_control=row['sd_control'],
            mindfulness_components=row['mindfulness_components'],
            delivery_format=row['delivery_format'],
            social_skill_domain=row['social_skill_domain'],
            follow_up_months=int(row['follow_up_months']) if pd.notna(row['follow_up_months']) else None
        )
        studies.append(study)
        
    logger.info(f"Loaded {len(studies)} studies for visualization.")
    
    # Calculate effect sizes
    effect_size_results = calculate_effect_sizes_from_studies(studies)
    
    if len(effect_size_results) < 2:
        logger.warning("Insufficient studies for visualization (need at least 2).")
        return
        
    effect_sizes = [r.effect_size for r in effect_size_results]
    standard_errors = [r.standard_error for r in effect_size_results]
    study_labels = [f"{s.author} ({s.year})" for s in studies]
    
    # Generate forest plot
    create_forest_plot(
        effect_sizes, standard_errors, study_labels,
        output_path=str(forest_output)
    )
    
    # Generate funnel plot ONLY if N >= 10 (FR-014)
    if len(effect_sizes) >= 10:
        create_funnel_plot(
            effect_sizes, standard_errors, study_labels,
            output_path=str(funnel_output)
        )
    else:
        logger.warning(
            f"Funnel plot suppressed: Only {len(effect_sizes)} studies available. "
            "FR-014 requires N >= 10 for funnel plot generation."
        )
        # Create a placeholder text file explaining the suppression
        placeholder_path = config / "processed" / "funnel_plot_suppressed.txt"
        with open(placeholder_path, 'w') as f:
            f.write(
                f"Funnel plot suppressed.\n"
                f"Reason: Only {len(effect_sizes)} studies available.\n"
                f"Requirement: N >= 10 per FR-014 for reliable publication bias assessment.\n"
            )
        logger.info(f"Suppression notice saved to {placeholder_path}")

if __name__ == "__main__":
    main()