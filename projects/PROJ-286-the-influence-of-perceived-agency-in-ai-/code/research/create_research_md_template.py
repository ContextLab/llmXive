import os
import sys
from pathlib import Path

def create_research_md_template(output_path: str) -> None:
    """
    Create the research.md template file with the required structure.
    
    This includes the markdown table with exact column headers as specified:
    | Effect Size | Alpha | Target Power | Required N | Calculated N |
    """
    template_content = """# Research Plan: The Influence of Perceived Agency in AI Interactions on Trust

## Literature Review

This section summarizes key findings from the literature on perceived agency and trust in human-AI interaction.

### Key Citations

- **Lee, J. D., & See, K. A. (2004).** Trust in automation: Designing for appropriate reliance. *Human Factors*, 46(1), 50-80.
- **Langer, E. J. (1975).** The illusion of control. *Journal of Personality and Social Psychology*, 32(2), 311-328.

## Power Analysis

### Methodology

A power analysis was conducted to determine the required sample size for detecting the expected effect size in a one-way ANOVA design with three conditions (High Agency, Low Agency, Control).

### Parameters

- **Effect Size (f):** 0.25 (medium effect, based on previous literature)
- **Alpha Level:** 0.05
- **Target Power:** 0.80
- **Test Type:** One-way ANOVA

### Results

The following table summarizes the power analysis results:

| Effect Size | Alpha | Target Power | Required N | Calculated N |
|-------------|-------|--------------|------------|--------------|
| 0.25        | 0.05  | 0.80         | TBD        | TBD          |

*Note: The "Required N" and "Calculated N" columns will be populated by the power analysis script (T002).*

## Hypotheses

### Primary Hypothesis

H1: Participants in the High Agency condition will report significantly higher trust scores compared to the Control condition.

### Secondary Hypotheses

H2: Participants in the Low Agency condition will report significantly lower trust scores compared to the Control condition.

H3: The perceived agency score will be significantly higher in the High Agency condition compared to the Low Agency condition.

## Analysis Plan

### Statistical Tests

1. **One-way ANOVA** to test for overall differences in trust scores across conditions.
2. **Planned Contrasts:**
   - High vs. Low (coefficients: [1, -1, 0])
   - (High + Low) vs. Control (coefficients: [1, 1, -2])
3. **Post-hoc tests:** Tukey HSD for all pairwise comparisons.
4. **Effect sizes:** Cohen's d for all pairwise comparisons.

### Sensitivity Analysis

Sensitivity analyses will be conducted to assess the robustness of results to:
- Attention check pass rate thresholds
- Straight-lining detection thresholds
- Completion time outliers

## References

- Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors*, 46(1), 50-80.
- Langer, E. J. (1975). The illusion of control. *Journal of Personality and Social Psychology*, 32(2), 311-328.
"""

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"Research.md template created at {output_path}")

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create the research.md template file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='specs/001-perceived-agency-trust/research.md',
        help='Path to output research.md file'
    )
    
    args = parser.parse_args()
    
    try:
        create_research_md_template(args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()