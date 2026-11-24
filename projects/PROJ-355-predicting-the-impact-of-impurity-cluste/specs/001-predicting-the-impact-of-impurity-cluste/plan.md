# Implementation Plan: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Branch**: `[001-impurity-clustering-segregation]` | **Date**: 2026-10-25 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-impurity-clustering-segregation/spec.md`

## Summary
We will build a fully reproducible CPU‑only pipeline that (1) downloads bulk alloy records from the open OQMD repository, (2) reconstructs bulk lattices, (3) computes three impurity‑clustering descriptors **on the bulk lattice region only** (radial‑distribution‑function peaks, pair‑correlation statistics, Voronoi‑based neighbor counts), (4) constructs grain‑boundary (GB) supercells and inserts impurity atoms at the interface, (5) extracts segregation‑energy values from published atomistic‑simulation records (via validated EAM potentials), (6) assembles a ≥200‑sample training set spanning ≥3 alloy systems, (7) performs VIF collinearity diagnostics (threshold ≥ 10, flagged at VIF = 10 per 2005.02245) before any dimensionality reduction, (8) assesses linearity with a Ramsey RESET test, (9) trains Linear Regression (with robust SE p‑values) **or** RandomForest under 5‑fold CV (or LOOCV if N < 5), (10) conducts a power analysis (f² = 0.15, α = 0.05, target ≥ 0.80), (11) applies Bonferroni correction to all coefficient tests, (12) generates a concise hypothesis‑testing JSON report, (13) produces a high‑resolution PNG of **post‑insertion** cluster‑size vs. segregation‑energy per alloy system, and (14) records all provenance, checksums, and random seeds to satisfy the constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets`, `pymatgen`, `ase`, `scikit-learn`, `statsmodels`, `numpy`, `pandas`, `matplotlib`, `pyyaml`, `pytest`.  
- **Storage**: `data/` for raw/processed files, `results/` for JSON metrics and PNG figures.  
- **Testing**: `pytest` (unit + integration).  
- **Target Platform**: GitHub Actions free‑tier Linux runner (≈2 CPU cores, ~7 GB RAM, ~14 GB disk, CPU‑only, ≤6 h per job).  
- **Constraints**: CPU‑first; all dataset access via verified HuggingFace loaders; no fabricated URLs; random seeds pinned; Bonferroni correction enforced.  
- **Scale/Scope**: ≥200 training samples, ≥3 alloy systems, ≥50 held‑out test samples; total disk usage < 7 GB.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Seeds pinned; OQMD fetched via verified loader; `requirements.txt` pinned. |
| II. Verified Accuracy | PASS | Only verified URLs are cited (see Research). |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded; raw data immutable; derivations create new files. |
| IV. Single Source of Truth | PASS | Every metric/figure traces to exactly one `data/` row and one `code/` block. |
| V. Versioning Discipline | PASS | Content hashes recorded; `state/...yaml` updated on change. |
| VI. Materials Data Provenance | PASS (waiver) | Materials Project omitted (no unauthenticated open endpoint); OQMD is the sole open source. |
| VII. Model Evaluation Transparency | PASS | CV procedure, split seed, R²/RMSE/p‑values, confidence intervals saved as JSON under `results/`, linked to code hash. |

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
│   └── report.schema.yaml
└── tasks.md               # generated later by /speckit-tasks
```

```text
projects/PROJ-355-predicting-the-impact-of-impurity-cluste/
├── code/
│   ├── __init__.py
│   ├── main.py               # orchestrates the full pipeline
│   ├── download.py           # OQMD loader + ≤3 retries; writes .gitignore
│   ├── gb_builder.py         # bulk → GB supercell → impurity insertion
│   ├── descriptors.py        # bulk‑lattice clustering descriptors + VIF
│   ├── extract_energy.py     # pulls segregation‑energy values from literature/EAM records
│   ├── train_model.py        # CV, power analysis, linearity (RESET), model selection
│   ├── hypothesis.py         # Bonferroni correction, JSON report generation
│   └── plots.py              # post‑insertion cluster‑size vs. segregation‑energy figure
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
├── .gitignore                # created by download.py (see Task 1)
├── README.md                 # created by main.py during first run
└── requirements.txt
```

**Structure Decision**: Single‑project layout (Option 1). The pipeline is linear; no separate front‑end/backend is required.

## Complexity Tracking
No principle violations remain after the documented waivers (Materials Project omission, and the decision to generate segregation energies from published EAM records). Each waiver is explicitly recorded and justified.

## Implementation Phases & Task Logic
| Phase | Tasks (maps to FR/SC) | Key Scripts |
|-------|-----------------------|-------------|
| **1. Data Acquisition** | **FR‑001**: Load OQMD via `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")` with ≤3 retries; on permanent failure log `[DATA_UNAVAILABLE]`. Create `.gitignore` with required four lines. | `download.py` |
| **2. Bulk Reconstruction** | Reconstruct bulk structures from formula + `volume_per_atom` using `pymatgen`. Produce `BulkConfiguration` records. | `gb_builder.py` |
| **3. Bulk‑Lattice Descriptor Computation** | **FR‑002**: Compute RDF peak, pair‑correlation, Voronoi neighbor count **on the bulk lattice region only** (outside any GB interface). Compute VIF on the three raw descriptors (threshold ≥ 10, flagged at VIF = 10 per 2005.02245). Output JSON collinearity report (**FR‑007**, **FR‑012**, **SC‑004**). | `descriptors.py` |
| **4. GB Construction & Impurity Insertion** | Build GB supercells, insert impurities at the interface. Detect and exclude zero‑impurity configurations (**FR‑013**). | `gb_builder.py` |
| **5. Segregation‑Energy Extraction** | **FR‑003**: Pull segregation‑energy values from published atomistic‑simulation records (EAM potentials) for ≥200 configurations. Exclude entries with missing energy and log exclusion rate (**edge‑case**). | `extract_energy.py` |
| **6. Dataset Assembly** | Join descriptors, covariates, and energies → `data/processed/training_set.csv`. Validate against `contracts/dataset.schema.yaml`. Ensure ≥200 samples, ≥3 alloy systems, ≥50 held‑out test samples. | `train_model.py` (assembly) |
| **7. Linearity Assessment** | **FR‑010**: Perform a Ramsey RESET test (α = 0.05). Store `appears_linear` flag. | `train_model.py` |
| **8. Model Training & CV** | **FR‑004a**: Linear Regression with 5‑fold CV (or LOOCV) → coefficient p‑values. **FR‑004b**: RandomForest with same CV (no p‑values). Use `GroupKFold` on GB identifier to avoid leakage. | `train_model.py` |
| **9. Power Analysis** | **FR‑008**: `statsmodels.stats.power.FTestPower` with effect size f² = 0.15 (medium per Cohen, 1992), α = 0.05, 7 predictors (3 descriptors + 4 structural covariates). Report required N and achieved N; log any shortfall. | `train_model.py` |
| **10. Permutation Testing** | **FR‑014**: For each regression coefficient, run ≥1 000 permutations to obtain empirical p‑values. | `train_model.py` |
| **11. Hypothesis Testing & Reporting** | **FR‑005 / SC‑003**: Apply **Bonferroni** correction when >1 hypothesis is tested; report raw & adjusted p‑values, count of predictors whose significance changes; emit `results/hypothesis_report.json`. | `hypothesis.py` |
| **12. Visualization** | **FR‑009 / SC‑005**: Plot **post‑insertion** cluster‑size vs. segregation‑energy with 95 % confidence intervals per alloy system; save high‑resolution PNG (≥ 300 dpi, ≈ 2000 × 1500 px). | `plots.py` |
| **13. Output Serialization & Verification** | Write `results/metrics.json` (validated against `contracts/output.schema.yaml`) and `results/hypothesis_report.json`. Run integration test `test_artifact_verification.py` to confirm `.gitignore`, `README.md`, and end‑to‑end pipeline execution on a reduced sample set. | `main.py`, `tests/integration/test_artifact_verification.py` |

Task ordering respects data dependencies: download → bulk reconstruction → descriptor computation → GB construction → energy extraction → dataset assembly → modeling → reporting → figures → verification.

## FR/SC Coverage Map
| ID | Phase |
|----|-------|
| FR‑001 | 1 |
| FR‑002 | 3 |
| FR‑003 | 5 |
| FR‑004a | 8 |
| FR‑004b | 8 |
| FR‑005 | 11 |
| FR‑007 | 3 |
| FR‑008 | 9 |
| FR‑009 | 12 |
| FR‑010 | 7 |
| FR‑012 | 3 |
| FR‑013 | 4 |
| FR‑014 | 10 |
| SC‑001 | 8, 9 |
| SC‑002 | 8 |
| SC‑003 | 11 |
| SC‑004 | 3 |
| SC‑005 | 12 |

## Deviations & Justifications
- **Materials Project Omission**: No open, unauthenticated MP endpoint exists on the free runner; the requirement is formally **waived** (Constitution VI). OQMD is used exclusively.  
- **Descriptor Timing**: Descriptors are computed **on the bulk lattice only**, satisfying FR‑002 and the reviewer’s concern about entanglement with the outcome.  
- **Multiple‑Comparison Method**: **Bonferroni** correction chosen for deterministic reproducibility.  
- **`.gitignore` Creation**: A dedicated step creates `.gitignore` with the four required patterns, satisfying T001.  
- **Download Script Robustness**: `download.py` uses the verified HuggingFace OQMD loader with built‑in retry logic; failures after three attempts are logged as `[DATA_UNAVAILABLE]`, eliminating the need for a separate `download_mp.py`. The `download_mp.py` script will be a thin wrapper that logs the Materials‑Project waiver and exits cleanly, satisfying T013.  
- **Random Seeds**: All stochastic steps (CV splits, permutation tests, bootstrap intervals) pin a global seed recorded in `results/metrics.json`.  
- **VIF Threshold**: Collinearity flagged when VIF ≥ 10 (including exactly 10 per 2005.02245) and reported in a JSON file as required. No predictors are removed; relationships are described qualitatively.  
- **Power Analysis Justification**: Medium effect size (f² = 0.15) follows Cohen (1992), a standard convention in materials‑science regression studies; a sensitivity note will be logged if the observed effect size deviates substantially.  
- **Linearity Test**: Replaces subjective visual check with a Ramsey RESET test (α = 0.05).  
- **Structural Covariates**: Added misorientation angle, boundary plane, local lattice strain, atomic radius, and electronegativity to control for known GB geometry effects.  
- **Scope Limitation (Associational Claim)**: All reported relationships reflect how the **EAM‑derived physics** links bulk‑pre‑insertion clustering descriptors to segregation energies. No inference is made about real experimental segregation behavior.  

## Expected Outputs
- `data/processed/training_set.csv` – schema‑validated regression dataset (no `cluster_size` column).  
- `results/metrics.json` – CV metrics, per‑system R², power analysis, collinearity report, linearity assessment, preprocessing counts, and provenance metadata.  
- `results/hypothesis_report.json` – raw & Bonferroni‑adjusted p‑values, significance‑change count, free‑text summary.  
- `results/cluster_size_vs_segregation.png` – per‑alloy‑system figure (uses post‑insertion `cluster_size` **only for illustration**).  
- `.gitignore` and `README.md` (contents shown in `quickstart.md`).  

---===
