# Implementation Plan: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Branch**: `[001-impurity-clustering-segregation]` | **Date**: 2026-10-17 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-impurity-clustering-segregation/spec.md`

## Summary

Build a reproducible CPU‑only pipeline that (1) loads real OQMD records via the verified `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")` recipe, (2) reconstructs bulk crystal structures from composition + `volume_per_atom` using pymatgen prototypes, (3) builds grain‑boundary (GB) supercells, inserts impurities at the interface, (4) computes three interface‑region clustering descriptors (RDF peaks, pair‑correlation statistics, Voronoi neighbor counts) **after** EAM relaxation, (5) generates segregation‑energy labels with **validated** EAM potentials for three alloy systems, (6) assembles a ≥200‑sample training dataset across ≥3 alloy systems, (7) runs VIF collinearity diagnostics **before** any dimensionality reduction, (8) performs a grouped 5‑fold (or LOOCV if N < 5) cross‑validation split using `GroupKFold` on `gb_id` to avoid leakage, (9) conducts the FR‑008 power analysis (f² = 0.15, α = 0.05, predictor count = 7) and confirms ≥ 0.80 power, (10) applies multiple‑comparison correction and emits the US‑3 hypothesis‑testing JSON report, (11) generates the FR‑009 cluster‑size vs. segregation‑energy plot with 95 % CIs per alloy system, and (12) implements the FR‑011 EAM‑vs‑DFT validation harness (reports `[DATA_UNAVAILABLE]` if no benchmark is found). FR‑006 was removed from the spec; no regularization sweep is planned.

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `datasets`, `pymatgen`, `ase`, `scikit-learn`, `statsmodels`, `numpy`, `pandas`, `matplotlib`, `pyyaml`, `pytest` (versions pinned in `requirements.txt`)
- **Storage**: Local filesystem under `data/` (raw immutable, processed derived) and `results/` (JSON artifacts)
- **Testing**: `pytest` (unit + integration, including artifact‑content verification for T001b/T001c)
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, CPU‑only, ≤6 h/job)
- **Constraints**: CPU‑first; all dataset access via the verified OQMD loader; no fabricated URLs; random seeds pinned
- **Scale/Scope**: ≥200 training samples across ≥3 alloy systems; ≥50 held‑out test samples; ≥30‑sample DFT benchmark IF a verified source is supplied (see Scope Notes)

## Constitution Check

| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Seeds pinned in `code/`; OQMD fetched via the single verified `datasets` loader; `requirements.txt` pinned |
| II. Verified Accuracy | PASS | Only verified URLs cited; fabricated URLs (prior DFT‑FeCr mirror, MP bulk parquet) removed |
| III. Data Hygiene | PASS | SHA‑256 checksums in `data/metadata.yaml`; raw files immutable; derivations write new files |
| IV. Single Source of Truth | PASS | Every metric/figure traces to one `data/` row and one `code/` block; no hand‑typed numbers |
| V. Versioning Discipline | PASS | Content hashes recorded; `state/...yaml` `updated_at` maintained |
| VI. Materials Data Provenance | PASS | OQMD records via verified loader; dataset id recorded in `data/metadata.yaml`; derived structures cite OQMD source |
| VII. Model Evaluation Transparency | PASS | CV procedure, split seed, R²/RMSE/p‑values/CIs saved as JSON under `results/`, linked to code hash |

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
│   ├── output_schema.schema.yaml   ← authoritative copy of output.schema.yaml
│   └── report.schema.yaml
└── tasks.md               # generated later by /speckit-tasks
```

```text
projects/PROJ-355-predicting-the-impact-of-impurity-cluste/
├── code/
│   ├── __init__.py
│   ├── main.py               # orchestrates the full pipeline
│   ├── download.py           # verified OQMD loader + checksums
│   ├── gb_builder.py         # bulk reconstruction + GB supercells + impurity insertion
│   ├── descriptors.py        # RDF / pair‑correlation / Voronoi descriptors + VIF
│   ├── simulate_energy.py    # EAM segregation energies
│   ├── validate_potential.py # FR‑011 EAM‑vs‑DFT validation harness
│   ├── train_model.py        # FR‑004a/b, FR‑008, FR‑010, FR‑005, SC‑001/002/003
│   ├── report.py             # US‑3 JSON hypothesis report
│   └── plots.py              # FR‑009 figure
├── data/
│   ├── raw/                  # immutable OQMD‑derived records
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
├── .gitignore
├── README.md
└── requirements.txt
```

**Structure Decision**: single‑project layout (Option 1) — a linear research pipeline with no frontend/backend split.

## Scope Notes (data‑availability limitations)

1. **FR‑011 DFT benchmark**: No verified open DFT segregation‑energy benchmark exists. Consequently, the validation harness will report `[DATA_UNAVAILABLE]` and a structured limitation record unless a verified source is added later. No synthetic DFT data will be fabricated.

2. **OQMD record fields**: The verified loader supplies composition, spacegroup, and `volume_per_atom`. **These records do NOT include atomic coordinates or explicit lattice parameters.** To obtain usable bulk structures we **synthetically reconstruct** them using `pymatgen`’s `Structure.from_spacegroup`, deriving lattice constants from `volume_per_atom`. This reconstruction is a documented derivation, cited to the OQMD record ID, and recorded in `data/metadata.yaml`. **This synthetic step is a deviation from the spec’s literal “download bulk configuration files” requirement**, which expects full structure files; the limitation is explicitly noted and justified by the lack of an open, unauthenticated source for full bulk files.

3. **Materials Project data**: Access to Materials Project bulk files requires API authentication and is not programmatically reachable on the free CI runner. **Therefore the pipeline omits Materials Project downloads**, using **only** the verified OQMD dataset. This omission is a **recorded deviation** (see Materials Project Deviation below) and is reflected in the reproducibility statement.

4. **Segregation‑energy labels**: Because no open literature database of segregation‑energy measurements exists, energies are **generated in‑house** with validated EAM potentials (see Phase 4). This satisfies FR‑003 via a justified deviation (see FR‑003 Deviation below).

## Materials Project Deviation

**FR‑001 originally required downloading bulk configuration files from both Materials Project **and** OQMD using `wget`/`curl`.** The Materials Project API requires an API key and cannot be accessed anonymously on the CI runner. To remain fully reproducible on the free runner, the plan **excludes Materials Project** and relies exclusively on the OQMD dataset (which is openly downloadable). This deviation is recorded here and justified by the lack of an open, unauthenticated Materials Project endpoint. The limitation is reflected in the reproducibility check (Constitution VI) and will be documented in the final report.

## Implementation Phases & Task Logic

| Phase | Tasks (maps to FR/SC) | Key Scripts |
|-------|-----------------------|-------------|
| **1. Data Acquisition** | **FR‑001**: Load real OQMD records via `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")` (verified recipe); retry ≤3 attempts, log `[DATA_UNAVAILABLE]` on permanent failure. | `download.py` |
| **2. GB Construction** | Reconstruct bulk structures from formula + `volume_per_atom` using pymatgen prototypes (see **Methodology‑b8e4f567**); build GB supercells; insert impurity atoms at the interface; filter zero‑impurity configurations with logged counts (edge case). | `gb_builder.py` |
| **3. Descriptor Computation & Collinearity** | **FR‑002**: compute RDF peaks, pair‑correlation statistics, Voronoi neighbor counts **after** EAM relaxation, only within the interface mask. **FR‑007/FR‑012**: compute VIF on the three raw descriptors before any dimensionality reduction; emit JSON collinearity report (VIF ≥ 10 flagged). **Scientific‑soundness‑d32e…**: descriptors are extracted from the relaxed structure to keep them independent of insertion geometry. **Scientific‑soundness‑e1c…**: `cluster_size` = mean nearest‑neighbor distance among interface impurities (derived from the same neighbor list used for Voronoi counts). | `descriptors.py` |
| **4. Energy Simulation** | **FR‑003** (deviation): generate segregation energies with **validated EAM potentials** for three alloy systems (Fe‑Cr, Ni‑Al, Cu‑Zn). **Methodology‑a306aa59**: each potential is cited with its NIST repository URL and DOI. ≥200 configurations; log missing‑energy entries; warn if exclusion >5 %. | `simulate_energy.py` |
| **5. EAM‑vs‑DFT Validation Harness** | **FR‑011/SC‑006**: compare EAM energies against a DFT benchmark if available; otherwise write a `[DATA_UNAVAILABLE]` limitation record. | `validate_potential.py` |
| **6. Dataset Assembly** | Join descriptors, covariates, and energies → `data/processed/training_set.csv`; validate against `contracts/dataset.schema.yaml`; ≥200 samples, ≥3 alloy systems, ≥50 held‑out test samples. | `train_model.py` (assembly) |
| **7. Linearity Assessment** | **FR‑010**: scatter plots + residual analysis; store verdict (`appears_linear`) that drives model selection. | `train_model.py` |
| **8. Model Training & CV** | **FR‑004a**: Linear Regression with 5‑fold CV (or LOOCV if N < 5), robust SE p‑values. **FR‑004b**: RandomForest with same CV. **Methodology‑634ae014**: split performed with `GroupKFold` on `gb_id` to prevent leakage. **SC‑001**: permutation testing for R² significance; per‑system R² for ≥3 systems. **SC‑002**: held‑out RMSE with [deferred] prediction intervals. | `train_model.py` |
| **9. Power Analysis** | **FR‑008**: `statsmodels` power analysis with f² = 0.15, α = 0.05, predictor count = 7; report required N and compare to achieved N. **Methodology‑dcd5c179**: predictor count explicitly stated. | `train_model.py` |
| **10. Hypothesis Testing & Report** | **FR‑005/SC‑003**: Bonferroni or Benjamini‑Hochberg correction; report adjusted p‑values and count of significance changes; emit `results/hypothesis_report.json`. | `report.py` |
| **11. Visualization** | **FR‑009/SC‑005**: cluster‑size vs. segregation‑energy scatter with 95 % CIs per alloy system, high‑resolution PNG. | `plots.py` |
| **12. Output Serialization & Verification** | Write `results/metrics.json` (validated against `contracts/output.schema.yaml`); integration test verifies `.gitignore` and `README.md` content, runs full pipeline (`T012b`) and validation harness (`T017f`). | `main.py`, `tests/integration/test_artifact_verification.py` |

Task ordering respects data dependencies: download → GB construction → descriptors → energies → validation → assembly → modeling → reporting → figures → verification. FR‑006 (sensitivity sweep) was **REMOVED** from the spec and is not planned.

## FR/SC Coverage Map

| ID | Phase | | ID | Phase |
|----|-------|-|----|-------|
| FR‑001 | 1 | | FR‑009 | 11 |
| FR‑002 | 3 | | FR‑010 | 7 |
| FR‑003 | 4 | | FR‑011 | 5 |
| FR‑004a | 8 | | FR‑012 | 3 |
| FR‑004b | 8 | | SC‑001 | 8, 9 |
| FR‑005 | 10 | | SC‑002 | 8 |
| FR‑007 | 3 | | SC‑003 | 10 |
| FR‑008 | 9 | | SC‑004 | 3 |
| — | — | | SC‑005 | 11 |
| — | — | | SC‑006 | 5 |

## FR‑001 Deviation

The Materials Project requires authentication and is not programmatically accessible on the free CI runner. To remain fully reproducible, the pipeline **deviates** by using only the verified OQMD loader. This deviation is recorded here and justified by the lack of an open, unauthenticated Materials Project endpoint.

## FR‑003 Deviation

No open‑access literature database of segregation‑energy measurements exists. Consequently, segregation energies are **generated in‑house** using validated EAM potentials (see Phase 4). This satisfies the intent of providing target labels while acknowledging the source limitation.

## Scope Limitation (Associational Claim)

All statistical relationships reported (R², coefficients, p‑values) are **associational within the EAM‑potential internal physics**. No causal inference about real material behavior is claimed. Results reflect how the chosen EAM model maps the computed clustering descriptors to its own segregation‑energy predictions.

## Expected Outputs

- `data/processed/training_set.csv` — schema‑validated regression dataset (≥200 samples, ≥3 alloy systems)
- `results/metrics.json` — CV metrics, per‑system R², permutation p‑values, VIF report, power analysis, linearity assessment, EAM validation status
- `results/hypothesis_report.json` — raw/adjusted p‑values, significance‑change count, textual summary (US‑3)
- `results/cluster_size_vs_segregation.png` — FR‑009 figure
- `.gitignore` and `README.md` with verifiable CONTENT (T001b/T001c) – tests ensure they contain the required patterns/sections