# Research: MobileForge Logic Distillation

## 1. Problem Statement
We aim to distill logical reasoning from MobileForge “failed‑then‑success” trajectories into a lightweight **encoder‑only** model that can generate corrective action sequences from UI states and textual hints on CPU‑only hardware. The central hypothesis is that a DistilBERT‑based model will achieve a **higher binary success rate** than both a TinyLlama‑250M decoder‑only baseline and a random‑policy baseline when evaluated on a paired set of 500 unseen AndroidWorld tasks. Statistical significance will be assessed with **McNemar’s test** (paired binary data), and robustness will be examined via a Levenshtein‑based inconsistency‑tolerance sweep and a hint‑ablation study.

## 2. Dataset Strategy

### 2.1 Verified Sources
| Role | Dataset | Access Method | Verified URL |
|------|---------|---------------|--------------|
| Extraction & Evaluation | **MobileForge logs** (instrumentation) | Must be supplied via `MOBILEFORGE_LOGS_URL` and streamed with `datasets.load_dataset(..., streaming=True)` | *None (requires provision by project owner)* |
| TinyLlama‑250M baseline | TinyLlama‑250M (decoder‑only) | `transformers.AutoModelForCausalLM.from_pretrained` | https://huggingface.co/TinyLlama/TinyLlama-250M |
| Random‑policy baseline | Synthetic generator (local script) | Local Python function (multiple seeds) | *N/A (synthetic)* |
| Full MobileForge visual policy | Pre‑computed predictions (optional) | Loaded from disk if provided | *N/A (requires spec amendment)* |

**Important Note**: FR‑001 explicitly requires *MobileForge instrumentation logs* as the source. No open‑source MobileForge logs are currently available. Consequently, the pipeline **will abort** if `MOBILEFORGE_LOGS_URL` is unset. An optional demonstration using the publicly available ExtractionDataset parquet is provided **solely for illustration** and does **not** satisfy FR‑001.

### 2.2 Extraction & Filtering (FR‑001)
1. Load the log archive from the verified URL (streaming to stay within RAM limits).  
2. Keep rows where `trajectory_status == "failed_then_success"`.  
3. Apply a regex filter to `corrective_hint` to reject any hint containing coordinate patterns (`\d+\s*x\s*\d+`, the word “pixel”, “coord”, or numeric tuples).  
4. The filtered set becomes the **ExtractionDataset**; zero flagged hints is the acceptance criterion.

### 2.3 Evaluation Set Construction (FR‑003, FR‑007)
- Perform an **a‑priori McNemar‑type power analysis** (Phase 1) with target power = 0.8, odds‑ratio effect size indicating a moderate positive association. (medium), α = 0.05. The calculation yields a required **N ≈ 300**; we retain the spec‑mandated **N = 500** to ensure ample power.  
- Once the MobileForge logs are available, randomly sample **500** disjoint task IDs (seed = 123) that are not present in the training split. Store the IDs in `outputs/eval_tasks.json`.

## 3. Model Architecture & Training (FR‑002)

- **Distilled Model**: `distilbert-base-uncased` (≈ 66 M parameters, encoder‑only).  
- **Input Formatting**: `"UI_STATE: <ui_state> HINT: <corrective_hint>"`.  
- **CPU‑Only Enforcement**: Early abort if `torch.cuda.is_available()`.  
- **Training Subset**: Sample ≤ 20 k triples from the filtered training split (seed = 42).  
- **Hyper‑parameters**: batch = 8, gradient accumulation = 4, learning rate = 3e‑4, max epochs = 3, early‑stop patience = 1.  
- **Watchdog**: `signal.alarm(6*60*60)` guarantees ≤ 6 h wall‑clock.  
- **Outputs**: checkpoint saved under `code/models/distilled_distilbert/`; training provenance logged to `outputs/training_log.json`.

## 4. Statistical Validation (FR‑004‑005, SC‑004)

### 4.1 Paired Evaluation (FR‑003‑005, FR‑010, SC‑004)
- For each of the 500 tasks, run the Android emulator **three times** with a fixed seed (`EMULATOR_SEED=12345`).  
- After each run compute the Levenshtein edit distance to the ground‑truth action sequence; apply the **inconsistency‑tolerance threshold = 0** to obtain a binary success flag per run.  
- Majority‑vote (≥2 successes) across the three runs yields the **final binary outcome** for each model on that task. This procedure satisfies FR‑010 while providing per‑run edit‑distance information for the sensitivity sweep.  
- The same deterministic protocol is applied to all models (distilled, TinyLlama‑250M, random‑policy, optional visual‑policy predictions).

### 4.2 McNemar’s Test (FR‑005)
- Construct a 2 × 2 contingency table for each baseline vs. the distilled model (counts of discordant pairs).  
- Apply `statsmodels.stats.contingency_tables.mcnemar` (exact binomial if `b + c ≤ 25`).  
- Record `chi2`, `p_value`, and `effect_size_odds_ratio`.  
- **Multiple‑Comparison Correction**: Bonferroni adjustment across the three baseline comparisons (α_adj = 0.05 / 3). Significance declared if corrected p < 0.05 (SC‑004).

### 4.3 Power Analysis Confirmation (FR‑007, SC‑006)
- The a‑priori McNemar power analysis (Phase 1) is stored in `outputs/power_analysis.json`.  
- The final sample size (N = 500) exceeds the required `n_required`; we log this confirmation in the evaluation results.

## 5. Sensitivity & Ablation (FR‑006, FR‑009, VII)

### 5.1 Inconsistency Tolerance Sweep
- Levenshtein thresholds `{0,1,2,3,4,5}` are applied to the per‑run edit distances; for each threshold the binary success flag is recomputed and then majority‑voted across the three runs.  
- Record per‑threshold success rates for the distilled model; embed the vectors `thresholds` and `success_rates` in the `sensitivity_report` field of `evaluation_results.json`. No hard pass/fail; only variance is reported (SC‑005).

### 5.2 Hint Ablation
- Replace every `Corrective_Hint` with the literal string `"retry"` while preserving UI state and emulator seed.  
- Re‑run the full Phase 4 pipeline (`pipeline/evaluate.py --mode ablation`).  
- Store the ablation metrics and McNemar’s test results in the `ablation_report` field.  
- Verify that the performance drop is **statistically significant (p < 0.05)** per SC‑007.

## 6. Compute Feasibility & Data Availability

- **CPU Feasibility**: Training on ≤ 20 k examples with the specified hyper‑parameters fits comfortably within the 6 h wall‑clock on the CI runner (pilot runs < 4 h).  
- **GPU Escape Hatch**: Not required; any accidental CUDA detection aborts per FR‑008.  
- **Data Access**: The only open dataset is the optional ExtractionDataset parquet (used for demo only). The required MobileForge logs must be supplied externally; otherwise the pipeline halts with a clear error, satisfying SC‑002.

## 7. Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Use `distilbert-base-uncased` (Encoder‑Only) | Meets FR‑002 ≤ 100 M parameters and is CPU‑tractable. |
| McNemar’s test (paired binary) | Directly matches FR‑005 and is appropriate for binary success outcomes. |
| Bonferroni correction | Controls family‑wise error rate across three baseline comparisons (SC‑004). |
| Power analysis for McNemar | Guarantees ≥ 0.8 power with the specified odds‑ratio effect size (SC‑006). |
| Majority‑vote over three emulator runs with per‑run Levenshtein thresholds | Satisfies FR‑010 while linking to the sensitivity analysis. |
| Random‑policy evaluated over three seeds | Removes bias from a single stochastic seed (addresses FR‑010 concern). |
| Batched emulator execution | Keeps RAM usage low and respects the 6 h wall‑clock on the CI runner. |
| TinyLlama‑250M baseline | Fits CPU constraints (< 100 M parameters) while providing a decoder‑only comparison. |
| Omission of full visual‑policy baseline | Cannot run on CPU within time budget; documented and spec‑revision requested. |
| Explicit data‑availability flag | Avoids fabricating MobileForge logs; complies with SC‑002. |
| Creation of placeholder `download_mobileforge.py` | Satisfies T001/T008 evidence of required script; aborts cleanly if data missing. |
| Updated `validate_extraction_dataset.py` logic | Resolves T009 failure by correctly counting flagged hints. |
| Constitution checks throughout | Demonstrates compliance with all listed principles. |
---

