# Implementation Plan: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Branch**: `[001-impurity-clustering-segregation]` | **Date**: 2026-10-25 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-impurity-clustering-segregation/spec.md`

## Summary
Build a fully reproducible CPU‑only pipeline that (1) downloads bulk alloy records **exclusively from the open OQMD dataset** (Materials Project omitted due to lack of an unauthenticated open endpoint on the free runner), (2) reconstructs bulk structures, (3) builds grain‑boundary supercells, (4) **computes three clustering descriptors (RDF peak, pair‑correlation, Voronoi neighbor count) *within the grain‑boundary interface region on the GB supercell **before** impurity insertion** (satisfying FR‑002 while keeping predictors independent of the outcome), (5) generates segregation‑energy labels with validated EAM potentials, (6) assembles a ≥200‑sample training set across ≥3 alloy systems, (7) performs VIF collinearity diagnostics (threshold ≥ 10, flagged at VIF = 10 per 2005.02245) before any dimensionality reduction, (8) assesses linearity using a quantitative Ramsey RESET test, (9) trains the selected model (Linear Regression with robust SE p‑values *or* RandomForest) under 5‑fold CV (or LOOCV if N < 5), (10) conducts a power analysis (f² = 0.15, α = 0.05, target ≥ 0.80), (11) applies **Bonferroni** correction to all coefficient tests, (12) generates a concise hypothesis‑testing JSON report, (13) produces a high‑resolution PNG of **post‑insertion** cluster‑size vs. segregation‑energy per alloy system (visualization only), and (14) **attempts** EAM‑vs‑DFT validation; if no open DFT benchmark is provided the harness records `[DATA_UNAVAILABLE]` (requires spec amendment). All artifacts are checksum‑verified and traceable to a single source of truth.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets`, `pymatgen`, `ase`, `scikit-learn`, `statsmodels`, `numpy`, `pandas`, `matplotlib`, `pyyaml`, `pytest`.  
- **Storage**: `data/` (raw immutable, processed derived) and `results/` (JSON metrics, PNG figures) on the local filesystem.  
- **Testing**: `pytest` (unit + integration).  
- **Target Platform**: GitHub Actions free‑tier Linux runner (A small number of CPU cores., ~7 GB RAM, ~a modest‑capacity disk, CPU‑only, ≤6 h per job).  
- **Constraints**: CPU‑first; all dataset access via verified HuggingFace loaders; no fabricated URLs; random seeds pinned; Bonferroni correction enforced.  
- **Scale/Scope**: ≥200 training samples, ≥3 alloy systems, ≥50 held‑out test samples; total disk usage < 7 GB.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Seeds pinned; OQMD fetched via verified loader; `requirements.txt` pinned. |
| II. Verified Accuracy | PASS | Only verified URLs cited (see Research). |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded; raw data immutable; derivations produce new files. |
| IV. Single Source of Truth | PASS | Every metric/figure traces to exactly one `data/` row and one `code/` block. |
| V. Versioning Discipline | PASS | Content hashes recorded; `state/...yaml` updated on change. |
| VI. Materials Data Provenance | PASS (waiver) | Materials Project data are omitted (no open unauthenticated source). OQMD is the sole open source. |
| VII. Model Evaluation Transparency | PASS | CV procedure, split seed, R²/RMSE/p‑values, confidence intervals saved as JSON under `results/`, linked to code hash. |
| FR‑011 Validation | **UNVERIFIED** (requires open DFT benchmark) | No open DFT benchmark is currently available; the validation harness will log `[DATA_UNAVAILABLE]`. Spec amendment needed to provide a benchmark. |

## Project Structure
```text
specs/001-predicting-the-impact-of-impurity-cluste/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   ├── output_schema.schema.yaml
│   └── report.schema.yaml
└── tasks.md               # generated later by /speckit-tasks
```

```text
projects/PROJ-355-predicting-the-impact-of-impurity-cluste/
├── code/
│   ├── __init__.py
│   ├── main.py               # orchestrates the full pipeline
│   ├── download.py           # OQMD loader + ≤3 retries; writes .gitignore
│   ├── gb_builder.py         # bulk reconstruction → GB supercell → impurity insertion
│   ├── descriptors.py        # **pre‑insertion** interface‑region descriptors + VIF diagnostics
│   ├── simulate_energy.py    # EAM segregation‑energy generation
│   ├── validate_potential.py # FR‑011 harness – writes DATA_UNAVAILABLE if needed
│   ├── train_model.py        # CV, power analysis, linearity (RESET test), model selection
│   ├── report.py             # Bonferroni correction, JSON hypothesis report
│   └── plots.py              # **post‑insertion** cluster‑size vs. segregation‑energy figure
├── data/
│   ├── raw/                  # immutable OQMD records (downloaded)
│   ├── processed/
│   └── metadata.yaml
├── results/
│   ├── metrics.json
│   ├── hypothesis_report.json
│   └── cluster_size_vs_segregation.png
├── tests/
│   ├── unit/
│   │   ├── test_descriptors.py
│   │   ├── test_gb_builder.py
│   │   └── test_train_model.py
│   └── integration/
│       └── test_artifact_verification.py
├── .gitignore                # created by download.py (see Task 1)
├── README.md                 # created by main.py during first run
└── requirements.txt
```

**Structure Decision**: Single‑project layout (Option 1). The pipeline is linear, no separate frontend/backend is required.

## Complexity Tracking
No violations after the documented waivers (Materials‑Project omission and DFT‑benchmark unavailability). Each waiver is explicitly recorded and justified.

## Implementation Phases & Task Logic
| Phase | Tasks (maps to FR/SC) | Key Scripts |
|-------|-----------------------|-------------|
| **1. Data Acquisition** | **FR‑001**: Load OQMD via `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")` with ≤3 retries; on permanent failure log `[DATA_UNAVAILABLE]`. Also **create `.gitignore`** with required patterns. | `download.py` |
| **2. Bulk Reconstruction** | Reconstruct bulk structures from formula + `volume_per_atom` using `pymatgen.Structure.from_spacegroup`. **Create `BulkConfiguration` records** as defined in `data-model.md`. | `gb_builder.py` |
| **3. Descriptor Computation (Pre‑Insertion)** | **FR‑002** (amended): compute RDF peak, pair‑correlation, Voronoi neighbor count **within the GB interface region on the supercell *before* impurity insertion**; **create `ClusteringDescriptor` records** per `data-model.md`; compute VIF on these three raw descriptors (threshold ≥ 10, flagged at VIF = 10 per 2005.02245) and output JSON collinearity report. | `descriptors.py` |
| **4. GB Construction & Impurity Insertion** | Build GB supercells, insert impurities at the interface; **create `GrainBoundaryStructure` records**; filter zero‑impurity cases (edge‑case logging). | `gb_builder.py` |
| **5. Energy Generation** | **FR‑003**: generate segregation energies with validated EAM potentials for Fe‑Cr, Ni‑Al, Cu‑Zn; ≥200 labeled configurations; **create `SegregationEnergy` records**; exclude missing‑energy entries; warn if exclusion > 5 %. | `simulate_energy.py` |
| **6. EAM‑vs‑DFT Validation Harness** | **FR‑011** (requires spec amendment): attempt validation against an open DFT benchmark; if none is provided, the script records `status: DATA_UNAVAILABLE` and exits cleanly. | `validate_potential.py` |
| **7. Dataset Assembly** | Join descriptors, covariates, and energies → `data/processed/training_set.csv`; validate against `contracts/dataset.schema.yaml`; ensure ≥200 samples, ≥3 alloy systems, ≥50 held‑out test samples. **Create `TrainingSample` records** per `data-model.md`. | `train_model.py` (assembly) |
| **8. Linearity Assessment** | **FR‑010**: perform a Ramsey RESET test (α = 0.05); result stored as `appears_linear` flag. | `train_model.py` |
| **9. Model Training & CV** | **FR‑004a**: Linear Regression (OLS) with 5‑fold CV (or LOOCV) → coefficient p‑values. **FR‑004b**: RandomForest with same CV. Use `GroupKFold` on `gb_id` to avoid leakage. **SC‑001**: permutation testing (≥1000 permutations, seeded) for held‑out R² per alloy system (≥3 systems). | `train_model.py` |
| **10. Power Analysis** | **FR‑008**: `statsmodels.stats.power.FTestPower` with effect size f² = 0.15 (medium per Cohen, 1992), α = 0.05, **Multiple predictors.** (3 descriptors + 4 structural covariates). Report required N and achieved N; log any shortfall. | `train_model.py` |
| **11. Hypothesis Testing & Reporting** | **FR‑005/SC‑003**: Apply **Bonferroni** correction when >1 coefficient is tested; report adjusted p‑values, count of predictors whose significance (α = 0.05) changes; emit `results/hypothesis_report.json`. | `report.py` |
| **12. Visualization** | **FR‑009/SC‑005**: Plot **post‑insertion** cluster‑size vs. segregation‑energy with 95 % confidence intervals per alloy system; save high‑resolution PNG. (Cluster size is *not* used as a predictor — it is visual‑only.) | `plots.py` |
| **13. Output Serialization & Verification** | Write `results/metrics.json` (validated against `contracts/output.schema.yaml`) and `results/hypothesis_report.json`; run integration test `test_artifact_verification.py` to confirm `.gitignore`, `README.md`, and end‑to‑end pipeline execution on a reduced sample set. | `main.py`, `tests/integration/test_artifact_verification.py` |

Task ordering respects data dependencies: download → bulk reconstruction → descriptor computation → GB construction → energy generation → validation → assembly → modeling → reporting → figures → verification.

## FR/SC Coverage Map
| ID | Phase |
|----|-------|
| FR‑001 | 1 |
| FR‑002 | 3 |
| FR‑003 | 5 |
| FR‑004a | 9 |
| FR‑004b | 9 |
| FR‑005 | 11 |
| FR‑006 | (removed) |
| FR‑007 | 3 |
| FR‑008 | 10 |
| FR‑009 | 12 |
| FR‑010 | 8 |
| FR‑011 | 6 |
| FR‑012 | 3 |
| SC‑001 | 9, 10 |
| SC‑002 | 9 |
| SC‑003 | 11 |
| SC‑004 | 3 |
| SC‑005 | 12 |
| SC‑006 | 6 (requires spec amendment) |

## Deviations & Justifications
- **Materials Project Omission**: No open, unauthenticated MP endpoint exists on the free runner; the requirement is formally **waived** (Constitution VI). OQMD is used exclusively.  
- **DFT Benchmark Unavailability**: No open DFT benchmark is publicly accessible; the validation harness records a `[DATA_UNAVAILABLE]` flag and the limitation is documented (requires spec amendment).  
- **Descriptor Timing**: Descriptors are computed **within the interface region on the pre‑insertion GB supercell** to satisfy FR‑002 while keeping predictors independent of the outcome.  
- **Multiple‑Comparison Method**: **Bonferroni** correction is explicitly chosen for deterministic reproducibility.  
- **`.gitignore` Creation**: A dedicated step (Task 1) creates `.gitignore` with the four required patterns, satisfying T001.  
- **Download Script Robustness**: `download.py` uses the verified HuggingFace OQMD loader with built‑in retry logic; failures after three attempts are logged as `[DATA_UNAVAILABLE]`, eliminating the need for a separate `download_mp.py` (T013 removed).  
- **Random Seeds**: All stochastic steps (CV splits, permutation tests, bootstrap intervals) pin a global seed recorded in `results/metrics.json`.  
- **VIF Threshold**: Collinearity is flagged when VIF ≥ 10 (including exactly 10 per 2005.02245) and reported in a JSON file as required. No predictors are removed; relationships are described qualitatively.  
- **Power Analysis Justification**: Medium effect size (f² = 0.15) follows Cohen (1992), a standard convention in materials‑science regression studies; a sensitivity note will be logged if the observed effect size deviates substantially.  
- **Linearity Test**: Replaces subjective visual check with a Ramsey RESET test (α = 0.05).  
- **Structural Covariates**: Added misorientation angle, boundary plane, local lattice strain, atomic radius, and electronegativity to control for known GB geometry effects (methodology‑c28c62e6).  
- **Scope Limitation (Associational Claim)**: All reported relationships reflect how the **EAM‑derived physics** links bulk‑pre‑insertion clustering descriptors to segregation energies. No inference is made about real experimental segregation behavior.  

## Expected Outputs
- `data/processed/training_set.csv` – schema‑validated regression dataset (no `cluster_size` column).  
- `results/metrics.json` – CV metrics, per‑system R², power analysis, collinearity report, linearity assessment, preprocessing counts, metadata.  
- `results/hypothesis_report.json` – raw & Bonferroni‑adjusted p‑values, significance‑change count, free‑text summary.  
- `results/cluster_size_vs_segregation.png` – per‑alloy‑system figure (uses post‑insertion `cluster_size` *only for illustration*).  
- `.gitignore` and `README.md` (contents shown in `quickstart.md`).  

---===
