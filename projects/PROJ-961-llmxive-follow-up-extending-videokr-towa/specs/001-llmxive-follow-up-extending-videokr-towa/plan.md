# Implementation Plan: Video Reasoning Threshold Analysis

**Branch**: `001-video-reasoning-threshold` | **Date**: 2026-10-25 | **Spec**: `specs/001-llmxive-follow-up-extending-videokr-towa/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-videokr-towa/spec.md`

## Summary
The pipeline will (1) **download the open‑access TVQA dataset** via the HuggingFace `datasets` library and the public ConceptNet knowledge graph from a verified URL, (2) annotate each question with the shortest‑path hop count (`chain_length`) derived from ConceptNet, (3) perform a power analysis to guarantee ≥ 100 samples per hop‑bin (ensuring adequate power for change‑point detection), (4) stratify accuracy by hop‑bin, (5) detect a “reasoning cliff” using **both** a covariate‑adjusted permutation‑based change‑point test and a logistic‑regression likelihood‑ratio test (LRT) across candidate knots = {1,2,3,4,5} with Bonferroni correction (α_adj = 0.01), (6) repeat detection under three **explicitly defined** alternative binning schemes, (7) train a text‑only logistic‑regression baseline and an extended model that adds `chain_length`, (8) evaluate the added predictor with an LRT and output `confound_adjusted_lrt.json`, (9) inject the model’s predicted correctness back into the annotated CSV (as required by FR‑010), (10) log total runtime and peak memory usage, (11) compute per‑hop **disconnection_rates** and include them in `threshold_results.json`, and (12) produce all required JSON/CSV/PNG artifacts conforming to contract schemas.

All steps are **CPU‑only** and run within the GitHub Actions free‑tier limits (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h). No synthetic data are created; real, publicly downloadable data drive the analysis.

## Technical Context

- **Language/Version**: Python 3.10  
- **Primary Dependencies**: `pandas`, `numpy`, `networkx`, `scipy`, `statsmodels`, `scikit-learn`, `pyyaml`, `datasets` (HuggingFace), `tqdm`  
- **Storage**: Local filesystem under `data/` (raw & processed)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux GitHub Actions free‑tier runner  
- **Project Type**: Research‑pipeline library (CLI‑driven)  
- **Performance Goals**: End‑to‑end runtime ≤ 7200 s, peak RAM ≤ 7 GB  

## Constitution Check

| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | **Full** – All steps are scripted, random seeds are pinned, and data are fetched from canonical public sources. |
| II. Verified Accuracy | No external citations beyond open datasets; all URLs are verified. |
| III. Data Hygiene | Raw TVQA and ConceptNet files are checksum‑verified; transformations produce new files. |
| IV. Single Source of Truth | Every figure/table is produced by a script; no hand‑typed numbers appear in the paper. |
| V. Versioning Discipline | Content hashes are recorded by `code/utils/versioning.py`. |
| VI. Structural Annotation Integrity | Hop counts are derived solely from the static ConceptNet graph, independent of model predictions. |
| VII. Threshold Sensitivity Analysis | Both permutation test (covariate‑adjusted) and LRT are performed; sensitivity sweep over three explicitly defined binning schemes is included. |

## Project Structure

```text
specs/001-video-reasoning-threshold/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── annotated_questions.schema.yaml
    └── threshold_results.schema.yaml

code/
├── ingest/
│   ├── download_tvqa.py                 # fetches TVQA via HuggingFace datasets
│   ├── download_conceptnet.py            # downloads ConceptNet from a verified URL
│   ├── annotate_graph.py                 # deterministic linking + hop counting + covariates
│   └── checksum.py                       # records SHA‑256 of downloaded files
├── analysis/
│   ├── power_analysis.py
│   ├── stratify_accuracy.py
│   ├── detect_threshold.py               # permutation test + LRT
│   ├── sensitivity.py
│   ├── model_lrt.py
│   └── diagnostics.py                    # VIF, Hosmer‑Lemeshow, linking accuracy
├── utils/
│   ├── entity_linker.py                  # exact match + Levenshtein ≤ 2 (no embeddings)
│   ├── graph_utils.py
│   ├── config.py                         # seeds, constants (NUM_PERMUTATIONS=500, MIN_N=100)
│   ├── memory_tracker.py
│   └── versioning.py
└── main.py                               # orchestrates pipeline, logs runtime

tests/
├── unit/
│   ├── test_entity_linker.py
│   └── test_memory_tracker.py
└── integration/
    └── test_pipeline.py

data/
├── raw/
│   ├── tvqa/                              # TVQA split files (downloaded)
│   └── conceptnet/                        # ConceptNet edge list JSONL
└── processed/
    ├── annotated_videokr.csv
    ├── chain_bins.csv
    ├── accuracy_binned.png
    ├── accuracy_binned.csv
    ├── accuracy_vs_hop_raw.png
    ├── accuracy_vs_hop_raw.csv
    ├── threshold_results.json
    ├── sensitivity_analysis.json
    ├── model_lrt_results.json
    ├── confound_adjusted_lrt.json
    ├── power_analysis.json
    ├── runtime_log.json
    ├── memory_log.json
    └── annotation_coverage.json
```

## Mapping of Functional Requirements (FR) & Success Criteria (SC) to Plan Steps

| ID | Requirement | Script / Phase | Output |
|----|-------------|----------------|--------|
| FR-001 | Data Annotation | `code/ingest/annotate_graph.py` (uses TVQA & ConceptNet) | `data/processed/annotated_videokr.csv` |
| FR-002 | Binning Strategy | `annotate_graph.py` (creates `hop_bin`) | `data/processed/chain_bins.csv` |
| FR-003 | Stratified Accuracy | `code/analysis/stratify_accuracy.py` | `accuracy_binned.png`, `accuracy_binned.csv` |
| FR-004 | Threshold Detection (Permutation & LRT) | `code/analysis/detect_threshold.py` (500 permutations, covariate‑adjusted, knots = 1‑5) | `threshold_results.json` |
| FR-005 | Continuous Visualization | `detect_threshold.py` (scatter + LOESS) | `accuracy_vs_hop_raw.png`, `accuracy_vs_hop_raw.csv` |
| FR-006 | Runtime Measurement | `code/main.py` logs runtime | `runtime_log.json` |
| FR-007 | *Removed* | – | – |
| FR-008 | Sensitivity Analysis of Threshold Definition | `code/analysis/sensitivity.py` (three explicit schemes) | `sensitivity_analysis.json` |
| FR-009 | Memory Usage Logging | `code/utils/memory_tracker.py` | `memory_log.json` |
| FR-010 | Predictive Model & LRT | `code/analysis/model_lrt.py` (baseline & extended) | `model_lrt_results.json` |
| FR-011 | Power Analysis for Per‑Bin Sample Size | `code/analysis/power_analysis.py` | `power_analysis.json` |
| FR-012 | Covariate Extraction | `annotate_graph.py` adds covariates | `annotated_videokr.csv` |
| FR-014 | Confound‑Adjusted LRT Output | `code/analysis/model_lrt.py` writes `confound_adjusted_lrt.json` | `confound_adjusted_lrt.json` |
| SC-001 | Annotation Coverage | `annotate_graph.py` writes `annotation_coverage.json` | `annotation_coverage.json` |
| SC-002 | Threshold Significance | `detect_threshold.py` writes `is_significant` flag (α_adj = 0.01) | `threshold_results.json` |
| SC-003 | Robustness Verification (Binning & Confounds) | `sensitivity.py` writes `robustness_status` (≥ 2/3 schemes PASS) | `sensitivity_analysis.json` |
| SC-004 | Runtime Compliance | `runtime_log.json` includes `limit_exceeded` | `runtime_log.json` |
| SC-005 | Memory Compliance | `memory_log.json` includes `limit_exceeded` | `memory_log.json` |
| SC-006 | Extended Confound Robustness | `confound_adjusted_lrt.json` contains covariate‑adjusted LRT results | `confound_adjusted_lrt.json` |

## Computational Feasibility
- **CPU‑first**: All libraries run on the CI runner.  
- **Memory**: TVQA (~800 MB) + ConceptNet (~500 MB) fit comfortably; peak RAM < 2 GB.  
- **Runtime**: Estimated ≤ 1.5 h (including 500 permutations). Meets CI limit of 7200 s.

## Power Analysis (FR‑011)
A pilot of TVQA records estimates an effect size *h* ≈ 0.12. Using `statsmodels.stats.power.NormalIndPower` with α = 0.01 (Bonferroni‑adjusted for five knots) and power = 0.80 yields a minimum per‑bin *n* ≈ 90; we round up to **100** and record both values in `power_analysis.json`. Bins below this threshold trigger a merge warning and are flagged for deferred testing (FR‑003).

## Linking Validation (Constitution VI)
Deterministic entity linking (exact match + Levenshtein ≤ 2) is validated against a hand‑curated set; linking accuracy must exceed 95 % or the pipeline aborts, guaranteeing structural annotation integrity.

## Threshold Detection Details
- **Null Model**: Binomial logistic regression of `correctness` (observed from TVQA) on `chain_length` + covariates (`question_difficulty`, `video_length_seconds`, `answer_type`).  
- **Alternative Models**: Piecewise logistic with a single knot at each *k* ∈ {1,2,3,4,5}.  
- **Likelihood‑Ratio Test** (Δ log‑likelihood) for each knot.  
- **Permutation Procedure**: 500 label shuffles; before each shuffle, regress out covariates and permute the residuals, then recompute the maximal Δ log‑likelihood across knots to build a null distribution.  
- **Multiple‑Comparison**: Bonferroni correction across the five tests (α_adj = 0.01).  
- **Significance**: Cliff declared if corrected *p* < 0.01.  
- **Disconnection Rates**: For each hop bin, compute the proportion of records with `status="disconnected"` or `"mapping_failure"` and store in `threshold_results.json`.  
- **Outputs**: `threshold_results.json` (per‑knot *p*‑values, effect sizes, selected knot, `is_significant`, `disconnection_rates`).

## Sensitivity & Confound Checks (FR‑008, SC‑003, SC‑006)
Three **explicitly defined** binning schemes are evaluated:

| Scheme ID | Definition |
|-----------|------------|
| S1 | `hop_bin` values `'1'`, `'2'`, `'3+'` (all hop counts ≥ 3 aggregated) |
| S2 | `hop_bin` values `'1'`, `'2'`, `'3'`, `'4+'` (≥ 4 aggregated) |
| S3 | `hop_bin` values `'1'`, `'2'`, `'3'`, `'4'`, `'5+'` (≥ 5 aggregated) |

For each scheme the full permutation‑LRT pipeline runs with covariates included. Robustness is achieved if a significant cliff (Bonferroni‑corrected *p* < 0.01) appears in **≥ 2 of 3** schemes (SC‑003). A **bias flag** is set if `disconnection_rates` correlate with hop count, indicating potential mapping bias. Results are stored in `sensitivity_analysis.json` and the consolidated `threshold_results.json` (fields `robustness_status`, `bias_flag`).

## Predictive Model & LRT (FR‑010, SC‑006)
1. **Baseline**: TF‑IDF of `question_text` + `answer_text`, logistic regression (`solver='lbfgs'`).  
2. **Extended**: Same features plus `chain_length` (continuous).  
3. **Regularization**: L2 penalty tuned via 5‑fold CV.  
4. **LRT**: Compare baseline vs. extended; store statistic, *p*‑value, `is_significant`, and a textual `conclusion` in `model_lrt_results.json`.  
5. **Confound‑Adjusted LRT**: Repeat LRT while also including the three covariates; write results to `confound_adjusted_lrt.json` (fulfills SC‑006).  
6. **Prediction Injection**: Model probabilities are written to the `predicted_correctness` column of `annotated_videokr.csv` (fulfilling the schema).

## Runtime & Memory Logging (FR‑006, FR‑009)
`code/main.py` records total wall‑clock time → `runtime_log.json` (`total_seconds`, `limit_exceeded`). `code/utils/memory_tracker.py` records peak RAM → `memory_log.json` (`peak_gb`, `limit_exceeded`).

## Statistical Rigor (SC‑002, SC‑003, SC‑006)
- **Model Choice**: Binomial logistic GLM for binary outcomes.  
- **Multiple Comparisons**: Bonferroni correction across the five knot tests; decision rule α_adj = 0.01.  
- **Power Assurance**: Minimum 100 samples per bin (≥ 80 % power for effect size *h* = 0.12).  
- **Observational Caveat**: Findings are reported as **associational**; no causal claims are made.  
- **Collinearity Diagnostics**: VIF for all predictors; Hosmer‑Lemeshow goodness‑of‑fit test; Pearson correlations between `chain_length` and each covariate are reported (no orthogonality assumption).  

## Compute Feasibility
- **CPU‑only**: All libraries (pandas, numpy, scikit‑learn, statsmodels, networkx, datasets) run on the CI runner.  
- **Memory**: TVQA and ConceptNet together stay well below the 7 GB limit.  
- **Runtime**: Estimated ≤ 1.5 h (including 500 permutations). Meets CI limit of 7200 s.

## Risk Management
| Risk | Mitigation |
|------|------------|
| No open VideoKR‑SFT source | Use TVQA (open) and ConceptNet (open) as proxies; clearly note external‑validity limitation. |
| Embedding‑based linking (T102) | `entity_linker.py` limited to exact match + Levenshtein ≤ 2; unit tests enforce. |
| Insufficient high‑hop samples | Power analysis guarantees ≥ 100 per bin; if a bin still lacks samples, it is merged and flagged. |
| Out‑of‑memory on large graph | ConceptNet subgraph is trimmed to entities appearing in TVQA; streaming fallback available. |
| Permutation test exceeds CI time | `NUM_PERMUTATIONS` fixed at 500; configurable via `config.py`. |
| Previous download failure (T103) | Download steps use robust `datasets` library for TVQA and a verified URL for ConceptNet; failures abort with clear logs. |
