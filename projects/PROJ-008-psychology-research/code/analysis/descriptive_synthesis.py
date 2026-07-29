import logging
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass

from code.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DescriptiveSynthesisResult:
    """Result of a descriptive synthesis when statistical meta-analysis is not possible."""
    n_studies: int
    effect_sizes: List[float]
    mean_effect: float
    std_effect: float
    min_effect: float
    max_effect: float
    median_effect: float
    iqr_low: float
    iqr_high: float
    narrative_summary: str

def perform_descriptive_synthesis(
    effect_sizes: List[float],
    study_ids: List[str],
    study_details: Optional[List[Dict[str, Any]]] = None
) -> DescriptiveSynthesisResult:
    """
    Perform a descriptive synthesis of effect sizes when meta-analysis is not appropriate.
    
    This function implements FR-014: When N < 10, switch from statistical meta-analysis
    to descriptive synthesis.
    
    Args:
        effect_sizes: List of effect sizes (Hedges' g)
        study_ids: List of study identifiers
        study_details: Optional list of dictionaries with study metadata
        
    Returns:
        DescriptiveSynthesisResult with summary statistics and narrative
    """
    if len(effect_sizes) == 0:
        raise ValueError("At least one effect size is required for descriptive synthesis")
    
    effect_array = np.array(effect_sizes)
    
    # Calculate summary statistics
    mean_effect = float(np.mean(effect_array))
    std_effect = float(np.std(effect_array, ddof=1)) if len(effect_array) > 1 else 0.0
    min_effect = float(np.min(effect_array))
    max_effect = float(np.max(effect_array))
    median_effect = float(np.median(effect_array))
    
    # Calculate IQR
    q1 = np.percentile(effect_array, 25)
    q3 = np.percentile(effect_array, 75)
    iqr_low = float(q1)
    iqr_high = float(q3)
    
    # Build narrative summary
    narrative_parts = []
    narrative_parts.append(f"Descriptive synthesis of {len(effect_sizes)} studies.")
    narrative_parts.append(f"Effect sizes ranged from {min_effect:.3f} to {max_effect:.3f}.")
    narrative_parts.append(f"The mean effect size was {mean_effect:.3f} (SD = {std_effect:.3f}).")
    narrative_parts.append(f"The median effect size was {median_effect:.3f} (IQR: {iqr_low:.3f} to {iqr_high:.3f}).")
    
    if study_details:
        narrative_parts.append("\nStudy details:")
        for i, detail in enumerate(study_details):
            study_id = study_ids[i] if i < len(study_ids) else f"Study {i+1}"
            narrative_parts.append(f"  - {study_id}: g = {effect_sizes[i]:.3f}")
            if isinstance(detail, dict):
                if 'intervention' in detail:
                    narrative_parts[-1] += f" ({detail['intervention']})"
                if 'population' in detail:
                    narrative_parts[-1] += f" in {detail['population']}"
    
    narrative_summary = " ".join(narrative_parts)
    
    return DescriptiveSynthesisResult(
        n_studies=len(effect_sizes),
        effect_sizes=effect_sizes,
        mean_effect=mean_effect,
        std_effect=std_effect,
        min_effect=min_effect,
        max_effect=max_effect,
        median_effect=median_effect,
        iqr_low=iqr_low,
        iqr_high=iqr_high,
        narrative_summary=narrative_summary
    )

def format_synthesis_report(
    synthesis_result: DescriptiveSynthesisResult,
    context: str = "Mindfulness interventions for social skills in ASD"
) -> str:
    """
    Format a descriptive synthesis result into a readable report.
    
    Args:
        synthesis_result: The descriptive synthesis result
        context: Contextual information about the analysis
        
    Returns:
        Formatted report string
    """
    report_lines = [
        "=" * 60,
        "DESCRIPTIVE SYNTHESIS REPORT",
        "=" * 60,
        "",
        f"Context: {context}",
        "",
        f"Number of studies: {synthesis_result.n_studies}",
        "",
        "Summary Statistics:",
        f"  Mean effect size (g): {synthesis_result.mean_effect:.3f}",
        f"  Standard deviation: {synthesis_result.std_effect:.3f}",
        f"  Median effect size: {synthesis_result.median_effect:.3f}",
        f"  Interquartile range: [{synthesis_result.iqr_low:.3f}, {synthesis_result.iqr_high:.3f}]",
        f"  Range: [{synthesis_result.min_effect:.3f}, {synthesis_result.max_effect:.3f}]",
        "",
        "Narrative Summary:",
        synthesis_result.narrative_summary,
        "",
        "Note: Statistical meta-analysis was not performed due to insufficient",
        "sample size (N < 10). Results should be interpreted as descriptive only.",
        "=" * 60
    ]
    
    return "\n".join(report_lines)

def main():
    """Main entry point for descriptive synthesis module."""
    logger.info("Descriptive synthesis module loaded successfully")
    logger.info("Functions available:")
    logger.info("  - perform_descriptive_synthesis")
    logger.info("  - format_synthesis_report")

if __name__ == "__main__":
    main()