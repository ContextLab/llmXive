# Specification: llmXive Feature Distillation

## Overview
This specification defines the requirements for extending the EvalVerse dataset analysis with CPU-tractable feature distillation. The goal is to determine which video dimensions can be accurately predicted using low-level features (optical flow, audio) versus those requiring expensive VLMs.

## User Stories

### US1: Dimensional Viability Analysis
As a researcher, I want to calculate the correlation between low-level features and human expert scores so that I can identify which dimensions are "feature-sufficient" (r ≥ 0.85) and which require VLMs.

**Acceptance Criteria:**
- Pearson and Spearman correlations calculated with confidence intervals

The research question remains: How do the variables relate? The method remains: Pearson and Spearman correlation analysis. References: [Citation]..
- Dimensions flagged as "feature-sufficient" or "VLM-required".
- Baseline comparisons (Mean, Shuffled) included.

### US2: Compute Feasibility Profiling
As a system administrator, I want to profile the memory and time usage of the pipeline so that I can verify it runs within 7GB RAM and 6 hours for 10k clips.

**Acceptance Criteria:**
- Peak memory tracked per clip.
- Linear scaling projection for 10k clips.
- Gate fails if constraints are violated.

### US3: Sensitivity Analysis
As a methodologist, I want to sweep classification thresholds (including high-confidence values) so that I can verify the robustness of the "feature-sufficient" decision boundary.

**Acceptance Criteria:**
- Flip rate calculated for each dimension.
- Full sensitivity matrix generated.

## Functional Requirements
- **FR-004**: Correlation calculation with bootstrapping.
- **FR-005**: Threshold sensitivity analysis.
- **FR-006**: Linear scaling validation.
- **FR-007**: 95% Confidence Interval calculation.
- **FR-008**: Dimension classification logic.
- **FR-009**: VLM proxy validation gate.

## Non-Functional Requirements
- **SC-001**: CPU-only execution.
- **SC-002**: < 7GB RAM usage.
- **SC-003**: Reproducibility (fixed seeds, explicit URLs).
- **SC-004**: Methodological verification (sensitivity matrix).
