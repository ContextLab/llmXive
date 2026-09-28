# Research: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Overview

This research document outlines the methodology, dataset strategy, and statistical rigor for predicting *synthetic* polymer degradation pathways using a lightweight GNN. It addresses the spec's requirements for data ingestion, model training, feature attribution, and validation while adhering to the project constitution's principles of reproducibility, data hygiene, and computational feasibility. **Critical Note**: The model predicts a *synthetic* distribution derived from chemical priors, not real-world degradation mechanisms. Findings are simulation-based associations and cannot be used for real polymer design without experimental validation.

## Dataset Strategy

### Verified Sources

The project relies on the following verified datasets (per the "Verified datasets" block):

- **SMILES (parquet)**: `
 *Rationale*: Contains ~700k SMILES strings; can be filtered for polyesters using functional group detection (ester bonds: `C(=O)O`). Estimated to yield a substantial set of polyester records after filtering.
- **SMILES (parquet)**: `
 *Rationale*: Test set for validation; can be used to verify model generalization.
- **SMILES (csv)**: `
 *Rationale*: Alternative SMILES source; may contain polymer-specific entries.

**Note**: The NIST Chemistry WebBook and Materials Project APIs are mentioned in the spec, but no verified URLs are provided in the "Verified datasets" block. Therefore, the plan will **attempt** to fetch from these APIs (with backoff) but will fall back to verified HuggingFace datasets if they fail.

### Dataset Limitations & Mitigations

- **Missing degradation labels**: All records from verified sources lack explicit degradation pathway labels. The system will:
 - Apply a synthetic label distribution (e.g., dominant hydrolysis, moderate oxidation, minor photolysis) based on literature priors.
 - Flag all records for manual curation (FR-008).
 - If ALL records are flagged, the system proceeds with synthetic labels but logs a "No Ground Truth" warning.
 - If N=0 after filtering, the system halts with a fatal error.
- **Small dataset size**: The verified SMILES datasets may yield a substantial number of polyester records after filtering. The system will:
 - Perform a power analysis (SC-004) using G*Power simulation (target power ≥0.8).
 - If n<150, switch to leave-one-out (LOO) validation (FR-009).
 - Trigger a power analysis warning in the report.
- **Environmental conditions**: Verified datasets lack temperature, pH, UV values. The system will:
 - Impute missing values with documented defaults (e.g., pH 7, 25°C, no UV) (FR-002).
 - Flag imputed records in metadata.

### Data Ingestion Pipeline

1. **Download**: Fetch verified SMILES datasets via `datasets.load_dataset()` (streaming if large).
2. **Filter**: Retain only polyester records using RDKit to detect ester bonds (`C(=O)O`).
3. **Label**: Apply synthetic labels or flag for manual curation.
4. **Impute**: Fill missing environmental conditions with defaults; log actions.
5. **Validate**: Check for valid SMILES, numeric parameters, and labels (SC-006).
6. **Save**: Write raw and processed datasets to `data/raw/` and `data/processed/` with checksums.

## Model Strategy

### Architecture

- **Type**: Graph Neural Network (GNN) with ≤3 layers, hidden dimension ≤128 (FR-003).
- **Layers**: 3 Graph Convolutional (GCN) or Graph Attention (GAT) layers.
- **Features**:
 - Node features: Atom type, degree, hybridization, formal charge.
 - Edge features: Bond type, conjugation, aromaticity.
 - Global features: Temperature, pH, UV (imputed if missing).
- **Output**: Softmax probabilities for 3 degradation classes (hydrolysis, oxidation, photolysis).

### Training Protocol

- **Validation**: 5-fold cross-validation (or LOO if n<150) (FR-009, SC-001).
- **Augmentation**: Edge dropout and subgraph sampling to expand dataset by **exactly 2x** (FR-004, SC-009).
- **Runtime**: ≤30 minutes for augmentation; ≤6 hours for training (SC-003).
- **Metrics**: Macro-F1 score, loss convergence (|loss_t - loss_{t-5}| / loss_{t-5} < 0.05) (SC-001).

### Feature Attribution

- **Method**: Integrated Gradients (FR-005).
- **Target**: Identify structural motifs (e.g., ester linkage, aromatic rings) correlating with *synthetic* degradation pathways.
- **Validation**: Verify ester bonds are in top [deferred] attribution scores for ≥90% of hydrolysis cases (SC-005). **Note**: This validates that the model learned the synthetic rule, not real chemistry.

## Statistical Validation

### χ² Test (Attribution Stability)

- **Purpose**: Validate the *internal consistency* of the model's attribution against a shuffled null (not external scientific truth) (FR-006, SC-002).
- **Method**:
 - Generate null distribution via multiple iterations of shuffled motif importance (from the same model's output).
 - Compare observed motif importance against null using χ² test (α=0.05).
 - Report p-value in final report (SC-011).
 - **Interpretation**: A significant p-value indicates the model's attribution is stable and not random noise, but does not validate the synthetic label as a real-world mechanism.
- **Confidence Flagging**: Flag predictions with softmax probability <0.6 as "low confidence" (SC-008, verified against arXiv 2312.01650).

### Power Analysis

- **Trigger**: If n<150, perform power analysis using G*Power simulation (SC-004).
- **Output**: Warning if power <0.8; report confidence intervals for all metrics (Constitution VII).

## Compute Feasibility

- **CPU-First**: All methods (GNN, Integrated Gradients, χ² test) are tractable on CPU.
- **GPU Escape Hatch**: Not required; lightweight GNN and small dataset fit within 7GB RAM.
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)` for large SMILES files to avoid OOM.

## Decision/Rationale

- **Dataset Choice**: Verified SMILES datasets are the only sources with programmatic access (per "Verified datasets" block). NIST/Materials Project APIs are attempted but fallback to HuggingFace if unavailable.
- **Synthetic Labels**: Necessary due to missing ground truth; aligns with FR-001 and FR-008. **Limitation**: Model learns synthetic distribution, not real mechanisms.
- **CPU Execution**: Lightweight GNN and small dataset fit within CI runner constraints; no GPU needed.
- **Statistical Rigor**: χ² test validates attribution stability; power analysis ensures validity despite small sample size.
- **Scientific Framing**: All findings are framed as "simulation-based associations" and "not causal for real-world design."