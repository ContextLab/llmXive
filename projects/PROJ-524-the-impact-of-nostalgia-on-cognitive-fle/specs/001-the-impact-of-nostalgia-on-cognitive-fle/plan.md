# Implementation Plan: Nostalgia Cognitive Flexibility Analysis

**Branch**: `001-nostalgia-cognitive-flexibility` | **Date**: 2026-10-20 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-nostalgia-cognitive-flexibility/spec.md`

## Summary
The study will **collect primary data** from adults aged ≥ 65 under a controlled nostalgia‑induction or neutral control condition, then run a fully reproducible statistical pipeline that satisfies all functional requirements (FR‑001 – FR‑007) and success criteria (SC‑001 – SC‑007).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==2.0.0`, `scipy==1.14.0`, `statsmodels==0.14.2`, `pyyaml==6.0.2` (pinned in `requirements.txt`)  
- **Compute**: CPU‑only; expected wall‑clock time < 30 min, memory < 2 GB.  
- **Target Platform**: Linux GitHub Actions runner (free tier).  

## Constitution Check
| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | ✅ | `requirements.txt` pins exact versions; random seed fixed (42) for any stochastic step; CI isolation enforced. |
| II. Verified Accuracy | ✅ | `code/reference_validator.py` checks title‑overlap ≥ 0.7 for all citations. |
| III. Data Hygiene | ✅ | All files under `data/` are SHA‑256 checksummed; raw files never overwritten; transformations write new files. |
| IV. Single Source of Truth | ✅ | All numbers in `statistical_report.json` and `sensitivity_report.json` are generated programmatically; no hand‑typed values. |
| V. Versioning Discipline | ✅ | After each artifact write, `utils.update_state_hash()` records the file’s SHA‑256 in `state/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle.yaml`. |
| VI. Stimulus Fidelity | ✅ | Placeholder audio files (`nostalgia.wav`, `control.wav`) stored with SHA‑256 checksums in `data/stimuli/manifest.json`; each participant receives a deterministic `stimulus_id`. |
| VII. Behavioral Trace Integrity | ✅ | Raw WCST trial logs (if any) preserved under `data/raw/`. |

## Project Structure
```text
specs/001-nostalgia-cognitive-flexibility/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml

projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/
├── data/
│   ├── raw/
│   │   ├── wcst_dataset.csv               # to be populated by the lab team after data collection
│   │   └── metadata.json                  # {"collection_mode": "real", "expected_n_per_group": 150}
│   ├── processed/
│   │   ├── cleaned_dataset.csv            # after FR‑001, FR‑006 filtering
│   │   └── wcst_metrics.csv               # participant_id, perseverative_errors, categories_completed
│   ├── stimuli/
│   │   ├── nostalgia.wav
│   │   ├── control.wav
│   │   └── manifest.json                  # paths + SHA‑256 checksums + stimulus_id mapping
│   └── results/
│       ├── statistical_report.json
│       ├── sensitivity_report.json
│       └── exclusion_log.json
├── code/
│   ├── __init__.py
│   ├── collection.py                     # protocol for in‑lab data collection (manual step)
│   ├── cleaning.py                       # FR‑001, FR‑006, missing‑value handling
│   ├── stimulus.py                       # assigns deterministic stimulus_id per participant
│   ├── analysis.py                       # Welch test, Bonferroni, Cohen's d with 95 % CI, MDES
│   ├── sensitivity.py                    # α‑sweep & MMSE‑exclusion sensitivity
│   ├── runtime_monitor.py                # logs warning if runtime > 6 h (FR‑007)
│   ├── reference_validator.py
│   ├── utils.py                          # checksum, hash updates, stimulus verification, state YAML update
│   └── main.py                           # orchestrates the pipeline
├── tests/
│   ├── contract/
│   │   └── validate_output.py
│   ├── integration/
│   └── unit/
├── requirements.txt
└── README.md
```

## Mapping of Functional Requirements & Success Criteria to Pipeline Phases
| FR / SC | Requirement | Script / Function | Output | Success Criterion Addressed |
|---------|-------------|-------------------|--------|------------------------------|
| FR‑001 | Age ≥ 65 filter | `cleaning.filter_age()` | `exclusion_log.json` (age) | SC‑001 (≥ 95 % retained) |
| FR‑006 | MMSE ≥ 24 filter (optional) | `cleaning.filter_mmse()` | `exclusion_log.json` (MMSE) | SC‑006 (counts match) |
| FR‑002 | Welch’s independent‑samples t‑test | `analysis.run_welch_test()` | `statistical_report.json` (raw p) | SC‑002 (Bonferroni‑corrected p ≤ 0.05 for at least one outcome) |
| FR‑003 | Bonferroni correction | `analysis.apply_bonferroni()` | `statistical_report.json` (corrected p) | SC‑003 (α_corrected = 0.025) |
| FR‑004 | Cohen's d with 95 % CI | `analysis.compute_cohen_d()` | `statistical_report.json` (effect size & CI) | SC‑004 (CI excludes zero for significant outcomes) |
| FR‑005 | Borderline flag (0.04–0.06) | `sensitivity.flag_borderline()` | `sensitivity_report.json` | SC‑005 (flag when applicable) |
| FR‑007 | Runtime warning > 6 h | `runtime_monitor.wrap()` around `main` | CI log entry “WARNING: Runtime exceeded 6 hours” | SC‑007 (warning appears if needed) |
| SC‑001 | ≥ 95 % retained after filtering | Verified by `exclusion_log.json` counts vs. initial N | – | – |
| SC‑002 | Bonferroni‑corrected p ≤ 0.05 for at least one outcome (when effect present) | Real nostalgia induction provides a plausible medium effect (Cohen's d ≈ 0.5) as per power analysis; verification in `statistical_report.json`. | – | – |
| SC‑003 | α_corrected = 0.025 | Implemented in `analysis.apply_bonferroni()` | – | – |
| SC‑004 | CI for Cohen's d does not include zero for statistically significant outcomes | Computed in `analysis.compute_cohen_d()` | – | – |
| SC‑005 | Sensitivity flag for p ∈ [0.04, 0.06] | `sensitivity.flag_borderline()` | – | – |
| SC‑006 | Exclusion log matches MMSE‑based removals | `cleaning.filter_mmse()` logs exact counts | – | – |
| SC‑007 | Runtime warning format | `runtime_monitor.py` writes standardized warning | – | – |

## Phase Ordering (Data‑Driven Execution Flow)
1. **Data Collection** – Researchers run the in‑lab protocol (see `code/collection.py`) to obtain `data/raw/wcst_dataset.csv` with required columns, including `stimulus_type`, `MMSE`, `education_years`, `gender`.  
2. **Stimulus ID Assignment** – `code/stimulus.py` verifies audio file checksums, creates a deterministic `stimulus_id` per participant, and updates `manifest.json`.  
3. **Checksum Verification & Stimulus Linking** – `code/utils.py verify_stimuli` confirms SHA‑256 matches and records the mapping.  
4. **Cleaning** – `code/cleaning.py` applies FR‑001 and FR‑006, produces `processed/cleaned_dataset.csv`, `processed/wcst_metrics.csv`, `exclusion_log.json`.  
5. **Statistical Analysis** – `code/analysis.py` runs Welch’s tests, Bonferroni correction, Cohen's d with 95 % CI, MDES; writes `statistical_report.json`.  
6. **Sensitivity Analyses** – `code/sensitivity.py` performs α‑sweep (0.01, 0.04, 0.05, 0.06) and MMSE‑exclusion sensitivity; writes `sensitivity_report.json`.  
7. **Runtime Monitoring** – `code/runtime_monitor.py` wraps the whole pipeline; emits warning if wall‑clock > 6 h.  
8. **Contract Validation** – `tests/contract/validate_output.py` checks both JSON files against `contracts/*.schema.yaml`.  
9. **Reporting** – `code/main.py` orchestrates steps 1‑8 and prints a concise summary.

## Risk & Mitigation
- **Real Data Availability** – The protocol specifies recruitment of at least 256 participants (128 per condition) based on a power analysis for a medium effect (Cohen's d ≈ 0.5) with α = 0.05, 80 % power. This ensures SC‑001 and SC‑002 are attainable.  
- **Runtime exceedance** – All steps are linear‑time; expected runtime < 30 min; warning mechanism satisfies FR‑007.  
- **Multiple‑comparison misuse** – Bonferroni factor derived from the actual number of primary outcomes (two).  
- **Effect‑size consistency** – Cohen's d is computed using the pooled standard deviation, which is appropriate for reporting alongside Welch’s test when variance heterogeneity is modest; the CI method is Welch‑compatible.  
- **Stimulus fidelity** – Placeholder audio files have SHA‑256 checksums recorded in `data/stimuli/manifest.json`; each participant receives a deterministic `stimulus_id`.  
- **Versioning** – `utils.update_state_hash()` ensures every artifact’s SHA‑256 is persisted to the project‑state YAML after write.  

---


