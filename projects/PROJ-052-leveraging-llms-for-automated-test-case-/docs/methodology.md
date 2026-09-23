# Methodological Documentation

## Strict Pairing Exclusion Logic

This document details the "Strict Pairing" exclusion criteria implemented in the `data_loader.py` and `analyzer.py` modules, and its impact on the statistical validity of the study.

### 1. The Problem: Unpaired Samples

In the Defects4J dataset, not every bug fix commit is accompanied by a specific, failing unit test method that targets the exact code change. Some entries may have:
- No test file associated.
- A test file that passes on the buggy version (false negative).
- A test file that is too generic to serve as a baseline.

Comparing an LLM-generated test against such samples would violate the "Strict Pairing" principle, as there is no ground-truth manual baseline to compare coverage against.

### 2. The Solution: `validate_manual_baseline_existence`

The pipeline implements a rigorous validation step before any test generation or analysis occurs.

**Implementation Location**: `code/data_loader.py` -> `validate_manual_baseline_existence(bug_id)`

**Logic**:
1. Query the Defects4J metadata for the `bug_id`.
2. Check for the existence of a specific test method ID known to fail on the buggy version.
3. If the test method is missing or invalid:
 - Return `False`.
 - Log the `bug_id` to `data/exclusion_log.json` under the key `missing_manual_baseline`.
 - Skip the sample in the main pipeline loop.

**Code Reference**:
```python
def validate_manual_baseline_existence(bug_id: str) -> bool:
 # Implementation details in code/data_loader.py
 pass
```

### 3. Impact on Statistical Analysis

The exclusion of samples affects the final dataset used for the Wilcoxon signed-rank test or paired t-test.

**Exclusion Rate Calculation**:
The `report_generator.py` module calculates the exclusion rate as:
$$ \text{Exclusion Rate} = \frac{\text{excluded\_count}}{\text{total\_samples}} $$

This rate is reported in `data/analysis_results.json` and included in `data/final_report.md`.

**Study Limitations**:
- **High Exclusion Rate**: If the exclusion rate > 50%, the final report prepends a warning: "Study Limitation: High Exclusion Rate (>50%). The results are based on a biased subset of bugs with specific manual baselines."
- **Sample Size**: If the remaining sample size (N) < 30, a warning is prepended: "WARNING: Sample size (N={N}) < 30. Results are exploratory."

### 4. Reproducibility

To reproduce the exact set of included/excluded samples:
1. Ensure the Defects4J dataset version matches the one used in the original run.
2. Run `python code/data_loader.py` with the `--verify-baseline` flag (if implemented) or inspect `data/exclusion_log.json` to see which `bug_id`s were dropped.
3. The statistical analysis in `code/analyzer.py` automatically filters out these IDs based on the `coverage_metrics.csv` and `exclusion_log.json`.

### 5. Future Work

Potential improvements to reduce exclusion rates without compromising rigor:
- Automated synthesis of manual baselines for samples lacking them.
- Refining the metadata query to detect "generic" tests that might still serve as valid baselines.
- Expanding the dataset to include other bug repositories with stricter test coverage.
