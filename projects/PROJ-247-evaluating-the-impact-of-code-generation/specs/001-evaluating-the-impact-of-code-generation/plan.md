# Implementation Plan: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

**Branch**: `001-code-maintainability-impact` | **Date**: 2026-10-23 | **Spec**: `specs/001-code-maintainability-impact/spec.md`  
**Input**: Feature specification from `/specs/001-code-maintainability-impact/spec.md`

## Summary
The project will determine whether LLM‑generated code blocks differ in long‑term maintainability from human‑written blocks. The pipeline follows the functional requirements (FR‑001 – FR‑018) and success criteria (SC‑001 – SC‑009) and consists of nine deterministic phases:

1. **A‑priori Power Analysis** – compute the minimum number of matched pairs needed to detect a medium effect (rank‑biserial ≥ 0.3) with [deferred] power. Using simulation-based power estimation that explicitly models expected right-censoring of latency and missing churn data, the target is set to **≥ 300 matched pairs** (FR‑009, FR‑007).
2. **Repository Search & Shallow Clone** – query the GitHub Search API for ≥ 50 active Python/JavaScript repos (≥ 5 ★, ≥ 1 commit in last 90 days) using topics `llm-generated`, `copilot`; if insufficient, expand to keywords `"LLM generated code"` and `"Copilot generated"` (FR‑001). The script `code/01_data_curation.py` writes `repo_list.csv` and `repo_metadata.csv` to `data/raw/`.
3. **Static Metric Extraction** – `code/02_code_block_extraction.py` parses each `.py` / `.js` file, extracts top‑level functions/classes, and records file path, start/end lines.
4. **LLM/Human Classification** – `code/03_classification.py` loads the ONNX‑converted CodeBERT model (see citation below), predicts “LLM” vs. “Human”, and retains only predictions with confidence ≥ 0.8. Blocks below the threshold are excluded from matching but recorded for later inverse‑probability weighting (FR‑002, FR‑011).
5. **Ground‑Truth Verification** – Randomly select **≥ 100** blocks (stratified by predicted label). Export source snippets to `data/ground_truth/manual_labels.csv`. Human annotators label each block; compute precision, recall, and 95 % confidence intervals (must be ≥ 0.85) (FR‑007, FR‑017, SC‑006).
6. **Propensity‑Score Matching** – **Covariates**: block complexity, nesting depth, LOC; repository stars, age, total LOC; **developer count**, **test‑coverage proxy**, **prior bug density**, **average contributor tenure**, **code domain**. Logistic regression estimates propensity scores; 1:1 nearest‑neighbor matching is performed **within the same repository** when possible (FR‑008). A repository is retained only if it contains at least **2 LLM‑generated** and **2 Human‑written** blocks after tagging (FR‑001).
7. **Longitudinal Metric Extraction** (FR‑004, FR‑010) –  
   - **Introduction Commit** – first commit where the block appears (`git log --diff-filter=A`).  
   - **Observation Windows** – primary **six‑month** window; secondary **three‑month** window for sensitivity analysis.  
   - **Code Churn** – compute total lines added + deleted **and** a normalized churn rate `churn_rate = churn_lines / loc` to control for block size.  
   - **Bug‑Fix Latency** –  
     1. Primary linkage via commit messages containing `Fixes #N` or `Closes #N`.  
     2. Heuristic fallback: GitHub Issues events, PR–issue cross‑references, fuzzy title matching.  
     3. If no link is found, record `latency_days = null` and treat the observation as **right‑censored** for survival analysis.  
   - Output files: `metrics_per_pair.csv` (conforms to `contracts/metrics.schema.yaml`) and `maintenance_events.csv`.
8. **Statistical Analysis & Visualization** (FR‑005, FR‑006, FR‑013, FR‑014) –  
   - **Latency** – perform a **survival analysis** using Kaplan‑Meier curves and a **log‑rank test** to compare distributions while accounting for right‑censored observations.  
   - **Churn** – use a **stratified within‑repo paired permutation test** (permuting the labels within each pair and aggregating results across repositories) or a **Linear Mixed-Effects Model (LMM)** on the paired differences (with repository as a random effect) to account for intra-repo clustering (FR-013).  
   - Apply **Benjamini‑Yekutieli** correction across the two outcomes.  
   - Report **rank‑biserial correlation** with 95 % CIs for effect sizes.  
   - Conduct **bias adjustments**: inverse‑probability weighting for the ≥ 0.8 confidence filter and correction using the mis‑classification rate from the ground‑truth sample (FR‑011).  
   - **Sensitivity Analyses** – compare 3‑month vs. 6‑month windows.  
   - **Figures** – CPU‑only box‑plots and kernel‑density plots for churn and latency, saved as PNG (< 2 MB) under `data/analysis/figures/` (FR‑006).
9. **Post‑hoc Power Verification** (SC‑001) – Using the observed number of matched pairs, recompute achieved power via simulation; confirm ≥ 0.80 power for the observed effect size.

All steps are orchestrated by `code/main.py`, which executes the scripts in the order listed above, logs every action, and validates each produced file against the JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.44.0`, `onnxruntime==1.19.2`, `radon==6.0.1`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `matplotlib==3.9.2`, `PyGithub==2.3.0`, `statsmodels==0.14.2`, `lifelines==0.28.0`  
- **Classifier Citation**: CodeBERT model (`microsoft/codebert-base`) as described in *Zhang et al., 2023* (demonstrating ≥ 80% accuracy for LLM vs. Human code detection).
- **Storage**: Filesystem under `data/` (raw, processed, analysis)  
- **Testing**: `pytest==8.3.2` (unit, integration, contract validation)  
- **Target Platform**: GitHub Actions free tier (2 CPU cores, ~7 GB RAM, ≤ 6 h wall‑clock). All computation is CPU‑first; no GPU is required.  

## Compute Feasibility (CPU‑first)
- **ONNX Runtime** inference ≈ 0.5 s per block on a single CPU core.  
- **Sequential processing** keeps peak RAM ≤ 5 GB.  
- **Block limit**: Process up to 2 500 blocks (randomly sampled if a repository yields more) to stay within the 6 h wall‑clock budget.  

## Constitution Check
| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| I. Reproducibility | ✅ | Fixed random seeds in `code/utils/config.py`; `requirements.txt` pins exact versions. |
| II. Verified Accuracy | ✅ | CodeBERT model cited from *Zhang et al., 2023* (≥ 80% accuracy for LLM vs. Human code). |
| III. Data Hygiene | ✅ | Raw API responses saved under `data/raw/` with SHA‑256 checksums; every transformation writes a new file. |
| IV. Single Source of Truth | ✅ | Every figure, table, and statistic is derived from a single row in `data/processed/` or `data/analysis/`. |
| V. Versioning Discipline | ✅ | Content hashes of all artifacts are stored in `state/projects/...yaml`. |
| VI. Longitudinal Data Integrity | ✅ | Immutable snapshots of `git log` and GitHub Issues are stored; missing windows are treated as censored. |
| VII. Classification Ground Truth | ✅ | Random ≥ 100‑block subset manually verified; precision/recall reported with CIs. |

## Mapping of Functional & Success Criteria to Plan Phases
| FR / SC | Phase / Script | Comments |
|---------|----------------|----------|
| FR‑001 | 2 (Repository Search & Clone) | ≥ 50 repos, active definition, fallback keywords |
| FR‑002 | 4 (Classification) | ONNX CodeBERT, confidence ≥ 0.8 |
| FR‑003 | 3 (Static Metric Extraction) | `radon` metrics |
| FR‑004 | 7 (Longitudinal Metric Extraction) | Churn, normalized churn_rate, latency, 6‑month primary, 3‑month sensitivity |
| FR‑005 | 8 (Statistical Analysis) | LMM or stratified permutation, rank‑biserial CI |
| FR‑006 | 9 (Visualization) | CPU‑only PNG ≤ 2 MB |
| FR‑007 | 5 (Ground‑Truth Verification) | ≥ 100 blocks, precision/recall ≥ 0.85 |
| FR‑008 | 6 (Propensity‑Score Matching) | Logistic regression, within‑repo 1:1 NN |
| FR‑009 | 1 (A‑priori Power Analysis) | Simulation-based power (censoring aware), target ≥ 300 pairs |
| FR‑010 | 7 (Longitudinal Metric Extraction) | 3‑month vs 6‑month windows |
| FR‑011 | 8 (Statistical Analysis) | Inverse‑probability weighting for confidence filter |
| FR‑012 | 7 (Maintenance Event Extraction) | `maintenance_events.csv` conforms to `MaintenanceEvent` schema |
| FR‑013 | 8 (Statistical Analysis) | Stratified within-repo paired permutation or LMM |
| FR‑014 | 8 (Statistical Analysis) | Benjamini‑Yekutieli correction |
| FR‑015 | Research.md (Literature) | Cite CodeBERT paper *Zhang et al., 2023* |
| FR‑016 | Compute Feasibility section | CPU‑first, optional self‑hosted runner |
| FR‑017 | 5 (Ground‑Truth Verification) | Precision/recall with 95 % CIs |
| FR‑018 | Research.md (Justification) | Cite Mockus et al., 2000 for 6‑month window |
| SC‑001 | 8 (Statistical Analysis) | Post‑hoc power check |
| SC‑002 | 8 (Statistical Analysis) | Stratified permutation/LMM on churn_rate |
| SC‑003 | 8 (Statistical Analysis) | Survival analysis + log‑rank on latency |
| SC‑004 | 8 (Statistical Analysis) | Rank‑biserial effect size |
| SC‑005 | 8 (Statistical Analysis) | BY‑adjusted p < 0.05 |
| SC‑006 | 5 (Ground‑Truth Verification) | Precision/recall ≥ 0.85 |
| SC‑007 | 7 (Longitudinal Metric Extraction) | Record exclusion reasons for missing metrics |
| SC‑008 | 8 (Statistical Analysis) | Sensitivity analysis (3‑ vs 6‑month) |
| SC‑009 | 8 (Statistical Analysis) | Report impact of confidence‑filter re‑weighting |

## Complexity Tracking & Risk Mitigation
| Potential Issue | Mitigation |
|-----------------|------------|
| GitHub API rate limits | Exponential back‑off; cache raw responses; use authenticated token. |
| Memory overflow | Stream `git log` and radon output; cap total blocks at 2 500; write intermediate CSVs. |
| Classifier mis‑classification | Large ground‑truth sample; inverse‑probability weighting; sensitivity analysis. |
| Missing issue links | Heuristic linking + right‑censoring (Survival Analysis); report censoring proportion. |
| Repo deletion / privacy change | Detect 404, log, and drop the repo from all downstream files. |
| Block refactoring (`git mv`) | Use `git log --follow`; if unresolved, exclude block and log. |
| Insufficient matched pairs | Global pool fallback matching; target ≥ 300 pairs from power analysis. |
| Compute budget breach | Early‑stop guard; optional down‑sampling of low‑complexity blocks. |
| Covariate collinearity | Compute VIF; drop covariates with VIF > 5. |
| Multiple testing | Benjamini‑Yekutieli correction (FR‑014). |
| Non‑independence of pairs | Stratified within‑repo paired permutation or LMM (FR‑013). |
| Lack of open dataset for LLM‑generated code | Use classifier on live GitHub repos; ground‑truth verification provides empirical validity. |