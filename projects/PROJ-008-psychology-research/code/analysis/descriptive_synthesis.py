import logging
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass
from code.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DescriptiveSynthesisResult:
    """Result of a descriptive synthesis."""
    k_studies: int
    mean_effect: float
    std_dev: float
    min_effect: float
    max_effect: float
    median_effect: float
    effect_size_range: str
    narrative_summary: str

def perform_descriptive_synthesis(
    effect_sizes: List[Any]
) -> DescriptiveSynthesisResult:
    """
    Perform a descriptive synthesis of effect sizes when meta-analysis is not appropriate (N < 10).
    Calculates basic statistics and generates a narrative summary.
    """
    if not effect_sizes:
        raise ValueError("No effect sizes provided for descriptive synthesis.")

    effects = [es.effect_size for es in effect_sizes if hasattr(es, 'effect_size')]
    if not effects:
        raise ValueError("Could not extract effect sizes from input.")

    k = len(effects)
    mean_eff = float(np.mean(effects))
    std_eff = float(np.std(effects, ddof=1))
    min_eff = float(np.min(effects))
    max_eff = float(np.max(effects))
    median_eff = float(np.median(effects))

    # Determine range string
    range_str = f"{min_eff:.3f} to {max_eff:.3f}"

    # Generate narrative summary
    # Interpret direction based on sign (assuming positive = improvement)
    direction = "improvement" if mean_eff > 0 else "deterioration" if mean_eff < 0 else "no change"
    magnitude = "small"
    if abs(mean_eff) > 0.2: magnitude = "small"
    if abs(mean_eff) > 0.5: magnitude = "medium"
    if abs(mean_eff) > 0.8: magnitude = "large"

    narrative = (
        f"A descriptive synthesis of {k} studies was performed. "
        f"The mean effect size was {mean_eff:.3f} (SD={std_eff:.3f}), "
        f"ranging from {min_eff:.3f} to {max_eff:.3f}. "
        f"This indicates a {magnitude} {direction} in social skills outcomes. "
        f"Due to the limited number of studies (N={k} < 10), a random-effects meta-analysis was not conducted."
    )

    return DescriptiveSynthesisResult(
        k_studies=k,
        mean_effect=mean_eff,
        std_dev=std_eff,
        min_effect=min_eff,
        max_effect=max_eff,
        median_effect=median_eff,
        effect_size_range=range_str,
        narrative_summary=narrative
    )

def format_synthesis_report(
    result: DescriptiveSynthesisResult
) -> str:
    """
    Format the descriptive synthesis result into a readable report string.
    """
    lines = [
        "## Descriptive Synthesis Report",
        "",
        f"**Number of Studies:** {result.k_studies}",
        f"**Mean Effect Size:** {result.mean_effect:.4f}",
        f"**Standard Deviation:** {result.std_dev:.4f}",
        f"**Median Effect Size:** {result.median_effect:.4f}",
        f"**Range:** {result.effect_size_range}",
        "",
        "### Narrative Summary",
        result.narrative_summary,
        "",
        "### Note",
        "This synthesis was performed because the number of studies was below the threshold required for meta-analysis."
    ]
    return "\n".join(lines)

def main():
    """
    Entry point for testing descriptive synthesis.
    """
    # Mock data for testing
    class MockES:
        def __init__(self, val):
            self.effect_size = val

    mock_data = [MockES(0.2), MockES(0.5), MockES(-0.1), MockES(0.8), MockES(0.3)]
    result = perform_descriptive_synthesis(mock_data)
    print(format_synthesis_report(result))

if __name__ == "__main__":
    main()
