# Implementation Plan: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

**Branch**: `001-code-maintainability-impact` | **Date**: 2026-10-12 | **Spec**: `specs/001-code-maintainability-impact/spec.md`  
**Input**: Feature specification from `/specs/001-code-maintainability-impact/spec.md`

## Summary
The project will answer whether code blocks classified as “LLM‑generated” differ in long‑term maintainability from human‑written blocks. The pipeline consists of:

1. **Curation** – Search, shallow‑clone, and record repository‑level covariates (stars, age, total LOC).  
2. **Extraction & Tagging** –  
   - Extract top‑level functions/classes from each `.py`/`.js` file.  
   - Compute static metrics (cyclomatic complexity, nesting depth, LOC) with `radon`.  
   - Classify each block with the ONNX‑converted CodeBERT model, retaining only blocks with confidence ≥ 0.8. Blocks below this threshold are excluded and later re‑weighted via inverse‑probability weighting.  
   - Record all metrics in `data/processed/tagged_blocks.csv`.  
3. **Ground‑Truth Verification** – Randomly select **≥ 100** blocks (stratified by predicted label) for manual labeling; export source snippets to `data/ground_truth/manual_labels.csv`. Compute precision and recall with 95 % confidence intervals; both must be ≥ 0.85. The observed mis‑classification rate is later used for bias correction in the analysis.  
4. **Propensity‑Score Matching** –  
   - **Covariates**: block‑level complexity, nesting depth, LOC; repo‑level stars, age, total LOC; **developer experience** (author commit count), **test‑coverage proportion** (when a coverage file exists), **prior bug density** (bugs per LOC in the preceding 3 months), and optional **code‑domain tags**.  
   - **Model**: Logistic regression (scikit‑learn) to estimate propensity scores.  
   - **Matching**: 1:1 nearest‑neighbor *within the same repository* when possible; otherwise, blocks are matched in a pooled global pool.  
   - **Filtering**: Repositories lacking ≥ 5 LLM‑generated and ≥ 5 Human‑written blocks after tagging contribute their blocks to the global pool rather than being discarded.  
   - **Result** – `matched_pairs.csv` (per‑pair IDs, propensity scores, and repository metadata).  
5. **Longitudinal Metric Extraction** –  
   - **Introduction Commit** – First commit where the block appears (detected via `git log --diff-filter=A`).  
   - **Observation Window** – Six months after that timestamp (primary) and nine months for sensitivity analysis.  
   - **Code Churn** – Sum of `lines_added` + `lines_deleted` for each block within the window, excluding the introduction commit.  
   - **Bug‑Fix Latency** –  
     1. Primary linkage: commits whose message contains `Fixes #N` or `Closes #N`.  
     2. Heuristic fallback: GitHub Issues events, PR–issue cross‑references, and fuzzy matching of issue titles/descriptions within ±3 days of the commit.  
     3. If still unlinked, latency is recorded as `null` and treated as a right‑censored observation; such cases are excluded from the latency test but retained for churn analysis, with the censoring proportion reported.  
   - **Output** – `metrics_per_pair.csv` (per‑pair churn & latency, conforms to `contracts/metrics.schema.yaml`) and `maintenance_events.csv` (individual churn/bug‑fix events, conforms to the `MaintenanceEvent` entity).  
6. **Maintenance Event Extraction** – Dedicated script extracts every churn and bug‑fix event, stores them in `data/processed/maintenance_events.csv`, and links each event to its `block_id`.  
7. **Statistical Analysis & Visualization** –  
   - **A‑priori Power Analysis** – Paired Wilcoxon, effect size d = 0.5, α = 0.05, power = 0.80 → requires **≥ 34** matched pairs; we target **≥ 40** pairs before data collection. Power calculation performed with `statsmodels.stats.power`.  
   - **Cluster‑Robust Wilcoxon** – Perform signed‑rank tests **within each repository**, then combine via a weighted Z‑method that accounts for intra‑repo correlation.  
   - **Multiple‑Comparison** – Benjamini‑Hochberg FDR correction across the two outcomes (churn, latency).  
   - **Effect Size** – Report **rank‑biserial correlation (rᵣ)** derived from the Wilcoxon statistic (consistent with the non‑parametric test).  
   - **Bias Adjustments** – Apply inverse‑probability weighting to correct for the confidence‑filter exclusion and adjust effect sizes using the mis‑classification rate from the ground‑truth sample.  
   - **Sensitivity Analyses** –  
     - Vary observation window (6 vs 9 months).  
     - Re‑weight results using the inverse‑probability weights.  
     - Adjust effect sizes for classifier error.  
   - **Figures** – Box plots and kernel‑density plots for churn and latency, saved as PNG under `data/analysis/figures/` (≤ 10 MB, CPU‑only `matplotlib`).  
8. **Output Artifacts** – All CSV/JSON files are immutable, checksummed, and validated against the JSON‑Schema contracts in `contracts/`.  

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.44.0`, `onnxruntime==1.19.2`, `radon==6.0.1`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `matplotlib==3.9.2`, `PyGithub==2.3.0`  
- **Storage**: Local filesystem under `data/` (raw, processed, ground_truth, analysis).  
- **Testing**: `pytest==8.3.2` (unit, integration, contract validation).  
- **Target Platform**: GitHub Actions free tier (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h).  

## Compute Feasibility (CPU‑first)
- **ONNX Runtime** enables CodeBERT inference on CPU (~0.5 s per block).  
- **Batch Processing** – Process repositories sequentially; stream `radon` analysis per file to keep peak RAM ≤ 5 GB.  
- **Block Limit** – At most **2 000** blocks are processed (randomly sampled if more).  
- **Early‑Stop Guard** – Abort if wall‑clock > 5.5 h; optionally down‑sample low‑complexity blocks.  
- **No GPU Required** – All steps run on CPU; optional down‑sampling if runtime exceeds budget.  

## Constitution Check
| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| **I. Reproducibility** | ✅ | Fixed random seeds in `code/config.py`; all scripts deterministic given the same token and API timestamps; `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | ✅ | CodeBERT model cited from HuggingFace (`https://huggingface.co/microsoft/codebert-base`); ground‑truth sample ≥ 100 ensures reliable validation. |
| **III. Data Hygiene** | ✅ | Raw API responses saved under `data/raw/` with SHA‑256 checksums recorded in `state/`; all transformations output new files. |
| **IV. Single Source of Truth** | ✅ | Every figure/table derives from `data/processed/matched_pairs.csv` and `data/analysis/wilcoxon_results.json`. |
| **V. Versioning Discipline** | ✅ | Content hashes tracked in `state/projects/PROJ-247-evaluating-the-impact-of-code-generation.yaml`; any artifact change updates `updated_at`. |
| **VI. Longitudinal Data Integrity** | ✅ | Immutable snapshots of `git log` and GitHub Issues stored; missing issue links are logged and handled via censored‑data approach. |
| **VII. Classification Ground Truth** | ✅ | Random ≥ 100‑block subset manually verified; precision/recall ≥ 0.85 reported with confidence intervals; mis‑classification rate used for bias correction. |

## Project Structure

```
specs/001-evaluating-the-impact-of-code-generation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── dataset_schema.schema.yaml
    ├── ground_truth_schema.schema.yaml
    ├── metrics.schema.yaml
    └── metrics_schema.schema.yaml

code/
├── 01_data_curation.py          # FR‑001, FR‑003
├── 02_code_block_extraction.py # extracts functions/classes
├── 03_classification.py        # FR‑002, FR‑007
├── 04_matching.py               # FR‑008
├── 05_metrics_extraction.py    # FR‑004
├── 06_maintenance_events.py    # extracts MaintenanceEvent records
├── 07_analysis.py              # FR‑005, FR‑006
├── utils/
│   ├── git_utils.py
│   ├── github_utils.py
│   └── config.py               # seeds, constants, .env handling
├── requirements.txt
└── main.py                     # orchestrates the pipeline

data/
├── raw/
│   ├── repos.json               # raw GitHub API response
│   ├── repo_list.csv            # FR‑001 output (repo_id, stars, age, total_loc)
│   ├── repo_metadata.csv        # duplicate for clarity
│   └── clones/                  # shallow clones (depth=100)
├── processed/
│   ├── tagged_blocks.csv        # CodeBlock + classification
│   ├── matched_pairs.csv        # MatchedPair
│   ├── metrics_per_pair.csv     # per‑pair churn & latency (conforms to metrics.schema.yaml)
│   ├── maintenance_events.csv   # individual churn/bug‑fix events
│   └── ground_truth/
│       └── manual_labels.csv    # FR‑007 output
├── analysis/
│   ├── wilcoxon_results.json
│   └── figures/
│       ├── churn_boxplot.png
│       └── latency_boxplot.png

tests/
├── unit/
├── integration/
└── contract/
    └── test_schemas.py          # validates CSV/JSON against contracts

.logging.conf (provided)
.env.example (provided)
```

### Structure Decision
A single‑directory `code/` pipeline keeps data flow simple and satisfies the batch‑research nature of the project. No web service or UI is required.

## Mapping of Functional & Success Criteria to Plan Phases
| FR / SC | Phase / Script | Description |
|---------|----------------|-------------|
| FR‑001 | `01_data_curation.py` | GitHub search, shallow clone, repo metadata CSVs |
| FR‑002 | `03_classification.py` | ONNX CodeBERT inference, confidence filter |
| FR‑003 | `01_data_curation.py` (radon call) | Static complexity extraction |
| FR‑004 | `05_metrics_extraction.py` | Churn aggregation & bug‑fix latency (with robust linking) |
| FR‑005 | `07_analysis.py` | Wilcoxon signed‑rank, BH correction, rank‑biserial effect size, cluster‑robust aggregation |
| FR‑006 | `07_analysis.py` (matplotlib) | PNG box‑/density plots |
| FR‑007 | `03_classification.py` + `06_ground_truth.py` | Random ≥ 100‑block subset, precision/recall ≥ 0.85 with 95 % CI |
| FR‑008 | `04_matching.py` | Propensity‑score model with expanded covariates, 1:1 nearest‑neighbor within repo or pooled pool |
| SC‑001 | `07_analysis.py` (a‑priori & post‑hoc power) | Target power ≥ 0.80 for d = 0.5; report achieved power |
| SC‑002 | `07_analysis.py` (median churn test) | Wilcoxon on churn |
| SC‑003 | `07_analysis.py` (median latency test) | Wilcoxon on latency |
| SC‑004 | `07_analysis.py` (rank‑biserial) | Effect‑size reporting |
| SC‑005 | `07_analysis.py` (Benjamini‑Hochberg) | FDR control |
| SC‑006 | `03_classification.py` + manual check | Precision/recall ≥ 0.85 with 95 % CI |

## Complexity Tracking & Risk Mitigation
| Potential Issue | Mitigation |
|-----------------|------------|
| **API rate limits** | Exponential back‑off; store raw responses to avoid re‑fetching. |
| **Memory overflow** | Process repos sequentially; write intermediate CSVs; stream `git log` and radon output; limit total blocks to 2 000. |
| **Classifier mis‑classification** | Large ground‑truth sample (≥ 100) and sensitivity analysis that re‑weights results by observed error rate. |
| **Missing issue links** | Primary GitHub Issues events + PR cross‑references + fuzzy fallback; treat remaining missing latencies as right‑censored and report censoring proportion. |
| **Repo deletion / privacy change** | API call returns 404; the repo is logged and removed from all downstream files. |
| **Block refactoring / `git mv`** | `git log --follow` is used; if the path cannot be resolved, the block is excluded and noted. |
| **Confidence‑filter bias** | Record exclusion rates; apply inverse‑probability weighting; include in sensitivity analysis. |
| **Insufficient blocks per repo** | Pool blocks across repos when a repo cannot provide ≥ 5 LLM + 5 Human blocks. |
| **Compute budget** | Batch ONNX inference (~0.5 s per block) on a maximum of 2 000 blocks; streamed radon; early‑stop guard aborts if wall‑clock > 5.5 h; optional down‑sampling of low‑complexity blocks. |
| **Covariate omission** | Include developer experience, test‑coverage proportion, prior bug density, and optional domain tags in propensity model. |
| **Selection bias from confidence filter** | Inverse‑probability weighting and sensitivity analysis (already added). |
| **Short observation window** | Provide nine‑month sensitivity analysis; justify six‑month as primary based on prior literature. |
| **Non‑independence of pairs** | Cluster‑robust meta‑analysis across repositories. |
| **Effect‑size mismatch** | Use rank‑biserial correlation instead of Cohen’s d. |
| **Longitudinal data integrity** | Immutable snapshots of `git log` and Issues stored; gaps documented. |

---



