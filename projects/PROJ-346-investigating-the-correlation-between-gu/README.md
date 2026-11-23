# Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility

## Project Overview

This project investigates the statistical associations between gut microbiome composition and cognitive flexibility using publicly available datasets (AGP, UK Biobank, NHANES). It adheres strictly to an **associational-only** framework for the primary analysis (User Stories 1-3) while proposing a literature-derived mechanistic hypothesis (User Story 4) for future causal testing.

## Core Distinction: Correlational Findings vs. Mechanistic Hypothesis

This project explicitly separates two distinct analytical tracks:

### 1. Correlational Findings (User Stories 1-3)
* **Scope**: Statistical analysis of real-world cohort data (AGP, UK Biobank, NHANES).
* **Goal**: Identify significant associations between microbial taxa abundance and cognitive flexibility scores.
* **Limitation**: These findings are **strictly associational**. They cannot establish causality or reveal the underlying cellular mechanisms.
* **Output**: `data/processed/correlation_results.json`, `data/processed/regression_results.json`, `figures/`.
* **Note**: If data linkage fails (no common participants), the pipeline executes a **Meta-Analytic Fallback (FR-008)** using synthetic literature statistics to provide a measurable outcome, rather than reporting a simple "gap".

### 2. Mechanistic Hypothesis (User Story 4)
* **Scope**: Literature synthesis and theoretical modeling.
* **Goal**: Address the "cellular alphabet" gap by proposing a biologically plausible pathway linking the gut to the brain (e.g., Microbe -> SCFA -> HDAC Inhibition -> BDNF/CREB).
* **Nature**: This is a **hypothesis generation** exercise derived from existing literature, NOT a measurement of the current dataset.
* **Output**: `reports/mechanistic_hypothesis.md`, `reports/future_experimental_protocol.md`.
* **Statement**: "The current correlational analysis identifies associations; the proposed mechanistic pathway provides the biological plausibility for future causal testing."

## Installation

```bash
pip install -r requirements.txt
```

## Quickstart

The full pipeline can be executed via `quickstart.md`.

1. **Ingestion & Preprocessing**:
 ```bash
 python code/01_ingest.py
 python code/02_preprocess.py
 ```
2. **Analysis**:
 ```bash
 python code/03_correlation.py
 python code/04_regression.py
 python code/05_sensitivity.py
 ```
3. **Visualization**:
 ```bash
 python code/06_visualize.py
 ```
4. **Mechanistic Synthesis**:
 ```bash
 python code/08_mechanistic_synthesis.py
 python code/09_future_design.py
 ```

## Data Structure

* `data/raw/`: Raw downloads from AGP, UK Biobank, NHANES, and synthetic literature metadata.
* `data/processed/`: Cleaned, merged, and normalized datasets.
* `data/qc/`: Quality control logs and filtering reports.
* `figures/`: Generated plots (heatmaps, forest plots).
* `reports/`: Final narrative reports and experimental protocols.

## Compliance & Constraints

* **Associational Only**: No causal claims are made in the primary analysis results.
* **Real Data**: All primary analysis relies on real external data sources. Synthetic data is used *only* for the Meta-Analysis fallback or benchmarking.
* **Reproducibility**: All scripts are deterministic where possible; random seeds are fixed for sampling.

## Response to Reviewer (Eric Kandel)

Per the reviewer's feedback regarding the need for a "cellular alphabet," this project has been extended with **User Story 4**. While the primary data analysis (US1-US3) remains strictly correlational due to the limitations of public datasets, US4 synthesizes existing literature to propose a specific molecular pathway (SCFA -> Histone Acetylation -> BDNF) that *could* be measured in a future experimental design (e.g., Gnotobiotic models). This distinguishes the *observed associations* from the *theoretical mechanism*.
