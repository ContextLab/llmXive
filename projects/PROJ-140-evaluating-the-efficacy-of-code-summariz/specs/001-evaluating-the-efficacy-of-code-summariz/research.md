# Research: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

## 1. Research Question & Hypotheses
**RQ:** Do code summaries (LLM‑generated or rule‑based) improve bug‑localization *accuracy* and *speed* compared with a baseline (no summary) for graduate‑level software‑engineering students?

| Hypothesis | Direction |
|------------|-----------|
| **H1 (Accuracy)** | Summaries increase the correct‑first‑line identification rate relative to baseline. |
| **H2 (Speed)** | Summaries reduce median time‑to‑decision relative to baseline. |
| **H3 (LLM vs Rule)** | LLM‑generated summaries outperform rule‑based summaries on both metrics. |

## 2. Dataset Strategy
The study relies exclusively on the **Defects4J v2.0** dataset, which supplies buggy Java methods together with ground‑truth buggy line numbers.

| Dataset | Verified URL(s) | Load Method | Notes |
|---------|----------------|-------------|-------|
| Defects4J (sampled Parquet) | `https://huggingface.co/datasets/chathuranga-jayanath/defects4j-context-5-len-10000-prompt-3/resolve/main/data/test-00000-of-00001.parquet` | `datasets.load_dataset("parquet", data_files=..., streaming=True)` | Stratified sample across Chart, Time, Math projects (a representative set of methods per project). |
| Defects4J (full Parquet) | `https://huggingface.co/datasets/chathuranga-jayanath/defects4j-context-5-len-all-prompt-3/resolve/main/data/test-00000-of-00001.parquet` | same as above | Used for optional larger‑scale analysis. |
| Adapted Defects4J (backup) | `https://huggingface.co/datasets/echodrift/adapt_defects4j/resolve/main/adapt_defects4j.parquet` | same as above | Fallback if primary URL unavailable. |

**Strategy**
1. Stream the dataset (`streaming=True`) to keep RAM < 7 GB.  
2. Verify each shard with SHA‑256 checksums stored in `data/checksums.txt`.  
3. Extract a stratified sample of **60 buggy methods** (20 per project) and persist to `data/processed/methods.csv`.  
4. All files conform to the JSON‑Schema contracts in `contracts/`.

## 3. Methodology

### 3.1 Study Design
- **Design**: Within‑subjects Latin‑square (12 participants × 10 tasks per condition = 360 observations).  
- **Conditions**:  
  1. **Baseline** – no summary.  
  2. **Rule** – srcML comment extractor.  
  3. **LLM** – CodeLlama‑7B (8‑bit) run on a Kaggle GPU (escape hatch).  
- **Counterbalancing**: Latin‑square guarantees each participant experiences each condition in each order exactly once.  
- **Real vs. CI**: CI runs in `--mode=sim` using synthetic logs; the real study replaces the log file with the anonymized human data.

### 3.2 Data Collection
- **Interaction Logging**: CSV columns `participant_id,task_id,condition,timestamp_ms,selected_line,ground_truth_line,fallback_status`.  
- **Latency Calibration**: At pipeline start, `code/utils/timing.py` runs a loopback test; the pipeline aborts if median precision > 100 ms (requirement from FR‑003).  
- **Fallback Logic**: If LLM generation exceeds 30 s, returns empty, or errors, the system logs a *fallback* and substitutes the rule‑based summary for that task. The `fallback_status` column records one of: `none`, `llm_timeout`, `llm_error`.  

### 3.3 Statistical Analysis

| Outcome | Model | Distribution / Link | Fixed Effect | Random Effect | Transformation |
|---------|-------|---------------------|--------------|---------------|----------------|
| **Accuracy** (binary) | **McNemar’s test** (paired) | Binomial, exact test | `condition` (baseline vs LLM, baseline vs Rule) | Paired within participants (implicit) | — |
| **Speed** (ms) | LME | Gaussian on `log(time)` | `condition` | `(1 | participant_id)` | `log` to reduce right‑skew. |

- **Fallback Handling**: Primary analysis **excludes** all trials where `fallback_status != none` to keep conditions pure. A sensitivity analysis will later include these trials with `fallback_status` as a covariate.  
- **Effect Sizes**: Odds Ratio (from McNemar) for accuracy; Cohen’s d (standardized beta) for speed.  
- **Confidence Intervals**: 95 % CI via **cluster bootstrap** (resample participants with replacement, `N=12` or `N=24` depending on power‑analysis outcome, 2000 resamples, seed = 42).  
- **Multiple Comparisons**: **Holm‑Bonferroni** correction across the four primary tests (baseline vs LLM accuracy, baseline vs LLM speed, baseline vs Rule accuracy, baseline vs Rule speed) with overall α = 0.05 (verified fact).  

### 3.4 A‑priori Power Analysis
We will run **Task T‑012** before any data collection:

1. **McNemar**: Using `statsmodels.stats.power.GofPower`, targeting an Odds Ratio = 2.0 (moderate effect) at α = 0.05, power = 0.80, yields **≈ 24 participants** (720 paired observations).  
2. **LME (speed)**: Using `statsmodels.stats.power.TTestIndPower` for a two‑sample comparison of log‑times with Cohen’s d = 0.6, α = 0.05, power = 0.80, also suggests **≈ 24 participants**.  

The script writes the recommended sample size to `data/power_analysis/report.txt`.  
- If the recommended N > 12, the pipeline automatically upgrades the simulated design to **24 participants** (maintaining the Latin‑square balance).  
- The final manuscript will report this a‑priori analysis, the chosen sample size, and acknowledge any residual power limitations.

### 3.5 Compute Feasibility & GPU Escape Hatch
- **CPU‑first**: All data handling, rule‑based summarization, latency test, simulation, and statistical analysis run on CPU within CI budget.  
- **GPU Escape Hatch**: Real LLM inference is performed **outside CI** via `scripts/run_llm_gpu.sh` on a Kaggle GPU (8‑bit quantization, `device="cuda"`). The script writes `summaries_llm.csv`; the main pipeline aborts with a clear message if the file is missing. No CPU approximation is attempted.

## 4. Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Use HuggingFace Parquet source | Direct programmatic download; open, checksum‑able, CI‑friendly. |
| Latin‑square design | Controls order effects; standard in SE HCI studies. |
| **McNemar’s test** for accuracy | Matches the specification (User Story 2) and is appropriate for paired binary outcomes across conditions. |
| Log‑transform LME for speed | Addresses right‑skewness of response times. |
| Cluster bootstrap | Preserves within‑subject correlation; necessary for correct CIs with N = 12/24. |
| **Holm‑Bonferroni** (α = 0.05) | More powerful than simple Bonferroni while controlling family‑wise error (verified fact). |
| **A‑priori power analysis** (T‑012) | Guarantees the study is not under‑powered for realistic moderate effects. |
| Simulated data for CI | Real human data cannot be generated in CI; simulation enables full‑pipeline verification. |
| GPU escape hatch for LLM | CodeLlama‑7B cannot meet the 30 s timeout on CPU; using a real GPU respects methodological integrity. |

## 5. Limitations & Risks
- **Sample Size**: Even with 24 participants, detection of very small effects may remain limited; we will report effect‑size estimates with CIs regardless of significance.  
- **LLM fallback** may dilute the LLM condition; primary analysis excludes fallback trials, and sensitivity analysis will assess impact.  
- **Participant dropout** (≤ 15 % assumed) will be handled by excluding incomplete participants from paired analyses.  
- **Bootstrap with 12/24 clusters** may produce unstable CIs; parametric CIs are provided as a supplement.  

---
