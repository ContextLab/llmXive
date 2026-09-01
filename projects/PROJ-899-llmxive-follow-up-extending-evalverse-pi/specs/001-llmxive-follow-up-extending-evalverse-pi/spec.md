# Specification: llmXive Feature Distillation

## Overview
This specification defines the requirements for extending the EvalVerse dataset analysis with CPU-tractable feature distillation. The goal is to determine which video dimensions can be accurately predicted using low-level features (optical flow, audio) versus those requiring expensive VLMs. All metrics (correlations, baselines, memory usage) MUST be derived from REAL measurements on the provided EvalVerse dataset; no simulated, placeholder, or hardcoded metrics are permitted.

## User Stories

### US1: Dimensional Viability Analysis
As a researcher, I want to calculate the correlation between low-level features and EvalVerse expert-calibrated VLM scores so that I can identify which dimensions are "feature-sufficient" (r ≥ 0.85) and which require VLMs.

**Acceptance Criteria:**
- Pearson and Spearman correlations calculated with 95% confidence intervals via bootstrapping (1,000 iterations). (See FR-004, FR-007, SC-001, Anchored to US1)
- Dimensions flagged as "feature-sufficient" or "VLM-required" based on the logic in FR-008 (See FR-008, Anchored to US1).
- Baseline comparisons (Mean, Shuffled) included.
- Decision rule: Flag as "feature-sufficient" if r ≥ 0.85 AND lower bound of 95% CI ≥ 0.70; otherwise "VLM-required". (See FR-008, Anchored to US1)
- Rationale: The threshold r ≥ 0.85 is a community-standard for "high" correlation in feature distillation, and the CI check ensures statistical robustness against sampling noise.

### US2: Compute Feasibility Profiling
As a system administrator, I want to profile the memory and time usage of the pipeline so that I can verify it runs within 7GB RAM and 6 hours for 10k clips.

**Acceptance Criteria:**
- Peak memory tracked per clip.
- Empirical profiling of per-clip time and memory, with total time projection for 10k clips based on measured averages (linear extrapolation).
- Gate fails if any single clip exceeds 7GB peak memory or if projected total time > 6 hours. Failure MUST produce exit code 1 and a specific log message "GATE FAILED: Resource constraint violated". (See FR-006, SC-001, SC-002, Anchored to US2)

### US3: Sensitivity Analysis
As a methodologist, I want to sweep classification thresholds on the correlation value r (including high-confidence values) so that I can verify the robustness of the "feature-sufficient" decision boundary.

**Acceptance Criteria:**
- Flip rate calculated for each dimension across thresholds.
- Full sensitivity matrix generated (See FR-005, SC-004, Anchored to US3).

## Functional Requirements
- **FR-004**: Correlation calculation with bootstrapping (1,000 iterations) for Pearson and Spearman coefficients. (See US1, Anchored to US1)
- **FR-005**: Threshold sensitivity analysis: sweep thresholds {0.70, 0.75, 0.80, 0.85, 0.90} and report flip rates. (See US3, Anchored to US3)
- **FR-006**: Linear scaling validation: measure per-clip time/memory and project total for 10k clips. (See US2, Anchored to US2)
- **FR-007**: 95% bootstrap confidence interval calculation (n=1000) for correlation coefficients. (See US1, Anchored to US1)
- **FR-008**: Dimension classification logic: flag "feature-sufficient" if r ≥ 0.85 and lower 95% CI ≥ 0.70; else "VLM-required". (See US1, Anchored to US1)
- **FR-009**: Feature-sufficiency validation gate: reject dimensions where the lower bound of the 95% CI drops below 0.70 OR r < 0.85. Output exit code 1 if any dimension fails this gate ONLY if the 'strict-mode' configuration flag is enabled; otherwise, flag the dimension as "VLM-required" and continue. (See US1, Anchored to US1)

## Non-Functional Requirements
- **SC-001**: CPU-only execution. (Anchored to US2)
- **SC-002**: Peak memory per clip < 7GB. (See US2, Anchored to US2)
- **SC-003**: Reproducibility (fixed seeds, explicit URLs).
- **SC-004**: Methodological verification: generate sensitivity matrix sweeping thresholds {0.70, 0.75, 0.80, 0.85, 0.90} and report flip rates per dimension. (See US3, Anchored to US3)

## Assumptions
- EvalVerse dataset is available with expert-calibrated VLM scores.
- Low-level features (optical flow, audio) are pre-computed or computable within the resource constraints.
- The "feature-sufficient" classification is strictly based on the correlation with VLM scores, not human expert scores.