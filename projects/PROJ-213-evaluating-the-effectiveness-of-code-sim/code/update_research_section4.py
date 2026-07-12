"""
Task T004: Document statistical design in research.md Section 4.

Implements the statistical design documentation as per spec FR-005:
- Wilcoxon signed-rank test for pass@1 and latency
- Bonferroni correction for 2 hypotheses (accuracy, latency)
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports if running as script
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

RESEARCH_FILE = "specs/001-eval-code-simplification/research.md"

def ensure_research_file():
    """Ensure research.md exists with basic structure."""
    research_path = Path(RESEARCH_FILE)
    if not research_path.exists():
        # Create directory if it doesn't exist
        research_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write initial structure
        initial_content = f"""# Research Documentation

**Generated**: {datetime.now().isoformat()}

## Section 1: Dataset Verification

*To be completed by T001*

## Section 2: Model Feasibility

*To be completed by T002*

## Section 3: Power Analysis

*To be completed by T003 and T003a*

## Section 4: Statistical Design

*This section will be populated by T004*

## Section 5: Constitutional Compliance

*To be completed by T004a*
"""
        with open(research_path, 'w', encoding='utf-8') as f:
            f.write(initial_content)
        print(f"Created new research.md at {research_path}")
    return research_path

def generate_section4_content():
    """Generate the content for Section 4: Statistical Design."""
    content = f"""## Section 4: Statistical Design

**Generated**: {datetime.now().isoformat()}

### 4.1 Overview

This section documents the statistical design for evaluating the effectiveness of code simplification on LLM performance, as specified in FR-005.

### 4.2 Hypotheses

The following hypotheses are tested:

1. **H1 (Accuracy)**: There is no significant difference in pass@1 scores between raw and simplified code inputs.
   - Null Hypothesis (H0): Median(pass@1_raw) = Median(pass@1_simplified)
   - Alternative Hypothesis (H1): Median(pass@1_raw) ≠ Median(pass@1_simplified)

2. **H2 (Latency)**: There is no significant difference in inference latency between raw and simplified code inputs.
   - Null Hypothesis (H0): Median(latency_raw) = Median(latency_simplified)
   - Alternative Hypothesis (H1): Median(latency_raw) ≠ Median(latency_simplified)

### 4.3 Statistical Tests

Per spec FR-005, the following tests are employed:

#### 4.3.1 Primary Test: Wilcoxon Signed-Rank Test

- **Application**: Paired comparison of pass@1 scores and inference latency
- **Rationale**: 
  - Data is paired (same problems evaluated under both conditions)
  - Distribution assumptions for parametric tests (normality) cannot be guaranteed
  - Wilcoxon signed-rank test is appropriate for paired, non-normally distributed data
- **Implementation**: `scipy.stats.wilcoxon`

#### 4.3.2 Multiple Comparison Correction: Bonferroni

- **Application**: Correction for 2 hypotheses (accuracy and latency)
- **Rationale**: 
  - Controls family-wise error rate (FWER)
  - Conservative approach suitable for small number of hypotheses
- **Calculation**: 
  - Adjusted alpha = α / k = 0.05 / 2 = 0.025
  - Adjusted p-value = min(p_raw × k, 1.0) where k=2
- **Implementation**: Manual adjustment of p-values from Wilcoxon tests

### 4.4 Analysis Procedure

1. **Data Preparation**:
   - Extract paired pass@1 scores from `data/processed/results_raw.csv` and `data/processed/results_simplified.csv`
   - Extract paired inference latency values from `data/processed/metrics_raw.csv` and `data/processed/metrics_simplified.csv`
   - Filter out pairs with missing values (parse failures, timeouts)

2. **Normality Check** (Diagnostic):
   - Perform Shapiro-Wilk test on difference scores
   - If normality assumption holds, consider parametric alternatives (paired t-test) as supplementary analysis

3. **Primary Analysis**:
   - Run Wilcoxon signed-rank test for pass@1 differences
   - Run Wilcoxon signed-rank test for latency differences
   - Apply Bonferroni correction to both p-values

4. **Effect Size Calculation** (Per FR-006):
   - Calculate Cohen's d for both metrics
   - Supplementary: Rank-biserial correlation for Wilcoxon tests

5. **Decision Rules**:
   - Reject H0 if adjusted p-value < 0.025
   - Report effect sizes with confidence intervals
   - Document any violations of test assumptions

### 4.5 Output Artifacts

The analysis will produce:
- `analysis_report.pdf`: Comprehensive statistical report including:
  - Test statistics (W, Z)
  - Raw and adjusted p-values
  - Effect sizes (Cohen's d, rank-biserial)
  - Visualizations (bar charts with error bars)
  - Interpretation of results

### 4.6 Assumptions and Limitations

1. **Independence**: Problems are independent samples
2. **Paired Design**: Each problem is evaluated under both conditions
3. **Ordinal/Continuous Data**: pass@1 (binary per sample, aggregated), latency (continuous)
4. **Symmetry**: Wilcoxon assumes symmetric distribution of differences (less strict than normality)

### 4.7 References

- Wilcoxon, F. (1945). "Individual Comparisons by Ranking Methods". Biometrics Bulletin.
- Bonferroni, C. E. (1936). "Teoria statistica delle classi e calcolo delle probabilità".
- Spec FR-005: Statistical testing requirements
- Spec FR-006: Effect size reporting requirements
"""
    return content

def update_research_section4():
    """Update research.md with Section 4 content."""
    research_path = ensure_research_file()
    
    # Read current content
    with open(research_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate new Section 4
    section4 = generate_section4_content()
    
    # Find and replace Section 4
    # Pattern to match Section 4 header and content until Section 5
    import re
    pattern = r'(## Section 4: Statistical Design.*?)(?=## Section 5:|## Section 6:|$)'
    
    # Check if Section 4 exists
    if re.search(pattern, content, re.DOTALL):
        # Replace existing Section 4
        new_content = re.sub(pattern, section4 + '\n', content, flags=re.DOTALL)
        print("Updated existing Section 4 in research.md")
    else:
        # Append Section 4 before Section 5 or at end
        if '## Section 5:' in content:
            # Insert before Section 5
            new_content = content.replace('## Section 5:', section4 + '\n\n## Section 5:')
            print("Inserted Section 4 before Section 5 in research.md")
        else:
            # Append at end
            new_content = content + '\n' + section4
            print("Appended Section 4 at end of research.md")
    
    # Write updated content
    with open(research_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Successfully updated {research_path} with Section 4: Statistical Design")
    return True

def main():
    """Main entry point."""
    print("Task T004: Documenting statistical design in research.md Section 4...")
    print("Spec FR-005: Wilcoxon for pass@1 and latency, Bonferroni for 2 hypotheses")
    
    try:
        success = update_research_section4()
        if success:
            print("\n✓ Task T004 completed successfully")
            print(f"  - Updated: {RESEARCH_FILE}")
            print(f"  - Section 4: Statistical Design (Wilcoxon + Bonferroni)")
            return 0
        else:
            print("\n✗ Task T004 failed: Could not update research.md")
            return 1
    except Exception as e:
        print(f"\n✗ Task T004 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())