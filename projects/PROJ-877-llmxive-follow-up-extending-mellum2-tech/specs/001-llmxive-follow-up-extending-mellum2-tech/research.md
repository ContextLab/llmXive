# Research: llmXive follow‑up – extending "Mellum2 Technical Report"

## Research Question
Is there a statistically significant correlation between static code‑complexity metrics (cyclomatic complexity, nesting depth, repetition ratio) and LLM prediction loss (per‑token cross‑entropy), and are there identifiable structural thresholds where this relationship becomes non‑linear? Does the finding hold across Python and Java code?

## Dataset Strategy

| Role | Dataset | Access Method | Verification |
|------|---------|---------------|--------------|
| Primary (Python & Java) | **bigcode/the‑stack** (HuggingFace) | **Streaming download via `datasets.load_dataset`**; abort if no verified source is supplied. | **Verified** – URL: https://huggingface.co/datasets/bigcode/the-stack |
| Human‑benchmark (required) | `code_x_glue_ct_code_to_text` (CodeXGLUE) | `datasets.load_dataset("code_x_glue_ct_code_to_text")` | **Verified** – URL: https://huggingface.co/datasets/code_x_glue_ct_code_to_text |
| Verified auxiliary (sanity) | CPU‑only overlap score parquet | Direct URL: https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet | Used only for internal sanity checks; not central to the research question. |

> **Rationale** – The original `codeparrot/github-code` dataset lacked a verified citation; we now use the verified open‑source `bigcode/the-stack` corpus, which contains both Python and Java files and is directly downloadable via the HuggingFace `datasets` library. The human‑benchmark dataset is **mandatory**; the pipeline aborts if it cannot be loaded, ensuring construct validity.

## Methodology

### 0. Power & Feasibility (Phase 0)
- **Effect size assumption**: anticipating a modest correlation of **r = 0.20** based on prior literature.  
- **Alpha**: 0.05 (two‑tailed).  
- **Desired power**: 0.80.  
- Using the standard Pearson‑correlation power formula, the required sample size per language is **≈ 500 repositories**. This figure drives Phase 1 sampling. If the compute budget (≤ 6 h CPU) cannot accommodate 500 per language, the maximal feasible `N` is logged and used, with an explicit limitation note in `logs/power_analysis.log`.

### 1. Data Ingestion & Language Verification (Phase 1)
- Stream the **verified code dataset** `bigcode/the-stack` and filter files ending with `.py` (Python) or `.java` (Java).  
- Perform a **stratified random sample** to obtain exactly **N** repositories per language.  
- Write `raw_samples.parquet` (schema in `contracts/dataset.schema.yaml`).  
- **Verification Step**: after sampling, run `pandas.DataFrame.groupby('language').size()` and write the counts to `logs/phase1_counts.log`. The pipeline aborts if any language deviates from the target `N`.  
- Record SHA‑256 checksums of the raw parquet file in `data/checksums.txt`.

### 2. Static Analysis (Phase 2)
- Run **CodeQL** to extract cyclomatic complexity per function.  
- Run **tree‑sitter** to compute maximum nesting depth and repetition ratio per chunk.  
- **Validation Sub‑step**: randomly sample a subset of chunks and compare the extracted metrics against a curated benchmark from Software Heritage; log any systematic deviations in `logs/static_analysis_validation.log`.  
- Errors (parse failures, unsupported syntax) are caught; the chunk is marked `status="parse_error"` and logged in `logs/static_analysis_errors.log`.  
- Output: `code_chunks.parquet` (conforms to `contracts/code_chunk.schema.yaml`).

### 3. KenLM n‑gram Model (Phase 3)
- Build a 5‑gram Kneser‑Ney model on the *entire corpus* (excluding the sampled chunks) using `kenlm`.  
- Store model file `ngram.model`; compute `log_ngram_prob` for each chunk during Phase 4.

### 4. LLM Inference (Phase 4)
- Load `mistralai/Mistral-7B-v0.1` on CPU (`device="cpu"`). If RAM usage exceeds 6 GB, automatically switch to **TinyLlama v1.1B** (`https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v0.1`, cited from arXiv 2401.02385).  
- For each chunk: run forward pass, capture per‑token loss and entropy, enforce a 60 s timeout, retry up to 3 times with exponential back‑off.  
- Record `inference_time_ms` and final `status`.  
- Output updates `code_chunks.parquet` with inference fields.

### 5. Normalization & Confound Control (FR‑010)
- Compute **log‑probability** from the KenLM model (`log_ngram_prob`).  
- Fit a linear regression model:  

  `per_token_loss ~ log_ngram_prob + comment_density + file_length + repo_popularity`  

  where `comment_density`, `file_length`, and `repo_popularity` are extracted from the source files and repository metadata.  
- Use the **residuals** of this regression as the **normalized difficulty metric** (`normalized_loss`). This approach controls for token‑frequency bias and the additional confounds, aligning with standard statistical practice (Gelman & Hill, 2007).

### 6. Aggregation (Phase 6)
- Filter to `status=="success"` chunks.  
- Compute repository‑level means → `repository_aggregates.parquet`.

### 7. Correlation Analysis (Phase 7)
- Pearson & Spearman correlations between each complexity metric and `normalized_loss`, per language.  
- Store results as `CorrelationResult` entries (one per metric, per language) in `correlation_results.parquet`.  
- Apply permutation‑test p‑values (see Phase 8) and FDR correction (Phase 9).  

### 8. Threshold Detection (Phase 8)
- Fit **piecewise linear regression** (`pwlf`) and **change‑point detection** (`ruptures`).  
- Perform a **likelihood‑ratio test** (χ², df = 1) comparing the piecewise model to a simple linear model; obtain a **permutation‑based p‑value** (1 000 repository‑level permutations).  
- Compute **ΔAIC**; a breakpoint is **reported** only if **p < 0.05** **and** **ΔAIC > 2**.  
- Additionally, conduct a **Chow test** at the candidate breakpoint; retain the breakpoint only if the Chow test is significant (p < 0.05).  
- Record breakpoint, slopes, model fit, AIC difference, and bootstrap stability (1 000 bootstrap samples). Perform a **sensitivity sweep** on `{0.01, 0.05, 0.1}` around the breakpoint; store results.

### 9. Significance Testing (Phase 9)
- **Block permutation** at repository level (1 000 permutations) to generate empirical null distributions for correlations and for the LR‑test statistic.  
- Compute raw p‑values, then apply **Benjamini‑Hochberg FDR** across all tests (FR‑008).  
- Store in `correlation_results.parquet` and `threshold_results.parquet`.  

### 10. Cross‑Language Validation (Phase 10)
- Repeat Phases 7‑9 on the Java subset.  
- Compare Pearson coefficients between Python and Java; report absolute difference.  
- **Success Criterion**: consistency defined as difference ≤ 0.1 (SC‑004).

### 11. Human‑Benchmark Validation (Phase 11)
- **Load** `code_x_glue_ct_code_to_text` (CodeXGLUE) **as a required step**. If the dataset cannot be loaded, the pipeline aborts with a clear error (no fallback).  
- Compute correlation between our static‑analysis metrics and the human‑rated complexity scores; store as `benchmark_correlation.parquet`.  

### 12. Analysis Consolidation (Phase 12)
- Merge correlation and threshold results into `analysis_results.json`.  
- **Validate** this file against `contracts/analysis.schema.yaml` using `jsonschema.validate`.  

### 13. Reporting (Phase 13)
- Assemble `final_report.json` conforming to `contracts/output.schema.yaml`.  
- Generate figures:  
  - `correlation_scatter.png` (scatter + regression line per language)  
  - `piecewise_fit.png` (piecewise regression with confidence bands)  
  - `bootstrap_stability.png` (distribution of threshold across bootstraps)  
- All results are written under `data/results/` and figures under `data/figures/`.  
- All artifacts are version‑hashed and listed in `data/checksums.txt`.

## Compute Feasibility (CPU‑First)
- **Model footprint**: Mistral‑large model requires a modest VRAM footprint (on the order of tens of gigabytes).; on CPU memory ≈ several GB. Fallback TinyLlama‑1.1B (~2 GB) ensures we never exceed the 7 GB RAM limit.  
- **Streaming** prevents loading the full code dataset into RAM.  
- **Batch size = 1** keeps peak memory low.  
- No GPU escape hatch is required; all libraries run on CPU.

## Decision / Rationale
- **Model choice**: Mistral‑7B provides richer reasoning; fallback to TinyLlama‑1.1B (`https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v0.1`, cited from arXiv 2401.02385) guarantees feasibility under the RAM budget.  
- **Normalization** via regression residuals controls for token‑frequency bias and the additional confounds, satisfying scientific rigor.  
- **Threshold detection** fulfills Principle VII; both PWLF and ruptures are lightweight CPU‑compatible, and the LR‑test plus Chow test provide formal statistical evidence.  
- **Dataset limitation**: The unverified `codeparrot/github-code` dataset has been replaced by the verified `bigcode/the-stack`.  
- **Power analysis first** prevents under‑powered studies (addresses methodology‑32f310e2).  

---



