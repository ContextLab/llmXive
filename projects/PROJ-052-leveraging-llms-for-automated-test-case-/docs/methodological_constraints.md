# Methodological Constraints: Strict Pairing Logic

## Overview

This document details the "Strict Pairing" exclusion criteria implemented in the PROJ-052 pipeline. These constraints are critical for maintaining the validity of the statistical comparison between LLM-generated tests and manual baselines.

## The Strict Pairing Requirement

The core hypothesis of this research is that LLM-generated tests can achieve comparable or superior line coverage on *changed lines* compared to manual tests. To test this fairly:

1. **Target**: We measure coverage on specific lines changed in a bug fix.
2. **Baseline**: We require a manual test that *specifically* fails on the buggy version and passes on the fixed version.
3. **Pairing**: For every generated test, there must be a corresponding manual test for the same bug instance.

If a manual baseline is missing, we cannot establish a ground truth for what "correct" coverage should look like for that specific bug. Including such samples would introduce bias, as we would be comparing generated tests against an undefined or non-existent baseline.

## Implementation Details

### Detection and Exclusion

The exclusion logic is implemented in `code/data_loader.py`:

- **Function**: `validate_manual_baseline_existence(bug_id: str) -> bool`
- **Mechanism**: Queries the Defects4J metadata for the specific `test_method` associated with the bug.
- **Action**:
 - If `True`: The sample proceeds to generation and analysis.
 - If `False`: The sample is skipped. An entry is logged to `data/exclusion_log.json` with key `missing_manual_baseline`.

### Reporting the Impact

The impact of this exclusion is quantified and reported in two places:

1. **`data/exclusion_log.json`**:
 - `total_samples`: Total number of samples attempted.
 - `excluded_count`: Number of samples dropped due to missing baselines.
 - `pairable_count`: Number of samples that passed the filter.

2. **`data/analysis_results.json`**:
 - `exclusion_rate`: Calculated as `excluded_count / total_samples`.
 - This metric is used by `code/report_generator.py` to determine if a warning should be prepended to the final report.

## Rationale for High Exclusion Rates

The Defects4J dataset, while comprehensive, does not always provide explicit, granular metadata linking every bug to a single, specific failing test method in a machine-readable format suitable for automated pairing. Some bugs may have multiple tests, or the test metadata may be incomplete.

By strictly enforcing this pairing, we ensure that every data point in our final statistical analysis represents a valid, apples-to-apples comparison. We prioritize **data validity** over **sample size**.

## Limitations and Mitigations

- **Limitation**: High exclusion rates reduce statistical power (N).
- **Mitigation**: The pipeline performs a post-hoc power analysis (Task T061) and explicitly reports the achieved power in the final report. If N < 30, the results are labeled as "exploratory".
- **Limitation**: The exclusion rate itself is a methodological limitation.
- **Mitigation**: The final report (`data/final_report.md`) includes a dedicated "Study Limitation" section if `exclusion_rate > 0.5`, ensuring transparency about the scope of the findings.