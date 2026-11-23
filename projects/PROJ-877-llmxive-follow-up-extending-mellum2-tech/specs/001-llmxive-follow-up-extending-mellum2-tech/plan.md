# Implementation Plan: llmXive follow‑up: extending "Mellum2 Technical Report"

**Branch**: `001-llmxive-complexity-loss` | **Date**: 2026-10-21 | **Spec**: `specs/001-llmxive-follow-up-extending-mellum2-tech/spec.md`  
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-mellum2-tech/spec.md`

## Summary
The project quantifies the relationship between static code‑complexity metrics (cyclomatic complexity, nesting depth, repetition ratio) and per‑token prediction loss (and entropy) from a frozen LLM. It then tests for non‑linear structural thresholds, validates findings via a rigorous permutation test, and confirms cross‑language consistency. All steps are fully reproducible, use only CPU resources (GPU escape hatch not required), and produce verifiable artifacts that satisfy every functional (FR‑001…FR‑011) and success‑criteria (SC‑001…SC‑005) requirement.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets`, `transformers`, `torch==2.3.0`, `tree-sitter`, `codeql`, `scikit-learn`, `statsmodels`, `pwlf`, `ruptures`, `pandas`, `pyarrow`, `matplotlib`, `seaborn`, `kenlm`  
- **Storage**: Local filesystem (`workspace/`); intermediate artifacts stored as Parquet (Snappy) or JSON under `data/`.  
- **Testing**: `pytest` + `jsonschema` contract validation.  
- **Target Platform**: GitHub Actions `ubuntu-latest` (Multiple CPU cores, ~7 GB RAM, no GPU).  
- **Performance Goals**: End‑to‑end wall‑clock ≤ 6 h; per‑chunk inference ≤ 60 s; peak RAM ≤ 7 GB.  
- **Constraints**: CPU‑only inference; deterministic random seeds; retry logic for parse/timeout/OOM failures; strict per‑language row count enforcement (see Phase 1 verification).  
- **Scale/Scope**: Target N = 500 repositories per language (Python & Java), subject to Phase 0 power analysis; if compute budget limits N, the exact value will be logged and used consistently.

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed random seeds in `code/config.py`; dataset fetched via `datasets.load_dataset` on every run; `requirements.txt` pins all versions. |
| II. Verified Accuracy | All external citations now point to **verified** sources: `bigcode/the-stack` (HuggingFace), `code_x_glue_ct_code_to_text` (HuggingFace), and TinyLlama‑1.1B (`https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v0.1`). |
| III. Data Hygiene | Raw downloads are checksummed (`sha256sum`) and recorded in `data/checksums.txt`. No in‑place edits; transformations write new Parquet files. |
| IV. Single Source of Truth | Every figure/table references a specific row in a Parquet artifact; the final JSON report contains pointers to those rows. |
| V. Versioning Discipline | Content hashes for each artifact are stored in `state/projects/PROJ-877-…yaml`; any change updates the hash and timestamp. |
| VI. Static Analysis Inference Independence | Static analysis (CodeQL/tree‑sitter) runs **before** any LLM forward pass; metrics are never fed back into the model. |
| VII. Non‑Linear Threshold Detection Rigor | Both piecewise regression (`pwlf`) and change‑point detection (`ruptures`) are mandatory; a formal Chow test plus permutation‑based p‑value is required, with ΔAIC > 2 as secondary evidence. |

## Project Structure
```text
specs/001-llmxive-follow-up-extending-mellum2-tech/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis.schema.yaml
    ├── code_chunk.schema.yaml
    ├── correlation_result.schema.yaml
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── threshold_result.schema.yaml
```

## Phase Execution Order (enforced by `code/main.py`)

| Phase | Description | FR/SC Covered |
|------|-------------|---------------|
| 0 | **Power & Feasibility (Phase 0)** – Compute Minimum Detectable Effect Size assuming a target correlation **r = 0.20**, α = 0.05 (two‑tailed), power = 0.80. Using the standard Pearson‑correlation power formula yields **≈ a few hundred repositories per language**. If the compute budget cannot accommodate this, the maximal feasible `N` is logged in `logs/power_analysis.log` and used, with an explicit limitation note. | SC‑005 |
| 1 | **Dataset Download & Language Verification (Phase 1)** – Stream the **verified** `bigcode/the-stack` dataset (HuggingFace) and filter files ending with `.py` (Python) or `.java` (Java). Perform a **stratified random sample** to obtain exactly **N** repositories per language. Write `raw_samples.parquet` (schema in `contracts/dataset.schema.yaml`). **Verification Step**: after sampling, run `pandas.DataFrame.groupby('language').size()` and write the counts to `logs/phase1_counts.log`. The pipeline aborts if any language deviates from the target `N`. Record SHA‑256 checksums of the raw parquet file in `data/checksums.txt`. | FR‑001 |
| 2 | **Static Analysis (Phase 2)** – Run **CodeQL** to extract cyclomatic complexity per function. Run **tree‑sitter** to compute maximum nesting depth and repetition ratio per chunk. **Validation Sub‑step**: randomly sample a subset of chunks and compare the extracted metrics against a curated benchmark from Software Heritage; log any systematic deviations in `logs/static_analysis_validation.log`. Errors (parse failures, unsupported syntax) are caught; the chunk is marked `status="parse_error"` and logged in `logs/static_analysis_errors.log`. Output: `code_chunks.parquet` (conforms to `contracts/code_chunk.schema.yaml`). | FR‑002, methodology-8e2b199c |
| 3 | **KenLM n‑gram Model (Phase 3)** – Build a 5‑gram Kneser‑Ney model on the *entire corpus* (excluding the sampled chunks) using `kenlm`. Store model file `ngram.model`; compute `log_ngram_prob` for each chunk during Phase 4. |
| 4 | **LLM Inference (Phase 4)** – Load `mistralai/Mistral-7B-v0.1` on CPU (`device="cpu"`). If RAM usage exceeds 6 GB, automatically switch to **TinyLlama v1.1B** (`https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v0.1`). For each chunk: run forward pass, capture per‑token loss and entropy, enforce a 60 s timeout, retry up to 3 times with exponential back‑off. Record `inference_time_ms` and final `status`. Output updates `code_chunks.parquet` with inference fields. |
| 5 | **Normalization & Confound Control (Phase 5)** – Compute **log‑probability** from the KenLM model (`log_ngram_prob`). Fit a linear regression model:  

  `per_token_loss ~ log_ngram_prob + comment_density + file_length + repo_popularity`  

  where `comment_density`, `file_length`, and `repo_popularity` are extracted from the source files and repository metadata. Use the **residuals** of this regression as the **normalized difficulty metric** (`normalized_loss`). This approach controls for token‑frequency bias and the additional confounds, aligning with standard statistical practice (see Gelman & Hill, 2007). |
| 6 | **Aggregation (Phase 6)** – Filter to `status=="success"` chunks. Compute repository‑level means → `repository_aggregates.parquet`. |
| 7 | **Correlation Analysis (Phase 7)** – Pearson & Spearman correlations between each complexity metric and `normalized_loss`, per language. Store results as `CorrelationResult` entries (one per metric, per language) in `correlation_results.parquet`. Apply permutation‑test p‑values (see Phase 8) and FDR correction (Phase 9). |
| 8 | **Threshold Detection (Phase 8)** – Fit **piecewise linear regression** (`pwlf`) and **change‑point detection** (`ruptures`). Perform a **likelihood‑ratio test** (χ², df = 1) comparing the piecewise model to a simple linear model; obtain a **permutation‑based p‑value** (Numerous repository‑level permutations). Additionally compute **ΔAIC**; a breakpoint is **reported** only if **p < 0.05** **and** **ΔAIC > 2**. As a formal test of a structural break, also conduct a **Chow test** at the candidate breakpoint; the breakpoint is retained only if the Chow test is significant (p < 0.05). Record breakpoint, slopes, model fit, AIC difference, and bootstrap stability (A sufficient number of bootstrap samples.). Perform a **sensitivity sweep** on `{0.01, 0.05, 0.1}` around the breakpoint; store results. |
| 9 | **Significance Testing (Phase 9)** – **Block permutation** at repository level (1 000 permutations) to generate empirical null distributions for correlations and for the LR‑test statistic. Compute raw p‑values, then apply **Benjamini‑Hochberg FDR** across all tests (FR‑008). Store in `correlation_results.parquet` and `threshold_results.parquet`. |
| 10 | **Cross‑Language Validation (Phase 10)** – Repeat Phases 7‑9 on the Java subset. Compare Pearson coefficients between Python and Java; report absolute difference. **Success Criterion**: consistency defined as difference ≤ 0.1 (SC‑004). |
| 11 | **Human‑Benchmark Validation (Phase 11)** – **Load** `code_x_glue_ct_code_to_text` (CodeXGLUE) **as a required step**. If the dataset cannot be loaded, the pipeline aborts with a clear error (no fallback). Compute correlation between our static‑analysis metrics and the human‑rated complexity scores; store as `benchmark_correlation.parquet`. |
| 12 | **Analysis Consolidation (Phase 12)** – Merge correlation and threshold results into `analysis_results.json`. **Validate** this file against `contracts/analysis.schema.yaml` using `jsonschema.validate`. |
| 13 | **Report Generation (Phase 13)** – Assemble `final_report.json` conforming to `contracts/output.schema.yaml`. Generate figures:  
  - `correlation_scatter.png` (scatter + regression line per language)  
  - `piecewise_fit.png` (piecewise regression with confidence bands)  
  - `bootstrap_stability.png` (distribution of threshold across bootstraps)  
All results are written under `data/results/` and figures under `data/figures/`. Artifacts are version‑hashed and listed in `data/checksums.txt`. |

**Mapping of Functional Requirements & Success Criteria**

| FR | Covered In Phase(s) | SC |
|----|---------------------|----|
| FR‑001 | 1 | – |
| FR‑002 | 2 | – |
| FR‑003 | 4 | SC‑003 |
| FR‑004 | 6,7 | SC‑001 |
| FR‑005 | 8 | SC‑002 |
| FR‑006 | 8 | SC‑002 |
| FR‑007 | 9 | SC‑003 |
| FR‑008 | 9 | SC‑003 |
| FR‑009 | 10 | SC‑004 |
| FR‑010 | 5,7 | – |
| FR‑011 | 11 | – |
| SC‑001 | 7,9 | – |
| SC‑002 | 8 | – |
| SC‑003 | 9 | – |
| SC‑004 | 10 | – |
| SC‑005 | 0 | – |

All FRs and SCs are explicitly addressed.

## Edge‑Case Handling (explicit in code)
- Parse failures → `status="parse_error"` and continue.  
- Constant‑metric datasets → detect zero variance, log warning, abort correlation step with clear message.  
- LLM inference failures → exponential back‑off retries, then `status="timeout"` or `status="oom"`; such chunks are excluded from aggregation.  
- Language‑specific bias → stratified sampling and separate analysis per language (Python, Java).  

---



