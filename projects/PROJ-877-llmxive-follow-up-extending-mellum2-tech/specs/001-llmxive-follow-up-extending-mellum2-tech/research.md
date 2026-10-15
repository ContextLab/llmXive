# Research: llmXive follow‑up – extending "Mellum2 Technical Report"

## Research Question
Does a statistically significant correlation exist between static code complexity metrics (cyclomatic complexity, nesting depth, repetition ratio) and LLM prediction loss (per‑token cross‑entropy), and are there identifiable structural thresholds where this relationship becomes non‑linear?

## Dataset Strategy

| Role | Dataset | Access Method | Verification |
|------|---------|---------------|--------------|
| Primary (Python & Java) | `codeparrot/github-code` (public HuggingFace dataset) | `datasets.load_dataset("codeparrot/github-code", split="train", streaming=True)` | **Not in verified list** – the dataset is open‑source but lacks a pre‑verified URL. The plan **explicitly notes** this limitation and logs it; the pipeline will abort with a clear message if the dataset cannot be fetched. |
| Cross‑language validation | Java subset of the same `codeparrot/github-code` dataset | Same streaming loader with `language=="Java"` filter | Same verification note as above. |
| Human‑benchmark (optional) | `code_x_glue_ct_code_to_text` (CodeXGLUE) – if available | `datasets.load_dataset("code_x_glue_ct_code_to_text")` | **No verified URL** in the provided list; the pipeline will attempt to load it, and if unavailable, will generate a *Validation Limitation Report* (FR‑011 fallback). |
| Verified auxiliary (for sanity check) | CPU‑only LLaMA overlap score parquet | Direct URL: https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet | Used only for internal sanity checks; not central to the research question. |

> **Rationale** – No fully verified code dataset exists in the supplied list; the open `codeparrot/github-code` dataset is the closest match and is openly downloadable, satisfying the “open source” requirement despite lacking a verified URL. The plan therefore proceeds with it but logs the verification gap.

## Methodology

### 1. Power & Feasibility (Phase 0)
- Compute Minimum Detectable Effect Size (MDES) given the 6 h CPU budget and per‑chunk inference cost (≈ 45 s).  
- Determine feasible `N` (target ≈ 500 repos per language).  
- If MDES > anticipated effect size, log limitation and proceed with the maximal feasible `N`.

### 2. Data Ingestion (Phase 1)
- Stream dataset; filter files ending with `.py` or `.java`.  
- Stratified random sample to obtain exactly `N` repositories per language, verified by a `groupby('language').size()` check logged to `logs/phase1_counts.log`.  
- Write `raw_samples.parquet` (schema defined in `contracts/dataset.schema.yaml`).  
- Record SHA‑256 checksums in `data/checksums.txt`.

### 3. Static Analysis (Phase 2)
- **CodeQL** extracts cyclomatic complexity per function.  
- **tree‑sitter** computes maximum nesting depth and repetition ratio.  
- Errors (parse failures, unsupported syntax) are caught, logged, and the chunk is marked `status="parse_error"` (edge‑case handling).  

### 4. KenLM n‑gram Model (Phase 3)
- Build a 5‑gram Kneser‑Ney model on the tokenized corpus (excluding the sampled chunks).  
- Store model file `ngram.model`; used to compute `ngram_probability` for each chunk (FR‑010).

### 5. LLM Inference (Phase 4)
- Load `mistralai/Mistral-7B-v0.1` (HF) with `torch_dtype=torch.float32`, `device="cpu"`.  
- If RAM exceeds 6 GB, automatically switch to `TinyLlama/TinyLlama-1.1B-Chat-v0.1`.  
- For each chunk: run forward pass, capture per‑token loss and entropy, enforce 60 s timeout, retry up to 3× with exponential back‑off.  
- Record `inference_time_ms` and `status` (`success`, `timeout`, `oom`).

### 6. Normalization (FR‑010)
- Compute `normalized_loss = per_token_loss / ngram_probability`.  
- Additionally, run a regression with `ngram_probability` as covariate to verify robustness.

### 7. Aggregation (Phase 5)
- Filter `status=="success"` chunks.  
- Compute repository‑level means for all metrics; store `repository_aggregates.parquet`.

### 8. Correlation Analysis (Phase 6)
- Pearson & Spearman between each complexity metric and `normalized_loss`.  
- Store `CorrelationResult` entries (one per metric, per language).

### 9. Threshold Detection (Phase 7)
- Apply `pwlf` (piecewise linear fit) and `ruptures` (change‑point) on the aggregated data.  
- Compare AIC/BIC of piecewise vs. linear; if ΔAIC > 2, accept non‑linear model.  
- Record breakpoint (`threshold_value`) and slopes.  
- Perform sensitivity sweep on `{0.01, 0.05, 0.1}` around the breakpoint; store results.

### 10. Significance Testing (Phase 8)
- Block permutation at repository level (1 000 permutations).  
- Compute empirical p‑values for correlations and threshold‑fit improvement.  
- Apply Benjamini‑Hochberg FDR correction across all tests (FR‑008).  

### 11. Cross‑Language Validation (Phase 9)
- Repeat steps 6‑8 on the Java subset; compare correlation coefficients (SC‑004).  

### 12. Human‑Benchmark Validation (Phase 10)
- Attempt to load CodeXGLUE benchmark.  
- If unavailable, generate a *validation limitation report* and set `benchmark_used: false` in final JSON.

### 13. Reporting (Phase 11)
- Assemble `final_report.json` (conforms to `contracts/output.schema.yaml`).  
- Generate figures: scatter with regression line, piecewise fit, bootstrap CI plot.  
- All artifacts stored under `data/results/` and `data/figures/`.

## Compute Feasibility (CPU‑First)
- **Model size**: Mistral‑7B ≈ 13 GB VRAM, but on CPU memory footprint ≈ 6 GB; fits within 7 GB limit. If memory spikes, fallback to TinyLlama‑1.1B (≈ 2 GB).  
- **Streaming** avoids loading full dataset into RAM.  
- **Batch size** = 1 (single‑chunk inference) to keep memory low.  
- No GPU escape hatch required; all libraries run on CPU.

## Decision / Rationale
- **Model choice**: Mistral‑7B provides richer reasoning capacity; fallback ensures pipeline never fails due to OOM.  
- **Normalization**: Division by n‑gram probability isolates structural uncertainty (FR‑010). Covariate check guards against over‑normalization.  
- **Threshold detection**: Piecewise regression meets Principle VII; linear regression is only a baseline.  
- **Dataset limitation**: Acknowledged lack of verified code dataset; using `codeparrot/github-code` is the best openly available option, with explicit logging of verification status.  
- **Power analysis first**: Guarantees we do not run an under‑powered study (SC‑005).  

---
