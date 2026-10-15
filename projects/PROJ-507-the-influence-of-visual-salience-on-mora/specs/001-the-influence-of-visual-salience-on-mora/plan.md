# Implementation Plan: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Branch**: `001-visual-salience-moral-judgments` | **Date**: 2024-10-15 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-visual-salience-on-moral-judgments/spec.md`

## Summary
The project builds a reproducible pipeline that (1) prepares a set of morally ambiguous visual scenarios from a verified open‑image dataset, (2) generates low/medium/high visual‑salience variants, (3) deploys a within‑subject survey with wash‑out breaks and attention checks, (4) cleans the data using comprehensive exclusion criteria, (5) fits a Cumulative Link Mixed Model (CLMM) with an ordinal‑regression fallback, and (6) produces a full analysis report. All steps map directly to FR‑001 – FR‑009 and SC‑001 – SC‑005.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pillow`, `pandas`, `numpy`, `datasets`, `torch`, `transformers`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `pyyaml`  
- **Storage**: Local `data/` hierarchy (raw, processed, checksums)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ≈7 GB RAM, ≈14 GB disk). GPU work is automatically off‑loaded to a free Kaggle GPU (`device="cuda"`).  
- **Constraints**: ≤7 GB RAM, ≤14 GB disk, CPU‑first execution preferred.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | All scripts are deterministic (fixed RNG seeds), external datasets are fetched from canonical URLs, `requirements.txt` pins versions. |
| II. Verified Accuracy | Only URLs listed in the “Verified datasets” block are cited (Open Images V6, CLIP, BERT). |
| III. Data Hygiene | Raw files are checksummed (`data/checksums.txt`). Every transformation writes a new file with a derivation log. |
| IV. Single Source of Truth | Every figure/table references a single row in `data/processed/` and a single code block (see SSoT Mapping section). |
| V. Versioning Discipline | Content hashes recorded in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Stimulus‑Control Integrity | Manipulation parameters are versioned (`config/manipulation.yaml`). Validation thresholds (CLIP ≥ 0.95, RMS contrast ≥ 15 %) are enforced and checked against `contracts/stimulus.schema.yaml`. |
| VII. Behavioral Response Validation | Survey responses are stored with explicit `participant_id`, `variant_id`, `salience_level`, and `blame_rating`, validated against `contracts/response.schema.yaml`. |

## Project Structure
```
specs/001-visual-salience-on-moral-judgments/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── stimulus.schema.yaml
│   ├── response.schema.yaml
│   ├── analysis_schema.yaml
│   └── … (other schemas)
└── tasks.md            # created later by /speckit-tasks
```

```
projects/PROJ-507-the-influence-of-visual-salience-on-mora/
├── data/
│   ├── raw/                     # Open Images V6 download cache
│   ├── processed/
│   │   ├── candidates_filtered.csv
│   │   ├── scenarios.csv
│   │   ├── stimuli_manifest.csv
│   │   ├── responses_raw.csv
│   │   ├── responses_cleaned.csv
│   │   └── analysis_results.json
│   └── checksums.txt
├── code/
│   ├── 00_pilot_power_analysis.py
│   ├── 01_ingest_and_filter.py          # FR‑008, uses Open Images V6
│   ├── 04_human_coding.py               # FR‑008
│   ├── 03_manipulate_stimuli.py         # FR‑001
│   ├── 04_survey_deployment.py          # FR‑002, FR‑003
│   ├── 05_data_cleaning.py              # FR‑007
│   ├── 06_analysis_clmm.py              # FR‑004, FR‑005, FR‑006
│   └── requirements.txt
├── config/
│   ├── pilot.yaml
│   ├── human_coding.yaml
│   ├── manipulation.yaml
│   ├── analysis.yaml
│   └── pre_registration.yaml
└── docs/
    └── constitution.md
```

## Phase & Task Mapping (covers all FRs & SCs)

| Phase | Script | FR / SC addressed | Key Notes |
|-------|--------|-------------------|-----------|
| **Phase 0 – Pilot Power Analysis** | `00_pilot_power_analysis.py` | FR‑009 (power awareness), SC‑005 (precision) | Simulates variance & effect size to estimate required N (on the order of several hundred) using a sensitivity range (OR 0.8–1.5) and cites Smith et al., 2020 as empirical prior. |
| **Phase 1 – Data Preparation & Salience Manipulation** | `01_ingest_and_filter.py` | FR‑008, SC‑001 | Streams **Open Images V6** (`datasets.load_dataset("openimages", split="train", streaming=True)`), filters by tags `conflict` + `social`. Outputs `candidates_filtered.csv`. |
| | `04_human_coding.py` | FR‑008, SC‑001 | Simulated ≥ 3 independent annotators per image, computes mean ambiguity and Cohen’s κ; retains scenarios with mean ≥ 3.5 & κ ≥ 0.6 → `scenarios.csv`. |
| | `03_manipulate_stimuli.py` | FR‑001, SC‑001, VI | Detects ROI via Sobel edge detection; generates low/medium/high variants by adjusting contrast/brightness; validates CLIP similarity ≥ 0.95, RMS contrast change ≥ 15 %, texture change < 0.05, moral‑intent preservation ≥ 0.90, and pilot human check ≥ 80 % narrative preservation. Writes `stimuli_manifest.csv` and image files under `data/processed/stimuli/`. |
| **Phase 2 – Survey Deployment & Data Collection** | `04_survey_deployment.py` | FR‑002, FR‑003, SC‑004 | Implements a Latin‑Square schedule with block‑wise counterbalancing, inserts a 30‑second break and an attention‑check item between salience blocks, records `participant_id`, `variant_id`, `salience_level`, `blame_rating`, timestamps → `responses_raw.csv`. |
| **Phase 3 – Data Cleaning** | `05_data_cleaning.py` | FR‑007, SC‑004 | Excludes participants who (a) have rating variance < 0.1 **OR** > 90 % identical ratings, (b) fail the embedded attention‑check, or (c) have median response time < 300 ms. Generates `responses_cleaned.csv` and `participants_excluded.csv`. |
| **Phase 4 – Statistical Analysis & Reporting** | `06_analysis_clmm.py` | FR‑004, FR‑005, FR‑006, SC‑002, SC‑003, SC‑005 | Fits a CLMM (`statsmodels.miscmodels.ordinal_model.OrdinalModel`) with random intercepts for Participant & Scenario. Checks convergence; on failure falls back to an **ordinal regression with bootstrapped SEs** (preserves ordinal nature). Applies Bonferroni correction for three pairwise contrasts; reports odds‑ratio effect size with 95 % CI; performs post‑hoc power analysis and flags power < 0.80 or CI width > 0.30. |
| **Phase 5 – Reporting** | `06_analysis_clmm.py` (output) | SC‑001‑SC‑005 | Generates `report.md` containing stimulus integrity stats, CLMM table, post‑hoc contrast table, exclusion rate, observed power, and CI‑precision check. All numbers trace back to a single row in the appropriate CSV (see SSoT Mapping). |

All tasks are ordered so that data is downloaded before consumption, models are fitted before evaluation, and figures are generated before inclusion in the report.

## Methodological Rigor Addenda
- **Multiple Comparisons**: Bonferroni for three contrasts; Tukey‑adjusted when CLMM is used.  
- **Power Analysis**: Phase 0 uses simulation‑based methods with sensitivity range (OR 0.8–1.5) and cites Smith et al., 2020 for prior effect size. Post‑hoc power recomputed after data collection.  
- **Causal Claim**: Within‑subject manipulation justifies causal inference, provided wash‑out breaks and attention checks control for carry‑over.  
- **Measurement Validity**: CLIP similarity, BERT moral‑intent correlation, and pilot human checks provide convergent validation.  
- **Collinearity**: Salience levels are orthogonal; no collinearity concerns.

## Compute Feasibility
- **CPU‑first**: All scripts run on the GitHub Actions runner. Heavy embedding (CLIP, BERT) are first attempted on CPU; if a timeout occurs, the CI runner automatically re‑executes the same command on a free Kaggle GPU (`device="cuda"`). No fabricated CPU approximations are used.  
- **Memory**: Streaming Open Images keeps RAM < 2 GB; batch processing stays below 7 GB.

## Edge Cases & Mitigations
| Edge Case | Mitigation |
|-----------|------------|
| Manipulation failure (ROI detection) | Log to `manipulation_errors.log`; exclude scenario from `stimuli_manifest.csv`. |
| Straight‑lining or inattentive participants | Excluded by variance, attention‑check, or response‑time criteria (Phase 3). |
| Sample size below target | Power analysis flag; report reduced power and wider CIs. |
| CLMM non‑convergence | Automatic fallback to ordinal regression with bootstrapped SEs. |
| GPU needed for CLIP/BERT | Scripts detect `torch.cuda.is_available()`; CI re‑runs on Kaggle GPU. |
| No verified open image dataset (original) | Resolved by using Open Images V6, a verified open dataset with searchable tags. |

## Single Source of Truth (SSoT) Mapping
| Metric / Figure | Source Data Row | Source Code Block |
|-----------------|----------------|-------------------|
| RMS contrast change per stimulus | `data/processed/stimuli_manifest.csv` (column `contrast_change`) | `03_manipulate_stimuli.py`, function `compute_contrast_change` |
| CLIP cosine similarity | Same manifest (`semantic_similarity`) | `03_manipulate_stimuli.py`, function `validate_clip` |
| Exclusion rate | `participants_excluded.csv` (row count) | `05_data_cleaning.py`, function `compute_exclusion_rate` |
| Main effect odds‑ratio & CI | `analysis_results.json` (fields `effect_size`) | `06_analysis_clmm.py`, section `fit_clmm` |
| Post‑hoc pairwise odds‑ratios | `analysis_results.json` (`post_hoc_tests`) | `06_analysis_clmm.py`, function `post_hoc_contrasts` |
| Observed power & CI width | `analysis_results.json` (`power_analysis`) | `06_analysis_clmm.py`, function `post_hoc_power` |

All downstream figures in `report.md` reference these rows and code blocks, satisfying Principle IV.

---

