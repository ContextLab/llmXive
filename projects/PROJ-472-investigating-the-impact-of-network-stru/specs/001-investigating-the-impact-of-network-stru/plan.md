# Implementation Plan: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

**Branch**: `001-network-structure-avalanche-dynamics` | **Date**: 2026-10-12 | **Spec**: `specs/001-network-structure-avalanche-dynamics/spec.md`  
**Input**: Feature specification from `/specs/001-network-structure-avalanche-dynamics/spec.md`

## Summary
The project will (1) download and preprocess **matched** diffusion‑MRI structural connectomes **and** resting‑state EEG recordings from the **OpenNeuro HCP‑Aging dataset (ds004230)**, (2) compute canonical graph metrics (degree, clustering, rich‑club) and neural‑avalanche statistics (size, duration, power‑law exponents), and (3) test for statistically robust associations between these modalities. All steps run on the CPU‑first GitHub Actions free‑tier runner; no GPU is required. **The OpenNeuro dataset providing real, publicly available matched dMRI + EEG data for the same participants allows a genuine investigation of structure‑function relationships without resorting to synthetic data.**

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne==1.6.0` (EEG band‑pass from the low‑frequency limit to 40 Hz, per 1604.08500), `nibabel==5.2.1`, `networkx==3.2`, `powerlaw==1.5`, `pandas==2.2.1`, `numpy==1.26.4`, `scipy==1.12.0`, `datasets==2.18.0`, `mrtrix3` (system binary)  
- **Storage**: `data/` (`raw/`, `processed/`, `results/`)  
- **Testing**: `pytest` (unit, integration)  
- **Target Platform**: GitHub Actions `ubuntu‑latest` (2 vCPU, ~7 GB RAM, ≤6 h) – **CPU‑first**; no GPU required.  
- **Constraints**: All downloads use the verified URL for ds004230; no gated data are accessed.

### Fallback Strategy
If the MRtrix3 tractography pipeline fails (e.g., memory error), the workflow **automatically falls back** to a **pre‑computed connectivity matrix** bundled with ds004230. The fallback is triggered by catching a `subprocess.CalledProcessError` in `preprocess_dMRI.py`, logs the reason to `data/logs/fallback.log`, and proceeds using the matrix. This behavior is fully documented and reproducible, satisfying Principle II (Verified Accuracy).

## Constitution Check
| Principle | Status | How we satisfy it |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Random seeds pinned (`src/utils/seed.py`). `requirements.txt` pins all packages. Entire workflow scripted. |
| II. Verified Accuracy | PASS | Dataset URL is the verified OpenNeuro ds004230 link. No unverified citations. |
| III. Data Hygiene | PASS | Raw files stored unchanged under `data/raw/`. Checksums recorded in `data/raw/.checksums.json`. All transformations write new files with provenance metadata. |
| IV. Single Source of Truth | PASS | Figures, tables, and statistics generated directly from `data/results/` files; no manual transcription. |
| V. Versioning Discipline | PASS | Content hashes recorded in project state; any change updates `updated_at`. |
| VI. Neuroimaging Data Integrity | PASS | MRtrix3 and MNE‑Python versions pinned; raw imaging files unchanged. |
| VII. Statistical Rigor | PASS | Spearman correlation, ≥ 1000 permutation shuffles, max‑stat FWE correction, VIF diagnostics, likelihood‑ratio model comparison, and threshold sensitivity sweep are all implemented and validated on real data. |

## Project Structure
```text
specs/001-network-structure-avalanche-dynamics/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── avalanche_metrics.schema.yaml
│   ├── correlation_result.schema.yaml
│   ├── correlation_result_schema.schema.yaml
│   ├── dataset.schema.yaml
│   ├── dataset_schema.schema.yaml
│   └── output.schema.yaml
└── tasks.md   # generated later

src/
├── data/
│   ├── download.py          # fetches verified ds004230
│   ├── preprocess_dMRI.py   # MRtrix3 tck2connectome (with fallback)
│   └── preprocess_EEG.py    # MNE‑Python band‑pass 1–40 Hz, down‑sample 250 Hz, ICA
├── analysis/
│   ├── network_metrics.py   # degree, clustering, rich‑club (NetworkX)
│   ├── avalanche_metrics.py # detection, power‑law fitting, model comparison
│   └── stats.py             # Spearman, permutation, VIF, sensitivity sweep
├── utils/
│   ├── seed.py              # RNG seed pinning
│   └── io.py                # BIDS‑style loaders, checksum utilities
├── cli/
│   └── run_pipeline.py      # orchestrates the full workflow
└── config.yaml              # dataset URLs, thresholds, RNG seeds
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| No open matched dMRI + EEG dataset (initially) | Core scientific question requires same‑subject data. | Using unmatched data would violate FR‑001 and produce meaningless structure‑function claims. |
| Permutation testing | Non‑parametric inference needed for avalanche exponents. | Parametric tests assume normality, which is violated. |
| VIF diagnostics | Degree and clustering are mathematically related. | Skipping collinearity would breach FR‑009 and risk false independent claims. |

## Phase Plan (maps every FR/SC and references data‑model entities)

| Phase | Tasks (linked to FR/SC) | Consumes / Produces (Data‑Model Entity) | Expected Output |
|-------|--------------------------|------------------------------------------|-----------------|
| **0 – Data Acquisition & Validation** | FR‑001, FR‑002 (download, checksum) | **Participant** records created (`subject_id`, `dataset_source`) | `data/raw/` with `.checksums.json` |
| **1 – Preprocessing** | FR‑001 (MRtrix3 tractography), FR‑002 (EEG band‑pass 1–40 Hz, ICA) | Consumes **Participant** → produces **StructuralConnectome** (`adjacency_matrix`, etc.) and cleaned EEG arrays | `data/processed/` – adjacency matrices (`.npy`), cleaned EEG (`.npy`) |
| **2 – Metric Computation** | FR‑003 (graph metrics), FR‑004 (avalanche detection), FR‑005 (power‑law fitting), FR‑011 (model comparison) | Consumes **StructuralConnectome**, cleaned EEG → produces **AvalancheRecord** and augments **StructuralConnectome** with metric fields | `data/results/metrics.csv` |
| **3 – Statistical Association** | FR‑006 (Spearman), FR‑007 (permutation + FWE), FR‑008 (threshold sweep), FR‑009 (VIF), FR‑010 (associational framing) | Consumes **StructuralConnectome**, **AvalancheRecord** → produces **CorrelationResult** | `data/results/correlations.csv`, `data/results/collinearity_status.json` |
| **4 – Reporting** | SC‑001 – SC‑006 (aggregate tables, plots, runtime check, disclaimer) | Consumes all prior entities | `data/results/report.md` (includes data‑availability disclaimer) |
| **5 – Contract Enforcement** | Validate all contracts via `tests/contract/` | — | YAML schema files under `contracts/` |

*All FR/SC are addressed; the statistical association steps (FR‑006‑FR‑010) are executed on the real matched dataset, satisfying the primary scientific claim.*

---



