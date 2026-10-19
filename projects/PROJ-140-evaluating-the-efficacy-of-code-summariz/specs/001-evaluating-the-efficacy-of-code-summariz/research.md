# Research: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

## 1. Research Question & Hypotheses
**RQ:** Do code summaries (LLM‑generated or rule‑based) improve bug‑localization *accuracy* and *speed* compared with a baseline (no summary) for graduate‑level software‑engineering students?

| Hypothesis | Direction |
|------------|-----------|
| **H1 (Accuracy)** | Summaries increase the correct‑first‑line identification rate relative to baseline. |
| **H2 (Speed)** | Summaries reduce median time‑to‑decision relative to baseline. |
| **H3 (LLM vs Rule)** | LLM‑generated summaries outperform rule‑based summaries on both metrics. |

## 2. Dataset Strategy
The study relies exclusively on the **Defects4J v2.0** dataset, which provides buggy Java methods together with ground‑truth buggy line numbers.

| Dataset | Verified URL(s) | Load Method | Notes |
|---------|----------------|-------------|-------|
| Defects4J (Parquet, sampled) | `https://huggingface.co/datasets/chathuranga-jayanath/defects4j-context-5-len-10000-prompt-3/resolve/main/data/test-00000-of-00001.parquet` | `datasets.load_dataset("parquet", data_files=..., streaming=True)` | Stratified sample across Chart, Time, Math projects. |
| Defects4J (Full) | `https://huggingface.co/datasets/chathuranga-jayanath/defects4j-context-5-len-all-prompt-3/resolve/main/data/test-00000-of-00001.parquet` | same as above | Used for optional larger‑scale analysis. |
| Adapted Defects4J | `https://huggingface.co/datasets/echodrift/adapt_defects4j/resolve/main/adapt_defects4j.parquet` | same as above | Backup source if primary URL is unavailable. |

**Strategy**
1. Load the dataset with `streaming=True` to keep RAM usage < 7 GB.  
2. Compute SHA‑256 checksums for each shard; store in `data/checksums.txt`.  
3. Perform a stratified extraction of **60 buggy methods** (20 per project) to balance difficulty.  
4. Persist the extracted methods to `data/processed/methods.csv` (schema validated by `contracts/dataset.schema.yaml`).  

All URLs are from the **Verified datasets** block; no other sources are introduced.

## 3. Methodology

### 3.1 Study Design
- **Design**: Within‑subjects Latin‑square (12 participants × 10 tasks per condition = 360 observations).  
- **Conditions**:  
  1. **Baseline** – no summary.  
  2. **Rule** – srcML comment extractor.  
  3. **LLM** – CodeLlama‑7B (8‑bit) on GPU (offline escape hatch).  
- **Counterbalancing**: Latin‑square ensures each participant sees each condition in each order exactly once.  
- **Real vs. CI**: CI runs in `--mode=sim` using synthetic interaction logs; the real study will replace the log file with the anonymized human data.

### 3.2 Data Collection
- **Interaction Logging**: CSV columns `participant_id,task_id,condition,timestamp_ms,selected_line,ground_truth_line`.  
- **Latency Calibration**: At pipeline start, `code/utils/timing.py` runs a loopback test; the pipeline aborts if precision > 100 ms.  
- **Fallback Logic**: If LLM generation exceeds 30 s, returns empty, or raises an error, the system logs a *fallback* and uses the rule‑based summary for that task (recorded in `generation_status`).  

### 3.3 Statistical Analysis

| Outcome | Model | Distribution / Link | Fixed Effect | Random Effect | Transformation (if needed) |
|---------|-------|---------------------|--------------|---------------|----------------------------|
| **Accuracy** (binary) | GLMM | Binomial, logit | `condition` (baseline vs. LLM / baseline vs. Rule) | `(1 | participant_id)` | — |
| **Speed** (ms) | LME | Gaussian (after `log`) | `condition` | `(1 | participant_id)` | `log(time)` to reduce right‑skew; if residuals remain non‑normal, fallback to Gamma GLMM. |

- **Effect Sizes**: Odds Ratio (derived from GLMM coefficient) for accuracy; standardized beta (fixed‑effect / residual SD) for speed.  
- **Confidence Intervals**: 95 % CI via **cluster bootstrap** (resample participants with replacement, `N=12`, seed = 42).  
- **Multiple Comparisons**: **Holm‑Bonferroni** correction across the four primary tests (baseline vs LLM accuracy, baseline vs LLM speed, baseline vs Rule accuracy, baseline vs Rule speed) with overall α = 0.05 (verified fact).  

### 3.4 Power & Limitations
- **Sample Size**: 12 participants (clusters). Post‑hoc power analysis (deferred) indicates sufficient power only for large effects (OR > 3, Cohen’s d > 1).  
- **Bootstrap Instability**: With few clusters, CI width may be large; we will report them with caution.  
- **LLM Fallback**: Frequency of fallbacks will be logged; a sensitivity analysis will re‑run the models after excluding fallback tasks.  

### 3.5 Compute Feasibility & GPU Escape Hatch
- **CPU‑first**: All data handling, rule‑based summarization, latency test, simulation, and statistical analysis run on CPU within the CI budget.  
- **GPU Escape Hatch**: Real LLM inference is performed **outside CI** via `scripts/run_llm_gpu.sh` on a Kaggle GPU (8‑bit quantization, `device="cuda"`). The script writes `summaries_llm.csv`; the main pipeline checks for its existence when `--mode=real`. If absent, it aborts with a clear message directing the user to run the GPU script. No CPU approximation is attempted.

## 4. Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Use HuggingFace Parquet source | Direct programmatic download; open, checksum‑able, CI‑friendly. |
| Latin‑square design | Controls order effects; standard in SE HCI studies. |
| GLMM over McNemar | Handles three conditions and repeated measures; McNemar is only for 2×2 paired tables. |
| Log‑transform LME | Addresses right‑skewness of response times; fallback to Gamma GLMM if normality fails. |
| Cluster bootstrap | Preserves within‑subject correlation; necessary for correct CI with small N. |
| Holm‑Bonferroni (α = 0.05) | More powerful than simple Bonferroni while still controlling family‑wise error; matches verified fact. |
| Simulated data for CI | Real human data cannot be generated in CI; simulation enables full‑pipeline verification. |
| GPU escape hatch for LLM | CodeLlama‑7B cannot meet the 30 s timeout on CPU; using a real GPU respects the methodological integrity. |

## 5. Limitations & Risks
- **Small N** limits detection of modest effects; we will report effect‑size estimates with wide CIs.  
- **LLM fallback frequency** may dilute the LLM condition; we will quantify and optionally exclude fallbacks in a sensitivity analysis.  
- **Participant dropout** (≤ 15 % assumed) will be handled by excluding incomplete participants from paired analyses.  
- **Bootstrap with 12 clusters** may produce unstable CIs; we will note this and provide parametric alternatives in the supplementary material.  

---
