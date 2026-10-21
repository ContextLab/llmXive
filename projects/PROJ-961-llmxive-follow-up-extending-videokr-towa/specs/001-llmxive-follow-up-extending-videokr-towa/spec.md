# Specification: Video Reasoning Threshold Analysis
**Project**: llmXive follow-up: extending "VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understanding"
**Version**: 1.2 (Revised)
**Date**: 2023-10-27
**Status**: Active

## 1. Overview

This specification defines the requirements for analyzing the "reasoning cliff" in video question answering tasks. The goal is to determine if there is a statistically significant drop in accuracy as the complexity (measured by graph hop count) of the required reasoning increases.

## 2. User Stories

### US1: Data Ingestion and Structural Annotation
As a researcher, I want to download the VideoKR‑SFT dataset and annotate each question with the exact shortest‑path hop count from the ground‑truth knowledge graph, so that I can stratify performance by reasoning complexity.

### US2: Accuracy Stratification, Threshold Detection, and Model‑Based Evaluation
As a researcher, I want to calculate accuracy per hop‑bin, detect a non‑linear "reasoning cliff" using both a permutation change‑point test **and** a likelihood‑ratio test (LRT) between linear and piecewise‑linear models, and train a text‑only logistic regression model to predict correctness, so that I can quantify the threshold where reasoning capability breaks down and validate it against a predictive baseline.

### US3: Sensitivity Analysis of Threshold Definition
As a researcher, I want to verify the robustness of the detected "cliff" by sweeping threshold definitions and by controlling for plausible confounds (question difficulty, video length, answer type), so that I can ensure the finding is not an artifact of a specific binning choice or omitted variable bias.

### US4: Runtime Monitoring
As a researcher, I want the pipeline to log total end‑to‑end runtime and automatically compare it against a predefined continuous‑integration (CI) runtime limit, so that I can enforce reproducibility constraints in automated testing environments.

### US5: Memory Usage Monitoring
As a researcher, I want the pipeline to record peak memory consumption and compare it against a CI memory limit (7 GB), so that resource usage stays within CI sandbox constraints.

## 3. Functional Requirements

### FR-001: Data Annotation
The system must ingest the VideoKR‑SFT dataset and the associated Knowledge Graph, and produce an annotated CSV that conforms to the project's schema contract (`contracts/annotated_questions.schema.yaml`).  
- Output: `data/processed/annotated_videokr.csv`  
- Columns (exactly as required by the **updated** schema):  
  - `question_id` (string)  
  - `question_text` (string)  
  - `answer_text` (string)  
  - `chain_length` (integer, 1, 2, 3…) – shortest‑path hop count  
  - `status` (string, e.g., `"annotated"`)

*Note*: The `predicted_correctness` column required by the original schema is omitted here; it will be added later by the predictive‑model step (FR‑010) after the annotation stage. The schema file will be revised accordingly (see FR‑012).

### FR-002: Binning Strategy
The system must generate a separate file containing the categorical **hop_bin** for each question.  
- Output: `data/processed/chain_bins.csv`  
- Columns: `question_id`, `hop_bin` (categorical values `'1'`, `'2'`, `'3+'` where all hop counts ≥ 3 are aggregated).  
- Logic: Aggregate hop counts ≥ 3 into the `'3+'` category. (See US1)

### FR-003: Stratified Accuracy
The system must calculate accuracy rates for each hop‑bin (1‑hop, 2‑hop, 3+).  
- Output: `data/processed/accuracy_binned.png`, `data/processed/accuracy_binned.csv`.  
- Constraint: If a bin contains **fewer than the sample size determined by FR‑011** (minimum required per‑bin n), the system must flag the bin for merging or defer the statistical test for that bin. (See US1)

### FR-004: Threshold Detection (Permutation Test & Logistic‑Regression LRT)
The system must detect the optimal “knot” (threshold hop count) where accuracy drops significantly.  

- **Permutation Test**: Operates on raw per‑sample correctness labels (binary 0/1), not on aggregated bin means. Perform a non‑parametric change‑point test with a sufficiently large number of permutations.  

- **Likelihood‑Ratio Test (LRT)**: Fit a **logistic regression** (binomial GLM) of correctness vs. hop count as the null model, and a piecewise‑logistic model with a knot at each candidate location (1 – 5). Compare models with an LRT to obtain a p‑value.  

- Grid Search: Evaluate knot locations across the early portion of the range up to five.  
- Multiple‑Comparison Correction: Apply Bonferroni correction across the five knot tests.  
- Output: `data/processed/threshold_results.json` containing both permutation‑test and LRT p‑values, the selected knot, and significance flags. (See US2)

### FR-005: Continuous Visualization
The system must generate a continuous plot of accuracy vs. hop count to visualize the trend without binning artifacts.  
- Output: `data/processed/accuracy_vs_hop_raw.png`.  
- Method: Scatter plot of raw binary correctness against hop count with a LOESS smooth trend line.  
- Output Data: `data/processed/accuracy_vs_hop_raw.csv`. (See US2)

### FR-006: Runtime Measurement
The system must log the total end‑to‑end runtime of the pipeline and compare it against the CI runtime limit (i.e., the predefined maximum allowable duration). Runtime monitoring is essential for reproducible research pipelines and to respect CI sandbox constraints.  
- Output: `data/processed/runtime_log.json` containing fields `total_seconds` and `limit_exceeded` (boolean). (See US4)

### FR-007: [REMOVED] Generalized Additive Models (GAM)
**STATUS**: REMOVED.  
**Reason**: The Plan’s “Complexity Tracking” table explicitly rejects GAMs for this task due to statistical invalidity on discrete ordinal variables (hop counts). The permutation test and LRT are the approved methodologies for non‑linearity detection. (Retained for traceability; not active.)

### FR-008: Sensitivity Analysis of Threshold Definition
The system must repeat the threshold detection (both permutation test and LRT) under three alternative binning schemes (e.g., `[initial,2,3+]`, `[initial,2,3,4+]`, `[initial,2,3,4,5+]`) and report the stability of the selected knot.  
- Output: `data/processed/sensitivity_analysis.json` with per‑scheme knots and significance flags. (See US3)

### FR-009: Memory Usage Logging
The system must record peak memory consumption during execution and compare it against the CI memory limit. Memory monitoring is required to guarantee that the pipeline can run within the limited resources of CI environments, ensuring reproducibility.  
- Output: `data/processed/memory_log.json` containing fields `peak_gb` and `limit_exceeded` (boolean). (See US5)

### FR-010: Predictive Model & Likelihood‑Ratio Evaluation
The system must train a logistic regression model using only text‑only features (e.g., TF‑IDF of question and answer) to predict correctness, and evaluate whether adding hop‑count as a predictor significantly improves fit via an LRT.  
- Steps:  
  1. Train baseline model on text features.  
  2. Train extended model adding `chain_length` as an additional feature.  
  3. Perform LRT between baseline and extended models.  
- Output: `data/processed/model_lrt_results.json` with LRT statistic, p‑value, and conclusion. (See US2)

### FR-011: Power Analysis for Per‑Bin Sample Size
Before conducting statistical tests, the system must perform a power analysis to determine the minimum number of samples required per hop‑bin to detect an effect size of **0.1** with **80 % power** at **α = 0.05** (two‑sided).  
- The computed minimum n is recorded in `data/processed/power_analysis.json` and used by FR‑003 to validate bin adequacy. (See US1)

### FR-012: Covariate Extraction for Confound Adjustment
The system must extract the following covariates for each question to enable confound‑adjusted analyses required by SC‑006 and SC‑003:  
- **question_difficulty** (float, 0–1): sourced from the dataset’s `difficulty_score` column.  
- **video_length_seconds** (float): sourced from accompanying video metadata file `metadata/video_lengths.csv`.  
- **answer_type** (categorical, `"multiple_choice"` or `"open_ended"`): derived from the answer format field in the original dataset.  
These covariates are added to `data/processed/annotated_videokr.csv` (as new columns) and are used in the adjusted LRTs.  

## 4. Data Model

### 4.1 Input Data
- **VideoKR‑SFT**: A CSV/JSONL dataset of video questions, answers, and correctness labels, including `difficulty_score` and answer format fields.  
- **Knowledge Graph**: A graph structure (nodes and edges) representing entities and relationships required for reasoning.  
- **Video Metadata**: `metadata/video_lengths.csv` containing `video_id` and `length_seconds`.

### 4.2 Annotated Output
- **CSV**: `data/processed/annotated_videokr.csv` (see FR‑001, FR‑012).  
- **Bin Mapping**: `data/processed/chain_bins.csv` (see FR‑002).  
- **Stratified Accuracy Visuals**: `data/processed/accuracy_binned.png` and `data/processed/accuracy_binned.csv` (see FR‑003).  
- **Raw Accuracy Visuals**: `data/processed/accuracy_vs_hop_raw.png` and `data/processed/accuracy_vs_hop_raw.csv` (see FR‑005).  

## 5. Success Criteria

### SC-001: Annotation Coverage
- Log total input records, unresolvable count, and annotated count.  
- Output: `data/processed/annotation_coverage.json`. (See US1)

### SC-002: Threshold Significance
- Explicitly compare calculated p‑values (both permutation test and LRT) against **α = 0.05**.  
- Output: `data/processed/threshold_results.json` with `is_significant` boolean and `conclusion` string. (See US2)

### SC-003: Robustness Verification (Binning & Confounds)
- Verify that the “cliff” remains significant (p < 0.05) in **≥ 2 of 3** binning schemes **and** after controlling for question difficulty, video length, and answer type (via covariate‑adjusted LRT).  
- Output: `data/processed/stability_metric.json` with `robustness_status` (`PASS`/`FAIL`). (See US3)

### SC-004: Runtime Compliance
- Measure total runtime and compare against the CI runtime limit of **7200 seconds**; set `limit_exceeded` flag accordingly.  
- Output: `data/processed/runtime_log.json`. (See US4)

### SC-005: Memory Compliance
- Measure peak memory usage and compare against the CI memory limit of **7 GB**; set `limit_exceeded` flag accordingly.  
- Output: `data/processed/memory_log.json`. (See US5)

### SC-006: Extended Confound Robustness
- Perform additional regression analyses including covariates for question difficulty (float), video length (seconds), and answer type (categorical). Confirm that the identified knot remains significant after adjusting for these covariates (p < 0.05).  
- Output: `data/processed/confound_adjusted_lrt.json` with adjusted LRT results. (See US3)

## 6. Methodology Notes

### 6.1 Change‑Point Detection
The project employs **both** a permutation‑based change‑point test (operating on raw binary correctness) and a **logistic‑regression** likelihood‑ratio test (LRT) comparing a null logistic model to a piecewise‑logistic model. This dual approach satisfies Constitution VII (mandatory LRT) while providing a non‑parametric robustness check.

### 6.2 Handling Small Bins
If a bin contains fewer samples than the minimum required by the power analysis (FR‑011), the system will attempt to merge it with the adjacent bin. Should the merged bin still fall below the required n, the statistical test for that bin is deferred and logged.

### 6.3 Predictive Baseline Model
A logistic regression model using only textual features serves as a baseline. Adding hop count as a predictor tests whether structural reasoning information provides additional explanatory power, evaluated via LRT (FR‑010).

### 6.4 Runtime & Memory Limits
- **CI runtime limit**: 7200 seconds (2 hours).  
- **CI memory limit**: 7 GB.  

These limits are enforced by FR‑006 and FR‑009 respectively and are justified as essential for reproducible CI‑based research pipelines.

## 7. Revision History

| Version | Date | Author | Changes |
|:--- |:--- |:--- |:--- |
| 1.0 | 2023-10-20 | Research Team | Initial draft including FR‑007 (GAM). |
| 1.1 | 2023-10-27 | Research Team | Removed FR‑007 to align with Plan's Complexity Tracking table (Resolves F001). |
| 1.2 | 2023-10-27 | Research Team | Added missing FR/SC links, defined CI limits, introduced power analysis, reinstated FR‑007 as removed for traceability, added FR‑008‑012, SC‑006, and predictive‑model requirement to satisfy methodological and scientific‑soundness concerns. |
| 1.3 | 2023-10-27 | Research Team | Fixed internal consistency (removed `predicted_correctness` from FR‑001), unified naming to `hop_bin`, added covariate extraction FR‑012, replaced linear model with logistic regression in FR‑004, justified runtime and memory monitoring, expanded Data Model with missing visual artefacts. |