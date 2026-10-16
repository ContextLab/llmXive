# Implementation Plan: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Branch**: `001-polymer-degradation` | **Date**: 2026-06-28 | **Spec**: `specs/001-predicting-polymer-degradation-pathways/spec.md`
**Input**: Feature specification from `/specs/001-predicting-polymer-degradation-pathways/spec.md`

## Summary

This feature implements a lightweight Graph Neural Network (GNN) pipeline to predict *synthetic* polymer degradation pathways (hydrolysis, oxidation, photolysis) derived from chemical priors, using molecular structures (SMILES) and environmental conditions. It ingests polymer degradation records, applies synthetic labeling where ground‑truth is missing, augments the data, trains a ≤3‑layer GNN on CPU, computes Integrated Gradients attributions, and validates structure‑mechanism relationships with a χ² test. All steps respect the project constitution (reproducibility, data hygiene, statistical validation) and run within the free‑tier CI constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: RDKit, PyTorch (CPU‑only), PyTorch Geometric, scikit‑learn, pandas, numpy, requests, scipy, datasets  
**Storage**: Local file system (CSV/Parquet for raw data, JSONL for processed records, Pickle for graph objects)  
**Testing**: pytest (unit, integration, contract)  
**Target Platform**: Linux (GitHub Actions free‑tier runner)  
**Project Type**: Computational Chemistry Simulation Pipeline  
**Performance Goals**: ≤6 h total runtime, ≤7 GB RAM peak, ≤30 min augmentation, ≤30 min training on CPU  
**Constraints**: CPU‑only execution; no GPU required; dataset size limited to fit RAM; synthetic labeling allowed only when ground‑truth absent.  
**Scale/Scope**: One polymer dataset (≈ few‑hundred records after filtering), three degradation classes, one lightweight GNN model, one statistical report.

> Domain‑specific quantitative details (e.g., exact record counts) are deferred to the research phase and will be cited from verified sources.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re‑check after Phase 1 design.*

- **I. Reproducibility** – All random seeds pinned; external data fetched from canonical URLs; `requirements.txt` pins dependencies.  
- **II. Verified Accuracy** – Citations will be validated by the Reference‑Validator against primary sources.  
- **III. Data Hygiene** – Raw data checksummed; transformations produce new files; no PII.  
- **IV. Single Source of Truth** – Every figure/statistic traces to a single data row and code block.  
- **V. Versioning Discipline** – Content hashes recorded; timestamps updated on change.  
- **VI. Computational Chemistry Validation** – χ² test (α = 0.05) for attribution stability; Integrated Gradients for feature importance; 5‑fold CV (or LOO if *n* < 150).  
- **VII. Small Dataset Robustness** – Edge‑dropout & subgraph‑sampling augmentation (2×); confidence intervals reported.

## Project Structure

### Documentation (this feature)

```text
specs/001-polymer-degradation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
projects/PROJ-078-predicting-polymer-degradation-pathways-/
├── data/
│   ├── raw/
│   ├── processed/
│   └── augmented/
├── code/
│   ├── ingest.py
│   ├── preprocess.py
│   ├── augment.py
│   ├── model.py
│   ├── train.py
│   ├── attribution.py
│   ├── validate.py
│   ├── utils.py
│   ├── data_models.py
│   └── requirements.txt
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── state/
│   ├── setup_log.txt
│   ├── artifact_hashes.yaml
│   └── current_stage.yaml
└── docs/
    └── usage.md
```

**Structure Decision**: Single‑project layout with modular scripts; aligns with CI runner limits and simplifies reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Data augmentation (2×) | Small dataset needs robustness (Constitution VII) | No augmentation would cause over‑fitting. |
| 5‑fold CV (or LOO) | Small sample size; must capture variance (Constitution VI) | Single split would hide uncertainty. |
| χ² test with ≥1000 iterations | Required statistical validation (FR‑006) | No test would leave findings unverifiable. |
| Synthetic labels | Ground‑truth absent; supervised learning otherwise impossible (FR‑001, FR‑008) | Training without labels is infeasible. |

## Implementation Phases

### Phase 0: API Source Verification (T051)

- Attempt to fetch NIST Chemistry WebBook and Materials Project records for polyesters.  
- Exponential backoff (max 3 retries).  
- Log successes/failures; on failure, fall back to verified HuggingFace CSV sources.

### Phase 1: Data Ingestion & Preprocessing (T013–T020)

- **T013** – `ingest.py`: download verified CSVs, filter for polyesters (ester SMARTS `C(=O)O`). Save raw CSV to `data/raw/`.  
- **T014** – Identify records missing `degradation_pathway`; flag them, compute missing‑label ratio.  
- **T015** – `preprocess.py`: convert SMILES → `MolecularGraph` via RDKit; impute missing temperature/pH/UV with defaults (25 °C, pH 7, UV 0). Skip invalid SMILES, log.  
- **T016** – Save processed records (`data/processed/records.parquet`) and graph objects (`data/processed/graphs/`). Record SHA‑256 checksums in `state/artifact_hashes.yaml`.  
- **T017a/b** – Power analysis using G*Power (via `statsmodels` proxy) → warning if *n* < 150; store decision in `state/power_analysis.json`.  
- **T019** – Verify ingestion success ≥95 % (SC‑006); generate `data/metadata.json`.  
- **T020** – Comprehensive logging of all actions.

### Phase 2: Data Augmentation (T025a–T025c)

- **T025a** – `augment.py`: edge dropout (p = 0.1) + subgraph sampling to create exactly 2× records while preserving topology.  
- **T025b** – Validate augmentation method (check that each augmented graph differs from its source and that edge dropout/subgraph sampling were applied).  
- **T025c** – Measure runtime; enforce <30 min (SC‑009).

### Phase 3: Model Training (T024–T033)

- **T024** – `model.py`: lightweight GNN (≤3 layers, hidden ≤ 128).  
- **T028** – `train.py`: 5‑fold CV (or LOO if *n* < 150) with early‑stopping; report macro‑F1 and loss convergence (|Δloss|/loss < 0.05).  
- **T029** – Compute Integrated Gradients for each test sample (`attribution.py`).  
- **T030** – Verify ester bond appears in top attribution scores for ≥90 % of hydrolysis cases (SC‑005).  
- **T031** – Save final model checkpoint (`code/models/model.pt`).  
- **T032** – Generate predictions on held‑out test set; compute macro‑F1 (SC‑001).  
- **T033** – Log training metrics, validation strategy used.

### Phase 4: Statistical Validation & Reporting (T034–T037)

- **T034** – Unit test for permutation‑test generation.  
- **T035** – Unit test for motif extraction across all identified motifs.  
- **T036** – Integration test for end‑to‑end report generation.  
- **T037** – `validate.py`: χ² test with ≥1000 null‑distribution iterations for **all** identified motifs; produce final markdown report (`docs/reports/final_report.md`) containing:
  - p‑value(s) (SC‑011)  
  - Top 3‑5 motifs with importance scores (SC‑007)  
  - Low‑confidence flagging (< 0.6) statistics (SC‑008)  
  - Power‑analysis warning if applicable (SC‑004)  

### Phase 5: Final Checks (T043–T057)

- Generate README, usage docs, memory monitoring, optional subsampling if RAM exceeds 7 GB, compute feasibility metrics (runtime, RAM) to satisfy SC‑003, and ensure all contracts pass schema validation.

## Compute Feasibility

- **CPU‑First** – All steps run on the free‑tier CI CPU (2 cores, ~7 GB RAM).  
- **GPU Escape Hatch** – Not required; no GPU‑only methods are used.  
- **Streaming** – Large CSVs are streamed via `datasets.load_dataset(..., streaming=True)` to avoid OOM.

## Risk Mitigation

- API failure → fallback to verified CSVs.  
- Small *n* → LOO validation + power‑analysis warning.  
- Invalid SMILES → skip & log.  
- Memory pressure → automatic subsampling.  
- Synthetic label reliance → explicit flagging in report; no causal claims.

---
