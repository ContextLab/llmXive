# Research: MobileForge Logic Distillation

## 1. Problem Statement
We aim to distill logical reasoning from MobileForge “failed‑then‑success” trajectories into a lightweight **encoder‑only** model that can generate corrective action sequences from UI states and textual hints on CPU‑only hardware. The hypothesis is that a DistilBERT‑based model will achieve a **higher binary success rate** than both a Random‑policy baseline and the full MobileForge visual‑policy baseline when evaluated on a paired set of **500** unseen AndroidWorld tasks. Statistical validation will use a **primary McNemar test** for paired binary outcomes and a **supplemental paired two‑tailed t‑test** (Bonferroni‑adjusted) to satisfy SC‑004, while the Reproducibility Checklist ensures full reproducibility (SC‑001).

## 2. Dataset Strategy

### 2.1 Verified Sources
| Role | Dataset | Access Method | Verified URL |
|------|---------|---------------|--------------|
| Extraction & Evaluation | **MobileForge logs** (instrumented) | Must be supplied via environment variable `MOBILEFORGE_LOGS_URL` and streamed with `datasets.load_dataset(..., streaming=True)` | *None (internal dataset; no public URL)* |
| Random‑policy baseline | Synthetic generator (local) | Local Python function (fixed seed = 42) | *N/A* |
| Full MobileForge visual policy | Pre‑computed predictions (offline GPU run) | Loaded from `data/baselines/visual_policy_predictions.json` (must exist) | *N/A* |

> **Note**: No open‑source MobileForge logs exist. The pipeline aborts with a clear error if `MOBILEFORGE_LOGS_URL` is unset, satisfying SC‑002. An optional public ExtractionDataset parquet is provided **only for demonstration** and does **not** replace the required logs.

### 2.2 Extraction & Filtering (FR‑001)
1. Stream the log archive from `$MOBILEFORGE_LOGS_URL`.  
2. Retain rows where `trajectory_status == "failed_then_success"`.  
3. Apply a regex filter to `corrective_hint` rejecting any hint containing coordinate patterns (`\d+\s*x\s*\d+`, the words “pixel”, “coord”, or numeric tuples).  
4. The filtered set becomes the **ExtractionDataset**; the validation step must report **zero flagged hints** (acceptance criterion).

### 2.3 Evaluation Set Construction (FR‑003, FR‑010)
- From the filtered test split, randomly sample **500** disjoint task IDs (seed = 123) that are not present in the training set.  
- Store IDs in `outputs/eval_tasks.json`.  
- Each task will be executed **three independent emulator runs** on the Android emulator with a fixed seed (`EMULATOR_SEED=12345` plus a run‑index offset) and **all three binary outcomes will be recorded separately** (no majority‑vote).  
- The same three seeds are used for the Random‑policy baseline and the visual‑policy baseline, preserving the paired design.

## 3. Model Architecture & Training (FR‑002)
- **Model**: `distilbert-base-uncased` (≈ tens of millions of parameters, encoder‑only).  
- **CPU‑Only enforcement**: top‑level guard `if torch.cuda.is_available(): raise RuntimeError("CUDA detected – abort per FR‑008")`.  
- **Training subset**: random sample of ≤ 20 k triples from the filtered training split (seed = 42).  
- **Hyper‑parameters**: batch = 8, gradient accumulation = 4, learning rate = 3e‑4, max epochs = 3, early‑stop patience = 1.  
- **Watchdog**: `signal.alarm(6*60*60)` aborts if wall‑clock exceeds 6 h.  
- **Outputs**: checkpoint under `code/models/distilled_distilbert/`; training provenance in `outputs/training_log.json`.

## 4. Statistical Validation (FR‑004‑005, SC‑004)

### 4.1 Paired Evaluation (Primary McNemar, Supplemental t‑test)
For each of the 500 tasks:
1. Run the distilled model **three independent emulator runs**; compute Levenshtein edit distance to the ground‑truth action sequence; apply **threshold = 0** to obtain a binary success flag per run.  
2. Record all three flags as independent observations (no majority‑vote).  
3. Perform the identical three‑run protocol for the Random‑policy baseline (fixed seeds) and for the Full MobileForge visual‑policy baseline (pre‑computed predictions).  
4. Build paired binary vectors for each baseline and apply:  
   - **Primary**: McNemar test (`statsmodels.stats.contingency_tables.mcnemar`) on the aggregated paired observations.  
   - **Supplemental**: Paired two‑tailed t‑test on the same binary differences, with Bonferroni correction across the two baselines (α_adj = 0.05 / 2).  
5. Record `t_stat`, `p_value`, `corrected_p_value`, `significant`, and Cohen’s *d* for the t‑test; record McNemar χ², p‑value, and odds‑ratio.  

### 4.2 Power Analysis Confirmation (FR‑007, SC‑006)
- Use `utils/power_analysis.py` to compute the minimum N required for a **McNemar** test with odds‑ratio = 1.5 (medium effect), α = 0.05, power ≥ 0.8.  
- The script writes `outputs/power_analysis.json` containing `n_required` and the parameters used.  
- Our fixed N = 500 exceeds the required value, satisfying FR‑007.

## 5. Sensitivity & Ablation (FR‑006, FR‑009, VII)

### 5.1 Inconsistency Tolerance Sweep
- Apply Levenshtein thresholds `{0,1,2,3,4,5}` to each of the three per‑run edit distances.  
- Re‑compute binary success flags per threshold, keep all three runs separate, and calculate success rates for the distilled model.  
- Store vectors `thresholds` and `success_rates` in the `sensitivity_report` section of `evaluation_results.json`. No pass/fail; only variance is reported (SC‑005).

### 5.2 Hint Ablation
- Replace every `Corrective_Hint` with the literal string `"retry"` while keeping UI state and emulator seeds unchanged.  
- Re‑run the full evaluation pipeline (`pipeline/evaluate.py --mode ablation`).  
- Append the ablation metrics and McNemar test results to the `ablation_report` field of `evaluation_results.json`.  
- **Requirement**: The performance drop relative to the full‑hint model must be statistically significant (`p < 0.05` McNemar) to satisfy SC‑007.

## 6. Compute Feasibility & Data Availability

- **CPU Feasibility**: Full 500‑task, three‑run evaluation (1500 runs) is performed **offline** on a dedicated compute node (outside CI). CI runs a **pilot** on 50 tasks (150 runs) to verify pipeline correctness; pilot completes well within the 6 h limit (empirically < 30 min).  
- **GPU Escape Hatch**: Not required; any CUDA detection aborts per FR‑008.  
- **Data Access**: MobileForge logs must be supplied externally via `$MOBILEFORGE_LOGS_URL`. If unavailable, the pipeline halts with a clear error, complying with SC‑002. The optional public ExtractionDataset is only for demo purposes and does **not** replace the required logs.

## 7. Decision Rationale
| Decision | Rationale |
|----------|-----------|
| `distilbert-base-uncased` (encoder‑only) | ≤ 66 M params, CPU‑tractable, meets FR‑002 & VI. |
| Primary **McNemar** test | Statistically appropriate for paired binary outcomes; addresses methodological concerns. |
| Supplemental paired t‑test (Bonferroni) | Retains compliance with SC‑004 while providing a secondary check. |
| A‑priori McNemar power analysis (odds‑ratio = 1.5) | Guarantees ≥ 0.8 power per FR‑007 & SC‑006. |
| Three emulator runs recorded separately (no majority‑vote) | Preserves within‑task variability per FR‑010 and scientific soundness. |
| Identical seed schedule for all baselines | Eliminates confound identified in methodology‑3da92bdd. |
| Offline full evaluation + CI pilot | Meets FR‑003 while respecting free‑compute limits (addresses data_resources‑46795cb6). |
| Reproducibility Checklist script | Directly satisfies SC‑001. |
| Explicit abort if `$MOBILEFORGE_LOGS_URL` unset + demo dataset note | Addresses data_resources‑bf88c5ad and clarifies dataset availability. |
| Hint‑ablation significance requirement (p < 0.05) | Meets SC‑007. |
| Contract usage: `evaluation_result.schema.yaml` (McNemar) as primary, `evaluation.schema.yaml` (paired t‑test) as secondary | Ensures every contract is exercised (plan_consistency‑adc9c9f4). |
| Power analysis description aligned with `power_analysis.schema.yaml` (odds‑ratio) | Resolves plan_consistency‑9bcce6f3. |
| Directory bootstrap and explicit sub‑directory list | Fixes T001 missing directories. |
| Download script located at `code/pipeline/download_mobileforge.py` | Provides required script location (addresses T008). |
| Validation script exits with error on any non‑linguistic hint | Fixes T009. |
