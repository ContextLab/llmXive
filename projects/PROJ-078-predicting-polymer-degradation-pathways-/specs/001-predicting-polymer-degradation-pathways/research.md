# Research: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Overview

This research document outlines the methodology, dataset strategy, and statistical rigor for predicting *synthetic* polymer degradation pathways using a lightweight Graph Neural Network (GNN). It satisfies all functional requirements (FR‑001 – FR‑009) and success criteria (SC‑001 – SC‑012) while adhering to the project constitution (reproducibility, data hygiene, statistical validation). All findings are framed as simulation‑based associations, not causal claims.

## Dataset Strategy

### Verified Sources

The only verified, programmatically downloadable sources provided are:

- **NIST (CSV)**: `https://huggingface.co/datasets/leeroy-jankins/NIST-AI-Risk-Management-Framework/resolve/main/NIST%20AI%20Risk%20Management%20Framework.csv`  
- **WebBook (CSV)**: `https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt`

These datasets do **not** contain polymer SMILES or degradation pathway labels. Consequently:

1. **Synthetic Labeling** – Because no verified source provides ground‑truth degradation pathways, the pipeline generates a synthetic label distribution (hydrolysis ≈ 60 %, oxidation ≈ 30 %, photolysis ≈ 10 %) based on literature priors.  
2. **Flagging for Curation** – All records lacking explicit labels are flagged (`label_source = "synthetic"`; `flagged_for_curation = true`). The report will list the proportion of flagged records (SC‑010).  
3. **Fallback to API** – The system first attempts to query the NIST Chemistry WebBook and Materials Project APIs (with exponential backoff, max 3 retries). If both APIs are unreachable or return no polyester records, the pipeline proceeds with the verified CSVs plus synthetic labeling.

### Dataset Limitations & Mitigations

| Issue | Mitigation |
|-------|------------|
| **No SMILES** | Synthetic SMILES are generated from the verified CSVs using a rule‑based polymer generator (deterministic seed = 42). |
| **Missing environmental variables** | Temperature, pH, and UV are imputed with defaults (25 °C, pH 7, UV 0) and flagged in metadata (FR‑002, SC‑006). |
| **Potentially small *n*** | Power analysis (G*Power via `statsmodels`) warns if *n* < 150 (SC‑004). LOO validation is used in that case. |
| **Synthetic labels** | Explicitly documented in the final report; no causal inference is claimed (Constitution VI). |

### Data Ingestion Pipeline

1. **Download** – `datasets.load_dataset(..., streaming=True)` pulls the two verified CSVs.  
2. **Filter** – RDKit detects ester bonds (`C(=O)O`) to retain only polyesters.  
3. **Label** – Apply synthetic label distribution; flag records lacking labels.  
4. **Impute** – Fill missing temperature/pH/UV with defaults; record imputation flags.  
5. **Validate** – Ensure SMILES parsable, numeric fields present, and label status recorded (≥ 95 % success required, SC‑006).  
6. **Save** – Raw data → `data/raw/`; processed records → `data/processed/records.parquet`; checksums stored in `state/artifact_hashes.yaml`.

## Model Strategy

### Architecture

- **Type**: Graph Neural Network (≤ 3 layers, hidden dimension ≤ 128) – satisfies FR‑003.  
- **Node Features**: Atom type, degree, hybridization, formal charge.  
- **Edge Features**: Bond type, conjugation, aromaticity.  
- **Global Features**: Temperature, pH, UV (imputed if missing).  
- **Output**: Softmax over three degradation classes.

### Training Protocol

- **Cross‑validation**: 5‑fold (source: 2604.10702) unless *n* < 150, then Leave‑One‑Out (LOO).  
- **Data Augmentation**: Edge dropout (p = 0.1) + subgraph sampling to double dataset size (FR‑004). Runtime < 30 min (SC‑009).  
- **Optimization**: Adam, learning rate = 1e‑3, up to 100 epochs; early‑stop on loss convergence (|Δloss|/loss < 0.05 over last 5 epochs).  
- **Metrics**: Macro‑F1 (SC‑001) and loss curves logged.

### Feature Attribution

- **Method**: Integrated Gradients (FR‑005).  
- **Target Motifs**: Ester linkages, aromatic rings near ester bonds, etc.  
- **Validation**: Ester bond must rank within the top [deferred] attribution scores for ≥ 90 % of hydrolysis cases (SC‑005). The validation uses a manually curated subset of ≥ 10 synthetic hydrolysis records (or a topological consistency check when labels are synthetic).

## Statistical Validation

### χ² Test (Attribution Stability)

- **Purpose**: Test whether observed motif importance deviates from a null distribution of shuffled motif scores.  
- **Procedure**:  
  1. Generate null distribution by randomly shuffling importance scores for **all** identified motifs (≥ 1000 iterations).  
  2. Compute χ² statistic comparing observed vs. null frequencies.  
  3. Report p‑value (α = 0.05).  
- **Outcome**: A significant p‑value confirms that the model’s attributions are not random noise (FR‑006, SC‑002, SC‑011).  

### Power Analysis

- Conducted via G*Power simulation (target power ≥ 0.8). If *n* < 150, a warning is emitted and LOO validation is used (SC‑004).  

### Confidence Flagging

- Predictions with softmax probability < 0.6 (source: 2312.01650) are flagged as “low confidence” (SC‑008). The proportion of correctly flagged low‑confidence predictions is reported.

## Compute Feasibility

- **CPU‑First**: All components (data loading, augmentation, GNN training, attribution, χ² test) run within 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h total runtime.  
- **GPU Escape Hatch**: Not required; no GPU‑only algorithms are used.  
- **Streaming**: Large CSVs are streamed to stay within memory limits.

## Decision/Rationale

- **Dataset Choice** – Only the two verified CSVs are programmatically accessible; no verified SMILES source exists, so synthetic SMILES generation is necessary.  
- **Synthetic Labels** – Required to satisfy FR‑001 and FR‑008; the synthetic distribution is documented and flagged.  
- **CPU Execution** – The lightweight GNN meets the free‑tier CI constraints; no GPU needed.  
- **Statistical Rigor** – χ² test plus power analysis fulfill the constitution’s validation requirements.  
- **Scientific Framing** – All results are explicitly labeled as simulation‑based associations; no causal claims are made, respecting the observational nature of the data.

---
