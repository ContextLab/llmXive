"""
Pilot Report Generator (T032)

Compiles the final pilot report in docs/pilot_report.md.
Labels findings as 'Pilot/Methodology Validation'.
Documents limitations (Global data blocked, no climate stratification).
Includes full statistical power documentation (p-values, effect sizes, robustness).
References docs/deviations.md.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime

from config import get_processed_path, get_deviations_path, get_test_region
from utils.logging import get_logger

logger = get_logger(__name__)

def load_json_file(file_path: Path) -> dict:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_deviations() -> str:
    """Load the deviations document content."""
    path = get_deviations_path()
    if not path.exists():
        logger.warning(f"Deviations file not found at {path}. Using placeholder text.")
        return "No deviations recorded."
    
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_report_content(
    statistical_results: dict,
    robustness_report: dict,
    deviations_content: str
) -> str:
    """Generate the Markdown content for the pilot report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    region = get_test_region()

    report = f"""# Pilot Report: Correlation Between Atmospheric Pressure and Earthquake Precursors

**Date Generated**: {timestamp}
**Test Region**: {region}
**Status**: Pilot / Methodology Validation

---

## 1. Executive Summary

This report documents the results of the **Pilot/Methodology Validation** phase for the study on the correlation between atmospheric pressure anomalies and earthquake precursors. 

The primary goal of this pilot was to validate the data acquisition, pre-processing, and statistical analysis pipeline using a verified test subset (2018 Alaska, N=12 earthquakes) due to constraints on global data access.

**Key Findings**:
- The pipeline successfully processed {statistical_results.get('total_events', 'N/A')} events.
- Statistical significance was evaluated using Kolmogorov-Smirnov tests and permutation tests.
- Robustness checks were performed across magnitude and regional stratifications.

---

## 2. Methodology and Limitations

### 2.1 Data Constraints (FR-001)
Per Constitution Principle II and the project's deviation records, **global data download was blocked** due to the absence of verified, programmatically accessible NOAA NCEP/NCAR sources for the full 2013-2023 period. 

Consequently:
- The analysis is restricted to a **verified test subset** (2018 Alaska region, N=12 events).
- Global climate indices (ENSO, PDO) were not included in the stratification (FR-011).
- All findings must be interpreted as **methodological validation** rather than definitive global scientific conclusions.

### 2.2 Deviation Record
Refer to `docs/deviations.md` for the formal record of scope reductions:
{deviations_content}

---

## 3. Statistical Power Documentation

### 3.1 Primary Statistical Results
The following results are derived from the `data/processed/statistical_results.json` artifact.

| Metric | Value | Interpretation |
| :--- | :--- | :--- |
| **P-Value (Permutation)** | {statistical_results.get('p_value_permutation', 'N/A')} | Probability of observing this statistic under the null hypothesis. |
| **P-Value (KS Test)** | {statistical_results.get('p_value_ks', 'N/A')} | Two-sample Kolmogorov-Smirnov test result. |
| **Effect Size (Cohen's d)** | {statistical_results.get('effect_size', 'N/A')} | Magnitude of the difference between event and control windows. |
| **Null Hypothesis** | {statistical_results.get('null_hypothesis', 'Rejected if p < 0.05')} | No difference in pressure anomaly distributions. |

**Framing**: These results are presented as **associational evidence** only, in accordance with FR-005. No causal claims are made.

### 3.2 Robustness Analysis
The following table summarizes the sensitivity of the results across different subsets and parameters (from `data/processed/robustness_report.json`).

#### Stratification by Magnitude
| Magnitude Range | Events | P-Value | Effect Size | Significant? |
| :--- | :--- | :--- | :--- | :--- |
| 4.0 - 5.0 | {robustness_report.get('magnitude', {}).get('4.0-5.0', {}).get('count', 'N/A')} | {robustness_report.get('magnitude', {}).get('4.0-5.0', {}).get('p_value', 'N/A')} | {robustness_report.get('magnitude', {}).get('4.0-5.0', {}).get('effect_size', 'N/A')} | {robustness_report.get('magnitude', {}).get('4.0-5.0', {}).get('significant', 'N/A')} |
| > 5.0 | {robustness_report.get('magnitude', {}).get('>5.0', {}).get('count', 'N/A')} | {robustness_report.get('magnitude', {}).get('>5.0', {}).get('p_value', 'N/A')} | {robustness_report.get('magnitude', {}).get('>5.0', {}).get('effect_size', 'N/A')} | {robustness_report.get('magnitude', {}).get('>5.0', {}).get('significant', 'N/A')} |

#### Stratification by Region
| Region | Events | P-Value | Effect Size | Significant? |
| :--- | :--- | :--- | :--- | :--- |
| Pacific Ring of Fire | {robustness_report.get('region', {}).get('ring_of_fire', {}).get('count', 'N/A')} | {robustness_report.get('region', {}).get('ring_of_fire', {}).get('p_value', 'N/A')} | {robustness_report.get('region', {}).get('ring_of_fire', {}).get('effect_size', 'N/A')} | {robustness_report.get('region', {}).get('ring_of_fire', {}).get('significant', 'N/A')} |
| Others | {robustness_report.get('region', {}).get('others', {}).get('count', 'N/A')} | {robustness_report.get('region', {}).get('others', {}).get('p_value', 'N/A')} | {robustness_report.get('region', {}).get('others', {}).get('effect_size', 'N/A')} | {robustness_report.get('region', {}).get('others', {}).get('significant', 'N/A')} |

#### Sensitivity Analysis (Anomaly Cutoff)
| Cutoff (σ) | P-Value | Effect Size | Significant? |
| :--- | :--- | :--- | :--- |
| 1.0σ | {robustness_report.get('sensitivity', {}).get('1.0', {}).get('p_value', 'N/A')} | {robustness_report.get('sensitivity', {}).get('1.0', {}).get('effect_size', 'N/A')} | {robustness_report.get('sensitivity', {}).get('1.0', {}).get('significant', 'N/A')} |
| 1.5σ | {robustness_report.get('sensitivity', {}).get('1.5', {}).get('p_value', 'N/A')} | {robustness_report.get('sensitivity', {}).get('1.5', {}).get('effect_size', 'N/A')} | {robustness_report.get('sensitivity', {}).get('1.5', {}).get('significant', 'N/A')} |
| 2.0σ | {robustness_report.get('sensitivity', {}).get('2.0', {}).get('p_value', 'N/A')} | {robustness_report.get('sensitivity', {}).get('2.0', {}).get('effect_size', 'N/A')} | {robustness_report.get('sensitivity', {}).get('2.0', {}).get('significant', 'N/A')} |

---

## 4. Conclusion

This pilot study successfully validated the end-to-end research pipeline, including data acquisition, pre-processing, statistical analysis, and robustness checks. 

**Limitations**:
- **Data Scope**: The analysis is limited to a small, verified test subset (N=12) due to the unavailability of global pressure data (FR-001).
- **Climate Factors**: Global climate indices (ENSO, PDO) were excluded from the analysis (FR-011).
- **Generalizability**: Results cannot be extrapolated to global earthquake prediction without further data acquisition and validation.

**Next Steps**:
1. Secure access to verified global atmospheric pressure data (e.g., via alternative APIs or datasets).
2. Expand the dataset to include the full 2013-2023 period.
3. Re-run the analysis with global climate indices included.
4. Validate findings against a larger, more diverse dataset.

---

*Generated by llmXive Automated Science Pipeline*
"""
    return report

def main():
    """Main entry point for generating the pilot report."""
    logger.info("Starting pilot report generation (T032)...")
    
    # Define paths
    processed_path = get_processed_path()
    stats_file = processed_path / "statistical_results.json"
    robustness_file = processed_path / "robustness_report.json"
    output_dir = Path("docs")
    output_file = output_dir / "pilot_report.md"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        logger.info(f"Loading statistical results from {stats_file}...")
        statistical_results = load_json_file(stats_file)
        
        logger.info(f"Loading robustness report from {robustness_file}...")
        robustness_report = load_json_file(robustness_file)
        
        logger.info("Loading deviations document...")
        deviations_content = load_deviations()
        
        # Generate report
        logger.info("Generating report content...")
        report_content = generate_report_content(
            statistical_results,
            robustness_report,
            deviations_content
        )
        
        # Write report
        logger.info(f"Writing report to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info("Pilot report generated successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        raise

if __name__ == "__main__":
    main()