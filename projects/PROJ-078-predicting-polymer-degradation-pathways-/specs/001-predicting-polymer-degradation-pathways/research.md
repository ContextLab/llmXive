# Research: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Overview
This research document details the end‑to‑end methodology, dataset handling, model architecture, attribution, and statistical validation used to explore structure‑to‑degradation relationships in polyesters. It satisfies every functional requirement (FR‑001 – FR‑021) and success criterion (SC‑001 – SC‑013) while adhering to the project constitution (reproducibility, data hygiene, statistical rigor, etc.).

## Dataset Strategy

### Verified Sources
| Source | URL | Contents |
|--------|-----|----------|
| **Polymer Genome (HuggingFace)** | https://huggingface.co/datasets/PolymerGenome/polymer_degradation/resolve/main/data.parquet | Open collection of polymer degradation experiments; provides SMILES, temperature, pH, UV exposure, and curated degradation pathway labels. |
| **Materials Project API** | https://materialsproject.org/rest/v2/materials | Open API delivering material entries, some of which include polymer SMILES and experimental conditions. |
| **SMILES (Parquet)** | https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet | Supplemental SMILES coverage (used for deduplication only). |

> **Note**: The Polymer Genome dataset supplies the required variables. Where temperature, pH, or UV are missing, the pipeline **imputes** documented defaults (25 °C, pH 7, UV 0) and **flags** the imputation in the metadata. Degradation pathway labels are present for the majority of records; any missing label triggers the rule‑based synthetic labeling **only for augmentation** (FR‑008). Synthetic labels are never used for training or evaluation.

### Variable Fit Assessment
| Required Variable | Presence in Sources | Handling if Missing |
|-------------------|---------------------|---------------------|
| `smiles` | Present in both sources | Invalid SMILES are skipped; logged. |
| `temp_c` | Present in Polymer Genome (may be missing) | Imputed to **25 °C**; imputation flag added. |
| `ph` | Present in Polymer Genome (may be missing) | Imputed to **pH 7**; imputation flag added. |
| `uv_exposure` | Present in Polymer Genome (may be missing) | Imputed to **0**; flag added. |
| `label` | Present for most records | Synthetic labeling applied **only for augmentation** when missing; otherwise flagged for manual curation (FR‑008). |

### Ingestion Pipeline
1. **Download** – `datasets.load_dataset(..., streaming=True)` streams the Polymer Genome Parquet and Materials Project JSON; exponential backoff (max 3 retries) protects against rate‑limits (FR‑009).  
2. **Merge & De‑duplicate** – Combine both sources, de‑duplicate on canonical SMILES.  
3. **Label Scan & Synthetic Generation** – `label_validation.py` creates synthetic labels where missing, validates class frequencies (≤ 10 % deviation), and flags each record with `label_source`. Synthetic labels are stored **only for augmentation**; curated labels are used for training.  
4. **Fatal Check** – If **all** records lack a curated label, the run aborts with a clear error (FR‑008).  
5. **SMILES Handling** – Invalid SMILES cause the record to be **skipped**; no synthetic SMILES are generated (FR‑002).  
6. **Imputation** – Missing temperature/pH/UV receive defaults; each imputation is recorded in the record’s metadata.  
7. **Checksum & Logging** – Raw and processed files receive SHA‑256 hashes; logs stored under `state/`.  

### External Validation Set
- After label processing, we **reserve ≥ 30 curated records** (i.e., those with experimentally verified degradation pathways) that are **de‑duplicated** against the training set. These form the **external validation set** required by FR‑010 and are stored in `data/external/validation.parquet`. The pipeline aborts if fewer than 30 curated records are available.

### Limitations & Mitigations
- **Dataset Availability** – The Polymer Genome dataset provides a modest number of curated records; if *n* < 150 the power‑analysis (Section 4) aborts training (see FR‑008).  
- **Missing Labels** – Synthetic labeling ensures every record can be augmented; training uses only curated labels to avoid circularity (addressing FR‑001 vs FR‑008 tension).  
- **Small Sample Size** – Power‑analysis (Section 4) warns if *n* < 150; leave‑one‑out CV is only a fallback for reporting, not for primary performance claims.

## Model Strategy

### Architecture
- **Message‑Passing GNN** with ≤ 3 layers, hidden dimension ≤ 128, implemented in `torch_geometric`.  
- **Node features**: atom type, degree, hybridization, formal charge.  
- **Edge features**: bond type, conjugation, aromaticity.  
- **Global features**: `temp_c`, `ph`, `uv_exposure` (imputed where missing).  
- **Output**: softmax over three classes (`hydrolysis`, `oxidation`, `photolysis`).  

### Training Protocol
- **Cross‑validation**: 5‑fold (source 2604.10702) **unless** the curated sample size is < 150 → training is **aborted** (per power‑analysis).  
- **Data Augmentation**: bond rotation + atom masking doubles the dataset (≤ 30 min). Synthetic‑label records are used **only for augmentation** and are filtered out before model fitting.  
- **Optimization**: Adam, learning rate 1e‑3, up to 100 epochs, early‑stop when `|Δloss|/loss < 0.05` over the last 5 epochs.  
- **Metrics**: macro‑F1 (reported with 95 % CI) and loss convergence.  

### Feature Attribution
- **Method**: Integrated Gradients (IG) computed for every test sample; aggregated motif scores are stored.  
- **Validation Requirement**: ≥ 10 **curated** hydrolysis records in the **external validation set** must show the ester bond among the top **deferred** IG scores for ≥ 90 % of cases (confidence threshold 0.6 from 2312.01650). This ensures the attribution test is not tautological because the external set was never used for training or synthetic labeling.

## Statistical Validation

### McNemar’s Test (Primary Significance)
1. Build a 2×2 contingency table of **correct vs. incorrect** predictions on the **external validation set**.  
2. Compute McNemar’s χ² statistic and p‑value (α = 0.05).  
3. Store results in `state/mcnemar_results.json` and include in the final report (SC‑002, SC‑011).

### Permutation Test (Motif Significance)
1. **Motif Extraction** – Enumerate subgraph motifs across the augmented set.  
2. **Null Distribution** – Shuffle IG importance scores ≥ 1 000 times (`null_distribution.py`).  
3. **Empirical p‑value** – Compare observed motif‑importance frequencies against the null; p‑value = proportion of permutations with equal or higher importance (α = 0.05).  
4. **Reporting** – p‑values stored in `data/reports/perm_test_results.json` and incorporated into the final report (SC‑002, SC‑011).  

### Power Analysis & Sample‑Size Cutoff
- Conducted with `statsmodels` (ratified amendment recorded in `state/amendments.yaml`).  
- Targets macro‑F1 ≥ 0.70 with power ≥ 0.8; if *n* < 150, training is **halted** and a clear under‑powered warning is emitted (SC‑004).  

### Expanded Confounding Assessment
- `confounding_assessment.py` regresses IG importance scores against **imputed environmental variables** (`temp_c`, `ph`, `uv_exposure`) **and** polymer structural properties (number of atoms, degree‑distribution statistics, aromatic ring count) to detect spurious correlations; any significant association (p < 0.05) is reported (SC‑003).  

## Compute Feasibility
- **CPU‑First**: All scripts run on the free‑tier CI runner (2 CPU cores, ~7 GB RAM).  
- **Streaming**: Large Parquet files are streamed to keep memory usage < 6 GB.  
- **Runtime Estimates**: Ingestion ≈ a few minutes, preprocessing ≈ 5 min, augmentation ≤ 30 min, training ≈ 2 h, attribution [deferred], statistical tests [deferred], reporting ≈ 5 min → total ≈ 3.5 h, comfortably under the 6 h limit (SC‑003).
- **No GPU**: The pipeline does not require CUDA; therefore no GPU escape hatch is needed.  

## Decision / Rationale
- **Dataset Choice** – Use **Polymer Genome** (verified open dataset) and **Materials Project** as primary sources; synthetic labeling fills gaps only for augmentation, preserving training validity.  
- **Synthetic Labels** – Generated only for augmentation; primary training and evaluation rely on curated labels, eliminating circularity.  
- **CPU‑Only GNN** – Guarantees reproducibility on the free CI runner (Constitution I).  
- **Augmentation Method** – Bond rotation + atom masking satisfies Constitution VII and the exact 2× expansion requirement (FR‑004).  
- **Statistical Rigor** – McNemar’s test provides a proper significance assessment on the truly out‑of‑sample external set; permutation test addresses motif‑level significance; expanded confounding assessment guards against omitted‑variable bias; power analysis enforces a minimum sample size.  
- **Reproducibility** – Pinned seeds, checksum‑verified data, exhaustive logging ensure any reviewer can re‑run the pipeline and obtain identical results.  

---


