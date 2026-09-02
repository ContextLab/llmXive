# Research: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

## Summary

This research document investigates the feasibility of correlating gut microbiome composition with sleep quality using public datasets. The primary source for microbiome data is the American Gut Project (AGP). The analysis requires specific variables: OTU count tables, `antibiotic_use_last_3m`, `sleep_efficiency`, and `sleep_duration_hours`.

## Dataset Strategy

### Verified Datasets Analysis

The `# Verified datasets` block provided for this project revision was analyzed against the requirements of FR-001 and FR-002.

| Dataset Name | Source URL | Contains Required Variables? | Status |
|:--- |:--- |:--- |:--- |
| **American Gut Project (AGP)** | *Not found in verified block* | **NO** (No verified URL provided) | **BLOCKED** |
| OTU (tsv) | ` | No (OTU counts only, no sleep metadata) | Incompatible |
| OTU (csv) | ` | No (Generic OTU data, no sleep metadata) | Incompatible |
| BMI (csv) | ` | No (BMI only, no microbiome) | Incompatible |
| CPU-only (parquet) | ` | No (LLM benchmark data) | Incompatible |

### Conclusion: Dataset Unavailability

**There is no verified, programmatic URL in the provided `# Verified datasets` block that contains the American Gut Project data with the required sleep metadata.**

Consequently:
1. **FR-001 (Download)** cannot be executed as a "Happy Path" task.
2. **FR-002 (Filter)** cannot be executed as the input data does not exist.
3. The project **MUST** execute the **Feasibility Termination** path.

### Rationale for Feasibility Termination Execution

Attempting to use the generic OTU datasets (e.g., `otus-fw`) would constitute **fabrication** of the sleep-microbiome link, as these datasets do not contain sleep variables. The Constitution (Principle III: Data Hygiene) and the "No Fabrication" rule strictly prohibit this. Therefore, the only valid implementation is to:
1. Verify the absence of the required URL.
2. Generate a "Feasibility Report" (a single file documenting the failure).
3. Generate a final report explicitly stating "Analysis not performed due to data unavailability".

## Statistical Methodology (If Unblocked)

*Note: This section describes the method to be used if a verified AGP URL becomes available. In the current blocked state, these steps are skipped.*

1. **Alpha-Diversity**: Compute Shannon, Simpson, and Observed OTUs using `scikit-bio`.
 * *Justification*: Non-parametric, robust to compositional data.
2. **Correlation**: Spearman rank correlation between diversity indices and sleep metrics.
 * *Justification*: Sleep and diversity distributions are often non-normal; Spearman detects monotonic trends.
3. **Multiple Comparison Correction**: Benjamini-Hochberg (BH) procedure.
 * *Justification*: Controls False Discovery Rate (FDR) for the set of ~6 tests (3 diversity x 2 sleep metrics).
4. **Significance Threshold**: q-value < 0.05.
5. **Effect Size**: |r| > 0.3 defined as "moderate".

## Compute Feasibility

- **CPU-First**: The planned analysis (Spearman correlation on a large-scale dataset) is computationally trivial for a 2-core CPU. No GPU is required.
- **Memory**: The full AGP dataset may exceed a significant amount of RAM. The implementation must use `pandas` chunking or `datasets` streaming to stay within limits.
- **Time**: Correlation and diversity calculations are O(N) or O(N log N) and will complete well within the allocated time limit.

## Decision: Feasibility Termination Execution

**Decision**: Execute the "Feasibility Termination" workflow defined in the plan.
**Rationale**: The absence of a verified AGP URL in the `# Verified datasets` block makes the "Happy Path" impossible without violating the "No Fabrication" rule. The Feasibility Termination ensures the pipeline produces a valid, reproducible artifact (the report of unavailability) rather than crashing or generating fake data.