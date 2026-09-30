# MobileForge Logic Distillation: Specification

## 1. Introduction

This document outlines the requirements for extending the MobileForge framework with CPU-tractable logic distillation. The goal is to train a lightweight model capable of generating corrective hints and action sequences for Android task automation based on UI states, while adhering to strict resource constraints (CPU-only, <6h training time) and statistical validation standards.

## 2. User Stories

### US-1: Data Extraction and Dataset Construction
As a researcher, I want to extract and filter `(UI_state, Corrective_Hint, Action)` triples from MobileForge logs, ensuring "failed-then-success" trajectories and purely linguistic hints, so that I can train a distilled model on high-quality, coordinate-free reasoning data.

### US-2: CPU-Tractable Model Training
As a researcher, I want to train a lightweight Encoder-Decoder model (e.g., T5-small) on CPU to predict action sequences from UI states and hints, so that I can deploy the model in resource-constrained environments without requiring GPU hardware.

### US-3: Evaluation and Statistical Validation
As a researcher, I want to evaluate the distilled model against a TinyLlama baseline on a representative set of unseen AndroidWorld tasks, performing statistical significance testing with a paired design (McNemar's test), so that I can rigorously validate the performance improvement of the distilled model.

### US-4: Sensitivity Analysis & Robustness
As a researcher, I want to verify the robustness of results against "inconsistency tolerance" threshold variations and perform stress tests, so that I can ensure the model's performance is stable across different evaluation parameters.

## 3. Functional Requirements

### FR-001: Data Pipeline
The system must extract triples from raw logs, filter for "failed-then-success" trajectories, and validate that hints are purely linguistic (no coordinate-based visual grounding).

### FR-002: Model Architecture
The distilled model must utilize an **Encoder-Decoder architecture (e.g., T5-small)**.
*Justification*: While the idea proposed an encoder-only model, the distillation task (UI State + Hint → Action Sequence) is a conditional generation task. Encoder-Decoder architectures (like T5) are the standard for this input-output mapping, avoiding the complexity of adding decoding heads to encoder-only models. Although the baseline (TinyLlama) is Decoder-only, using an Encoder-Decoder for the distilled model is methodologically superior for learning the conditional generation of action sequences from UI states.
*Constraint*: The model must be trainable on CPU within 6 hours and have ≤100M parameters.

### FR-003: Evaluation Dataset
The evaluation must use **N tasks** determined by the output of the A priori power analysis required in **FR-007** (See US-3). The tasks must be logically disjoint from the training set.
*Constraint*: The sample size N is calculated to ensure the study is adequately powered (≥0.8) to detect an effect size of Cohen's h ≥ 0.2, assuming a baseline success rate (p0) of 0.5, with a significance level α = 0.05. This requirement overrides the fixed "500 tasks" mentioned in the initial idea to ensure statistical validity and prevent underpowered studies.

### FR-004: Baseline Comparison
The system must compare the distilled model against a TinyLlama baseline on the exact same set of tracked tasks to enable paired statistical testing.
*Constraint*: The "paired" nature of the data must be established by evaluating the **exact same task instance** (same UI state, same seed) by both models under identical conditions.

### FR-005: Statistical Significance
The system must perform **McNemar's test** for paired binary outcomes (success/fail) to determine statistical significance.
*Justification*: This requirement corrects the idea's proposal of a paired t-test, which is inappropriate for binary data. McNemar's test is the standard for paired nominal data (2x2 contingency table).
*Constraint*: The test assumes a one-tailed alternative hypothesis (distilled model > baseline).

### FR-006: Sensitivity Analysis
The system must perform a sensitivity sweep across "inconsistency tolerance" thresholds to measure variance in success rates.
*Definition*: "Inconsistency tolerance" is defined as the **maximum allowable Levenshtein edit distance** between the generated action sequence and the ground truth.
*Constraint*: A task is considered "successful" within the sweep if the edit distance is ≤ the current threshold. This links the continuous metric to the binary outcome required for the statistical test.

### FR-007: Power Analysis
The system must conduct **A priori power analysis** to determine the required sample size (N) before execution (See US-3).
*Parameters*: The analysis must use a target Power ≥ 0.8, a minimum effect size of Cohen's h ≥ 0.2, a significance level α = 0.05, and an assumed baseline success rate (p0) of 0.5.
*Prohibition*: Post-hoc power analysis is explicitly prohibited.

### FR-008: Resource Constraints
All training and evaluation must run on CPU. Any detection of CUDA usage during training must trigger an immediate failure.

## 4. Non-Functional Requirements

### SC-001: Reproducibility
All experiments must be reproducible via random seed management and artifact versioning (Constitution Principle III).

### SC-002: Data Integrity
Data loaders must fail loudly on missing or corrupted real data; no synthetic fallbacks are permitted.

### SC-003: Performance
Training must complete within 6 hours on a standard CPU runner.

### SC-004: Statistical Rigor
All claims of improvement must be backed by statistically significant results (**p < 0.05, one-tailed**) from appropriate tests (McNemar's) with the alternative hypothesis that the distilled model performs better than the baseline.

### SC-005: Sensitivity Reporting
Sensitivity analysis results must be reported as variance across thresholds, without hard pass/fail cutoffs.

### SC-006: Statistical Power Reporting
Statistical power reporting must document the **a priori power calculation parameters** (Power ≥ 0.8, h ≥ 0.2, p0 = 0.5) and the resulting sample size N (See US-3). Post-hoc power measurements derived from test results are not permitted.

## 5. Data Models

### ExtractionDataset
- `triples`: List of `(UI_state, Corrective_Hint, Action)`
- `metadata`: Source log information, filtering criteria used

### DistilledModel
- `architecture`: Encoder-Decoder (T5-small)
- `weights`: Path to saved model weights
- `config`: Model configuration parameters

### EvaluationResult
- `metrics`: Success Rate, Step Efficiency
- `statistical_test`: McNemar's test p-value
- `power_analysis`: A priori power validation results
- `sensitivity_report`: Variance across thresholds

## 6. Implementation Plan

The implementation is divided into phases:
1. **Setup**: Project structure, dependencies, and state management.
2. **Foundational**: Core infrastructure, power analysis setup, and spec amendments.
3. **US-1**: Data extraction and dataset construction.
4. **US-2**: CPU-tractable model training.
5. **US-3**: Evaluation and statistical validation.
6. **US-4**: Sensitivity analysis and robustness testing.
7. **Polish**: Documentation, cleanup, and final validation.

## 7. Appendix

### A. Justification for Architecture Change (FR-002)
The initial proposal suggested an encoder-only model (e.g., DistilBERT). However, the task involves generating variable-length action sequences (text). Encoder-only models are designed for classification or encoding tasks and cannot natively perform sequence generation without additional decoding heads or complex workarounds. An Encoder-Decoder architecture like T5-small is the standard and most efficient approach for text-to-text generation tasks, making it the correct choice for this distillation pipeline.

### B. Justification for Statistical Test Change (FR-005)
The initial proposal suggested a paired t-test. However, the primary outcome metric is binary (Success/Fail). A t-test assumes continuous data and is inappropriate for binary proportions. McNemar's test is the standard statistical test for paired nominal data (2x2 contingency table), making it the correct choice for comparing the success rates of two models on the same set of tasks.

### C. Justification for Power Analysis Change (FR-007)
Post-hoc power analysis (calculating power after the experiment is done) is tautological and provides no new information; it is mathematically linked to the p-value. A priori power analysis (calculating required sample size before the experiment) is necessary to ensure the study is designed with sufficient sample size to detect a meaningful effect, preventing underpowered studies.