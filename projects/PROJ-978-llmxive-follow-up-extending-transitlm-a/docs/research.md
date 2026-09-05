# Research Documentation: llmXive Follow-up

## Overview
This project extends the "TransitLM: A Large-Scale Dataset and Benchmark for Map-Free Transit Ro" research.
The goal is to evaluate a lightweight, encoder-only retrieval-augmented model against the original LLM baseline.

## Key Objectives
1. Identify the "cognitive horizon" where lightweight models diverge from LLMs.
2. Apply statistical significance testing (Kaplan-Meier, Chi-squared) to validate topological limits.
3. Profile resource feasibility on edge devices.

## Data Sources
- **TransitLM SFT Dataset**: Retrieved from Hugging Face.
- **Preprocessing**: Filtering for Chinese cities, vocabulary restriction, and stratification by route length.

## Methodology
- **Lightweight Model**: Deterministic lookup strategy using transition frequencies.
- **Baseline Model**: CPU-quantized LLM (Qwen or similar).
- **Evaluation**: Route validity scoring, Bonferroni-corrected p-values, and survival analysis.

## Deliverables
- `data/analysis/performance_report.json`: Comparison of model performance.
- `data/analysis/survival_analysis_results.json`: Statistical validation of limits.
- `data/analysis/profiling_report.json`: Resource feasibility metrics.

## Execution Flow
1. Setup (T001-T003)
2. Data Download & Preprocessing (T004-T006)
3. Graph Construction & Validation (T007)
4. User Story 1: Performance Thresholds (T012-T017)
5. User Story 2: Statistical Significance (T020-T025)
6. User Story 3: Resource Feasibility (T028-T032)
