# Specification: llmXive Follow-up - Extending Trust-Region Behavior Blending

## Overview
This project extends the Trust-Region Behavior Blending (TRB) methodology for on-policy distillation by introducing **static diversity profiles** to predict model behavior stability and collapse without requiring ground-truth sweep logs.

## Context
The original TRB approach relies on sweep logs (optimal epsilon_0 per instance) to train a collapse predictor. However, for the target datasets (Book Corpus and BEIR), these ground-truth sweep logs are unavailable. This specification defines a **proxy strategy** to achieve the research goals using available data signals.

## Functional Requirements (FR)

### FR-001: Feature Extraction
The system must compute lexical and syntactic feature vectors from teacher model outputs (Book Corpus and BEIR) without GPU usage.
- **Metrics**: Distinct-n ratio (n=4), N-gram entropy, Parse tree depth variance.
- **Constraint**: Must run on CPU-only infrastructure.

### FR-002: Proxy-Based Collapse Prediction (AMENDED)
**Original Intent**: Predict "collapse" based on ground-truth optimal epsilon.
**Amended Strategy**: Since ground-truth sweep logs are unavailable, the system shall predict "proxy collapse" defined as **"low relevance" (for BEIR)** or **"short text length" (for Book Corpus)**.
- The system must correlate diversity profiles with these proxy targets.
- "Collapse" in downstream logic will refer to instances exhibiting low proxy scores (low relevance/short length).
- **Success Criteria**: A statistically significant correlation (p < 0.05, |r| > 0.2) must be established between diversity metrics and the proxy target.

### FR-003: Static Profile Generation
Generate a static diversity profile for each document in the source dataset to be used as input for correlation analysis.

### FR-004: Proxy Stability Forecasting (AMENDED)
**Original Intent**: Forecast model stability using ground-truth collapse labels.
**Amended Strategy**: Forecast **"proxy stability"** defined as the **variance of relevance scores** (for BEIR) or **variance of text lengths** (for Book Corpus) within a sampled batch.
- The system must predict whether a batch will exhibit high or low proxy variance based on the mean diversity profile of the batch.
- **Success Criteria**: The forecasted stability must correlate with observed variance in the target domain.

### FR-005: Cross-Domain Generalization
Apply correlation coefficients derived from the source domain (Book Corpus) to the target domain (BEIR) without re-training.
- Validate if static diversity profiles generalize across domains.

### FR-006: Statistical Significance Validation
Use permutation tests to validate that observed correlations are not due to random chance against the null distribution of the proxy target.

### FR-007: Proxy Stability Correlation (AMENDED)
**Original Intent**: Correlate diversity with ground-truth stability.
**Amended Strategy**: Correlate diversity metrics with **proxy stability** (relevance score variance).
- The system must demonstrate that high syntactic variation correlates with higher proxy stability (or vice versa, as determined by data).

## Success Criteria (SC)

### SC-001: Baseline Performance
The diversity-based ranking must outperform a mean-proxy baseline (predicting the average proxy value for all instances).

### SC-002: Proxy FPR Measurement (AMENDED)
**Original Intent**: Measure False Positive Rate for "collapse prediction" against ground truth.
**Amended Strategy**: Since ground-truth collapse labels are missing, measure **False Positive Rate for "proxy collapse" prediction**.
- Define "Proxy Collapse" as instances below the 20th percentile of the proxy target (relevance/length).
- Record the FPR of the diversity-based classifier against this proxy binary label.
- **Documentation**: Explicitly state in reports that SC-002 refers to *proxy* FPR, not ground-truth collapse FPR.

### SC-003: Computational Efficiency
Total runtime for feature extraction and correlation analysis must be under 6 hours on CPU-only runner.

### SC-004: Permutation Test Validation
The permutation test must confirm that the source-domain correlation is statistically significant (p < 0.05) against the null distribution of the proxy target.

### SC-005: Generalization Gap
The drop in correlation performance when applying source logic to target data must be within an acceptable threshold (defined as < 20% relative drop).

### SC-006: Proxy Stability Forecast Accuracy (AMENDED)
**Original Intent**: Accuracy of forecasting ground-truth stability.
**Amended Strategy**: Accuracy of forecasting **proxy stability** (variance of relevance scores).
- Measure the correlation between predicted stability (from diversity features) and observed variance in the target domain.

## Data Model Constraints
- **Source Data**: `tr-books-tokenized` (Book Corpus), `Tr-beir-formatted` (BEIR).
- **Proxy Targets**:
 - Book Corpus: `text_length` (number of tokens).
 - BEIR: `relevance_score` (from dataset metadata).
- **Missing Data**: No `optimal_epsilon_0` or `collapse_label` fields exist in the source datasets. All logic must adapt to proxy targets.

## Risk Mitigation
- **Risk**: Proxy targets (text length/relevance) may not correlate with actual model collapse.
- **Mitigation**: If T023 (Scope Gap Report) confirms no valid proxy correlation (|r| < 0.2 or p > 0.05), the project halts Phase 5 and reports the scope gap. No synthetic data or ground-truth fabrication is permitted.

## Version History
- v1.0: Initial draft.
- v1.1 (Current): Amended FR-002, FR-004, FR-007, SC-002, SC-006 to reflect proxy strategy.