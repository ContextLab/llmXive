# Specification: Investigating the Effectiveness of Loss Functions on Small-World Graphs

## Overview
This project investigates whether contrastive learning (InfoNCE) converges faster than supervised learning (Cross-Entropy) as graph connectivity ($\beta$) increases in Watts-Strogatz small-world networks.

## Functional Requirements

### FR-001: Sample Size
The study will generate **110** synthetic graphs (10 per $\beta$ level from 0.0 to 1.0). This sample size is derived from a power analysis targeting a moderate interaction effect ($f^2=0.15$) with 80% power.

### FR-005: Convergence Threshold
Convergence is defined as achieving validation accuracy **≥ 0.90**. If this threshold is not met within the maximum epoch limit, the run is flagged as censored.

### FR-006: Statistical Analysis (Tobit)
Primary analysis uses **Tobit Regression** to model convergence steps as a function of loss type, $\beta$, and their interaction, handling censored data points.

### FR-007: Statistical Analysis (Cox)
Secondary analysis uses **Cox Proportional Hazards** survival analysis to model the "time" (epochs) to convergence.

### FR-008: Interaction Focus
The analysis focuses exclusively on the interaction terms from Tobit and Cox models. Correlation coefficients are not required.

## Success Criteria

### SC-003: Analysis Results Output
The final analysis output must be saved to `data/analysis_results.json`.
This JSON file must contain:
- `tobit_interaction_p_value`: float
- `cox_interaction_p_value`: float
- `is_significant`: boolean
 - **Definition**: This field is `true` if the Bonferroni-corrected interaction p-value (minimum of Tobit and Cox) is less than 0.05. Otherwise, it is `false`.

## User Stories

### US-1: Synthetic Graph Generation
As a researcher, I want to generate 110 Watts-Strogatz graphs with annotated community labels so that I can have a controlled dataset with varying connectivity.
**Acceptance Scenario 1**:
Given the power analysis output N=110,
When the generation script runs,
Then `data/raw/graphs.jsonl` contains exactly 110 entries with balanced $\beta$ distribution (10 per level) and valid clustering coefficients.

### US-2: Dual-Loss Training
As a researcher, I want to train GCNs with Cross-Entropy and InfoNCE losses to compare their convergence speeds.
**Acceptance Scenario 1**:
Given a graph with $\beta=0.1$,
When training runs with both losses,
Then two model files and trajectory logs are saved, and convergence steps are recorded (or flagged as censored if accuracy < 0.90).

### US-3: Statistical Interaction Analysis
As a researcher, I want to analyze the interaction between loss type and $\beta$ to determine if contrastive learning benefits from small-world topology.
**Acceptance Scenario 1**:
Given the training logs from 220 runs,
When the analysis script runs,
Then `data/analysis_results.json` is generated with Tobit/Cox coefficients and a boolean `is_significant` flag indicating the presence of an interaction effect.

## Data Model
Refer to `data-model.md` for entity definitions (SyntheticGraph, TrainingRun, AnalysisResult).

## Contracts
Refer to `contracts/` for JSON schemas.