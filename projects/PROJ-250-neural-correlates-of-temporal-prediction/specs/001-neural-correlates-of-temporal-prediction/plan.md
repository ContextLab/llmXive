# Implementation Plan: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis  

**Branch**: `001-temporal-prediction-errors` | **Date**: 2026-10-25 | **Spec**: `specs/001-neural-correlates-of-temporal-prediction/spec.md`  
**Input**: Feature specification from `specs/001-neural-correlates-of-temporal-prediction/spec.md`

## Summary  
The project aims to (1) obtain an open‑access EEG dataset that contains both “simple” oddball and “complex” auditory‑scene conditions, (2) run a fully reproducible MNE‑Python preprocessing pipeline (1–40 Hz band‑pass, ICA, average‑mastoid reference, –200 ms → 500 ms epoching), (3) quantify MMN amplitude, latency, and topography per subject, (4) enforce signal‑quality criteria (SNR ≥ 3, ≥ 80 % topographic consistency), (5) test the hypothesis that MMN metrics scale with scene complexity using paired t‑tests with Benjamini‑Hochberg FDR correction, (6) compare observed Cohen’s d to a literature benchmark (≥ 0.5), (7) generate publication‑quality ERP and scalp‑map figures, and (8) validate every artifact against JSON/YAML contracts.  

**Critical blocker:** No verified, programmatically downloadable EEG dataset containing the required “simple” and “complex” condition labels is present in the verified‑datasets list. Consequently, the pipeline includes a *Dataset‑Gap* checkpoint that **halts execution until an appropriate open dataset is added** or the project scope is revised.

## Technical Context  

| Item | Detail |
|------|--------|
| **Language/Version** | Python 3.11 |
| **Primary Dependencies** | `mne>=1.7.0`, `numpy`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pytest`, `datasets` (🤗 HuggingFace) |
| **Storage** | Files under `data/` (raw, processed, templates, benchmarks) and `results/` (metrics, stats, figures) |
| **Testing** | `pytest` contract tests against `contracts/*.schema.yaml` |
| **Target Platform** | Linux GitHub Actions free tier (2 CPU cores, ≤7 GB RAM, ≤6 h) |
| **Compute Model** | **CPU‑first** – all steps run on NumPy/SciPy/MNE; no GPU required |
| **Constraints** | No fabricated dataset; all external URLs must be from the verified list; any missing requirement is reported as a fatal gap. |

## Constitution Check  

| Principle | Status | Comments |
|-----------|--------|----------|
| I. Reproducibility | **PASS** (deterministic seeds, pinned `requirements.txt`) |
| II. Verified Accuracy | **PASS** (Reference‑Validator invoked at three gates) |
| III. Data Hygiene | **PASS** (raw BIDS never overwritten; SHA‑256 recorded) |
| IV. Single Source of Truth | **PASS** (all figures/statistics trace to `results/metrics.csv` & `results/stats.json`) |
| V. Versioning Discipline | **PASS** (artifact hashes stored in `state/projects/...yaml`) |
| VI. Neurophysiological Signal Integrity | **PASS** (band‑pass, ICA, mastoid reference, epoch window hard‑coded) |
| VII. Statistical Rigor for ERP Comparison | **PASS** (paired t‑tests, FDR, Cohen’s d, topographic checks) |
| **Dataset‑Gap** | **FAIL** | Required “simple” **and** “complex” EEG dataset not present in verified list. Pipeline aborts at *Dataset‑Gap* checkpoint (Phase 0). |

## Project Structure  

```text
specs/001-neural-correlates-of-temporal-prediction/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── stats.schema.yaml

projects/PROJ-250-neural-correlates-of-temporal-prediction/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── dataset_gap.py          # Phase 0: dataset availability check
│   ├── download.py             # FR‑001 (conditional)
│   ├── preprocess.py           # FR‑002, FR‑003
│   ├── analysis.py             # FR‑004‑FR‑011, FR‑009‑FR‑010, FR‑016, covariate modelling
│   ├── visualize.py            # FR‑006
│   ├── verify_references.py    # FR‑012 helper
│   └── ... (other helper modules)
├── data/
│   ├── raw/                    # populated only if dataset passes Phase 0
│   ├── processed/
│   ├── templates/
│   │   └── canonical_mmn.npy   # generated in Phase 3 (FR‑009)
│   └── benchmarks/
│       └── mmn_effect_sizes.json   # location referenced in FR‑010
├── results/
│   ├── metrics.csv
│   ├── stats.json
│   └── figures/
│       ├── erp.png
│       ├── topography_simple.png
│       └── topography_complex.png
└── state/
    └── projects/
        └── PROJ-250-neural-correlates-of-temporal-prediction.yaml
```

## Implementation Phases & FR/SC Mapping  

| Phase | Core Tasks | FRs Covered | SCs Covered |
|-------|------------|-------------|--------------|
| **Phase 0 – Dataset‑Gap Check** | `dataset_gap.py` loads the list of verified URLs. It **searches for a dataset that (a) is openly downloadable via `datasets.load_dataset` or direct URL, **and** (b) contains an `events.tsv` with a `condition_label` column enumerating **both** “simple” **and** “complex” trials**. If none is found, the script aborts with a clear error message *“Dataset lacks required ‘complex’ condition; research question untestable with current data.”* (fulfills FR‑008 abort behavior). | FR‑008, FR‑012‑1 | – |
| **Phase 1 – Data Acquisition** *(conditional on Phase 0 success)* | `download.py`: download dataset, verify SHA‑256 checksums, record hashes in `state/...yaml` (fulfills SC‑007), and create an **EEGDataset** record in the data model. | FR‑001, FR‑013, SC‑007 | – |
| **Phase 2 – Preprocessing** | `preprocess.py`: <br>• Band‑pass 1–40 Hz (FIR, zero‑phase) <br>• ICA (`n_components=0.99`, `random_state=42`) <br>• Average‑mastoid re‑reference (`TP9`, `TP10`) <br>• Baseline correction (‑200 ms → 0 ms) <br>• Epoch –200 ms → 500 ms, label by `condition_label` (creates **Epoch** objects) <br>• Exclude subjects with > 50 % rejected epochs <br>• Interpolate missing channels (<10 % missing) <br>• **NaN check**: assert `np.isnan(epochs.get_data()).any() == False` (SC‑008). <br>• Populate **Subject** entries with QC info. | FR‑002, FR‑003, FR‑008 (re‑check), SC‑008 | – |
| **Phase 3 – Core MMN Analyses** | `analysis.py`: <br>• Verify both conditions still present (FR‑008, FR‑012‑2). <br>• Compute MMN amplitude & latency (150–250 ms, fronto‑central cluster) (FR‑004). <br>• Compute pre‑stimulus noise floor; calculate SNR = \|amplitude\| / SEM; enforce **SNR ≥ 3** (FR‑011, **mapped to SC‑001**). <br>• Generate **Leave‑One‑Out canonical topography** from the *simple* condition and save to `data/templates/canonical_mmn.npy` (FR‑009, path now explicit). <br>• Pearson‑r consistency (simple vs. LOO) & validity (complex vs. LOO) ≥ 0.8 (SC‑004). <br>• Paired t‑test with Benjamini‑Hochberg FDR across electrode cluster (FR‑005, SC‑002). <br>• Compute Cohen’s d and compare against benchmark loaded from `data/benchmarks/mmn_effect_sizes.json` (FR‑010, **explicit path added**; SC‑003). <br>• **Power analysis**: using `statsmodels.stats.power.TTestPower` with α = 0.05, power = 0.8, effect size = 0.5 → required N. If post‑QC N < required, **abort confirmatory testing**, flag results as exploratory, and log warning (FR‑016, **explicit SC‑006 mapping**). <br>• **Covariate modelling**: if stimulus‑level covariates (e.g., deviant probability, ISI, acoustic features) are present, fit a mixed‑effects model (`statsmodels.MixedLM`) with condition as fixed effect, covariates as additional fixed effects, and subject as random intercept. Report fixed‑effect estimate, SE, and p‑value as a robustness check (addresses methodology‑0f0359eb). <br>• Write per‑subject **MMNMetric** rows to `results/metrics.csv` (FR‑015 aggregation). <br>• Write group‑level **GroupStats** to `results/stats.json`. | FR‑004, FR‑005, FR‑008, FR‑009, FR‑010, FR‑011, FR‑012‑2, FR‑016, **covariate modelling added**, SC‑001, SC‑002, SC‑003, SC‑004, SC‑006 | – |
| **Phase 4 – Visualization & Reporting** | `visualize.py`: <br>• ERP waveforms with MMN window highlighted <br>• Scalp topography maps for simple & complex conditions <br>• Significance heatmaps <br>• Save PNG/SVG files to `results/figures/` (FR‑006). <br>• **SC‑005 verification**: after each save, assert file exists and size > 0 KB; raise error on failure. | FR‑006, FR‑012‑3 | SC‑005 |
| **Phase 5 – Contract Validation** | `pytest` suite validates: <br>• `data/raw/` metadata against `contracts/dataset.schema.yaml` <br>• `results/metrics.csv` against `contracts/output.schema.yaml` (covers SC‑005‑SC‑009) <br>• `results/stats.json` against `contracts/stats.schema.yaml` <br>• Execute `verify_references.py` to run the Reference‑Validator **before reporting** (fulfills FR‑012‑3). <br>• Ensure that the aggregated **StatisticalResult** is embedded within each **MMNMetric** as required by FR‑015. | FR‑014, FR‑015, FR‑012‑3 | SC‑005, SC‑006, SC‑007, SC‑008, SC‑009 |
| **Phase 6 – State Update** | Record all artifact hashes and timestamps in `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml` (FR‑013, Constitution Principle V). | FR‑013 | – |

All functional requirements (FR‑001 … FR‑016) and success criteria (SC‑001 … SC‑009) are now **explicitly mapped** to concrete phases. Any FR that cannot be satisfied because the required dataset is missing is reported as a fatal gap in Phase 0, prompting a scope revision rather than a fabricated data source.

## Compute Feasibility  
* **CPU‑first**: All heavy computations run on NumPy/SciPy/MNE; fully CPU‑compatible.  
* **Memory Management**: Process subjects sequentially; each `Epochs` object saved to disk (`.fif`) and loaded on demand, keeping RAM < 6 GB.  
* **Runtime Estimate**: [deferred] per subject; full cohort (< 20 subjects) comfortably fits within the 6 h CI limit.  
* **No GPU** required.  

---


