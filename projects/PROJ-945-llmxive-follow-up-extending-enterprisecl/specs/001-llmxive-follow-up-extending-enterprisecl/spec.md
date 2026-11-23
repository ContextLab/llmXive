# EnterpriseClawBench Extension Specification

## Overview
This document defines the scope and requirements for extending the EnterpriseClawBench benchmark
to evaluate lightweight correction adapters for enterprise LLM failures.

## User Stories

### US1: Syntactic & Pragmatic Feature Extraction
As a researcher, I want to extract syntactic and pragmatic features from raw enterprise logs
so that I can identify patterns distinguishing successful from failed traces.

### US2: Lightweight Adapter Training
As a developer, I want to train a lightweight classifier on feature triplets
so that I can predict whether a failure is correctable without fine-tuning large models.

### US3: Artifact Delivery Score Evaluation
As a stakeholder, I want to evaluate the impact of the adapter on the Artifact Delivery Score
so that I can quantify the practical value of the correction policy.

## Functional Requirements

### FR-001: Ground Truth Verification
The system must verify the existence and integrity of initial success/failure ground truth labels
in the raw dataset. A validation report must be generated with pass/fail status.

### FR-002: Semantic Outcome Oracle
The system must implement a rule-based oracle to derive "correctable" labels from error types
without using manual labels or LLM-based judgments.

### FR-003: Lightweight Feasibility Classifier
The system must implement a scikit-learn classifier (Random Forest or Logistic Regression)
for feasibility prediction. The model must be CPU-only and trained on feature triplets.
The exclusion of Llama-3-8B is removed as it is no longer relevant to the corrected scope.

### FR-004: Convergence Fallback
If the training loop fails to converge, the system must trigger a rule-based syntax correction
script to generate fallback predictions.

### FR-005: Statistical Significance
The system must perform statistical analysis (McNemar's, t-test, or Wilcoxon) to determine
if the adapter significantly improves the Artifact Delivery Score.

### FR-007: Resource Constraints
All components must adhere to strict memory constraints (peak RSS < 7GB) and runtime limits.
Streaming and chunked processing must be used where appropriate.

## Non-Functional Requirements

### NF-001: Reproducibility
All experiments must be reproducible with fixed seeds and deterministic logic.

### NF-002: Modularity
Components must be modular and independently testable.

### NF-003: Documentation
All code must be documented, and a final evaluation report must be generated.

## References
- EnterpriseClawBench Dataset Documentation
- Scikit-learn Documentation
- Statistical Analysis Guidelines for LLM Evaluation