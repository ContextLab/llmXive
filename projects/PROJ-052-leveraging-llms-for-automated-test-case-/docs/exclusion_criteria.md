# Exclusion Criteria: Strict Pairing

## Overview

This document provides a detailed technical explanation of the "Strict Pairing" exclusion logic implemented in PROJ-052. This logic is critical for maintaining the scientific integrity of the comparison between LLM-generated tests and manual baselines.

## The "Strict Pairing" Principle

The core hypothesis of this research is that LLM-generated tests can match or exceed the coverage of manual tests *on the specific lines of code changed by a bug fix*. To test this, we require a **paired** experimental design:
1. **Sample**: A specific bug fix (commit).
2. **Treatment**: Coverage of lines changed by the LLM-generated test.
3. **Control**: Coverage of lines changed by the manual test.

For this comparison to be valid, a **specific manual test** that targets the bug must exist in the Defects4J dataset.

## Exclusion Logic Implementation

The exclusion logic is implemented in `code/data_loader.py` via the function `validate_manual_baseline_existence(bug_id)`.

### Execution Flow

1. **Data Ingestion**: The pipeline streams the Defects4J dataset.
2. **Baseline Check**: For each `bug_id`, the system queries the metadata to find a corresponding test method ID known to fail on the buggy version.
3. **Decision**:
 - **If Baseline Exists**: The sample is included in the processing queue.
 - **If Baseline Missing**: The sample is **excluded**.
 - The `bug_id` is added to `data/exclusion_log.json` with the key `missing_manual_baseline`.
 - No test generation or execution occurs for this sample.

### Code Snippet (Conceptual)

```python
def validate_manual_baseline_existence(bug_id: str) -> bool:
 # Query Defects4J metadata
 metadata = get_defects4j_metadata(bug_id)
 if not metadata or not metadata.get('failing_test_method'):
 return False
 return True
```

## Impact on Results

### Exclusion Rate

The **Exclusion Rate** is the percentage of total samples dropped due to this criterion.
$$ \text{Exclusion Rate} = \frac{\text{Count of Missing Baselines}}{\text{Total Samples}} $$

This metric is calculated in `code/report_generator.py` and reported in `data/final_report.md`.

### Interpretation

- **Low Exclusion Rate (< 20%)**: The study results are likely representative of the broader Defects4J population.
- **High Exclusion Rate (> 50%)**: The results are based on a potentially biased subset of bugs (those with well-documented, specific tests). A warning is issued in the final report to contextualize the findings.

## Why Not Use Synthetic Baselines?

Using synthetic or generic tests as a fallback would violate the "Strict Pairing" principle because:
1. **Invalid Control**: A generic test might not cover the specific changed lines, making the comparison meaningless.
2. **Bias Introduction**: The LLM might be compared against a "weak" baseline, artificially inflating its perceived performance.
3. **Scientific Rigor**: The goal is to compare against *human* expertise, not a synthetic approximation.

## Conclusion

The "Strict Pairing" exclusion logic is a deliberate methodological constraint designed to ensure the validity of the statistical analysis. While it reduces the sample size, it guarantees that every data point in the final analysis represents a true, apples-to-apples comparison.
