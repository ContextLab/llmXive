# Research: 001-social-rejection-reward

## Executive Summary

This research plan outlines the methodology for analyzing the effect of simulated social rejection on immediate behavioral responses (mood, reaction times) using the **single verified dataset ds000208** (OpenNeuro).

**Critical Data Strategy Revision**: The original hypothesis of "modulation by reward" required a linked reward dataset which does not exist in the verified sources. The project now pivots to a valid, self-contained hypothesis: **"Does simulated social rejection (vs. control) significantly alter post-task mood and reaction times?"** This analysis is performed entirely within ds000208, comparing the Rejection condition against the Control condition. The "Composite Dataset" and "Cross-Dataset Between-Subjects" strategies are **removed** as scientifically invalid.

## Dataset Strategy

### Verified Sources

Per the project constraints and the "Verified datasets" block provided:

1. **Rejection Dataset (Cyberball Proxy)**:
 * **Source**: OpenNeuro (via HuggingFace mirror).
 * **URL**: `
 * **Rationale**: This dataset is verified to exist and is accessible via HuggingFace. It serves as the proxy for the social rejection condition.
 * **Variable Check**: The ingestion script MUST verify the presence of `Condition` (Rejection vs. Control), `ReactionTime`, and `Mood` columns. If `Condition` or `Mood` is missing, the dataset is rejected, and the pipeline halts (FR-001).

2. **Reward Dataset**:
 * **Status**: **Removed**. No verified reward dataset exists that can be linked to ds000208. The project no longer attempts to use this dataset.

### Data Availability & Feasibility

* **Openness**: ds000208 is publicly accessible via HuggingFace. No credentials required.
* **Size**: The dataset is a small sample. It will easily fit within 7 GB RAM.
* **Streaming**: Not required for this dataset size, but the code will use `pandas.read_parquet` with memory mapping if needed.
* **Risk**: The primary risk is the **absence of required conditions** (Rejection/Control) in ds000208. The plan handles this by halting with a clear error (FR-001).

## Statistical Methodology

### Design Selection Logic
1. **Check Conditions**: Verify presence of 'Rejection' and 'Control' conditions in ds000208.
2. **If Conditions Present**: Perform **One-Way Repeated Measures ANOVA** (or Paired T-Test) comparing Rejection vs. Control on Mood and RT. **(Actual Path: Expected)**.
3. **If Conditions Missing**: Halt with error.

### Models & Corrections
* **Primary Test**: One-Way Repeated Measures ANOVA (Within-Subjects).
* **Multiplicity**: Benjamini-Hochberg (BH) FDR correction applied to the set of *primary outcome metrics* (Reaction Time and Mood Rating).
* **Sensitivity**: Sweep α ∈ {0.01, 0.05, 0.1} (FR-006).
* **Assumptions**:
 * *Normality*: Checked via Shapiro-Wilk (if N > 30).
 * *Sphericity*: Checked via Mauchly's test (if ANOVA used).
 * *Causality*: All claims framed as **associational** (Constitution Principle VI). No causal language in Results.

### Power & Sample Size
* **Constraint**: N ≤ 500 (Spec FR-005).
* **Limitation**: The plan does **not** include a Power Analysis Report (T043 was rejected as scope creep). However, the report will include a "Limitations" section noting the sample size and the resulting power constraints.

## Compute Feasibility

* **Platform**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
* **Strategy**:
 * **CPU-First**: All statistical tests (ANOVA) are CPU-tractable. No GPU required.
 * **Memory**: Data loading uses `pandas` with chunking if necessary (though dataset is small).
 * **Time**: < 1 hour for full pipeline.
* **GPU Escape Hatch**: Not needed. No deep learning or transformer models are used.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Required conditions missing in ds000208 | Critical (Hypothesis untestable) | Strict validation (FR-001). Pipeline halts with clear error. No fabrication. |
| Memory overflow | Medium (Job failure) | Pre-load size estimation and `pandas` memory optimization. |
| Convergence failure (Small N) | Low | Report convergence warnings and confidence intervals. |
| API Unreachable (T015a) | High (Pipeline halt) | T015a halts immediately if API fails. No partial downloads. |

## Decision Rationale

* **Dataset Choice**: Only ds000208 is verified and sufficient for the revised hypothesis. ds003392 is removed from the plan.
* **Statistical Approach**: ANOVA is chosen for its simplicity and CPU efficiency. FDR is mandatory per FR-004.
* **Design Flexibility**: The pipeline dynamically selects the test based on condition availability, satisfying FR-007 and FR-008.
* **Scope**: Power analysis (T043) is excluded as it is not in the spec.
