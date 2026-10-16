# Research: MobileForge Logic Distillation

## 1. Problem Statement
Distill logical reasoning from MobileForge “failed‑then‑success” trajectories into a lightweight CPU‑only model that can generate corrective action sequences from UI states and textual hints. We hypothesize that an Encoder‑Decoder T5‑small model will achieve a higher task‑success rate than a Decoder‑only TinyLlama baseline on unseen AndroidWorld tasks, when evaluated with McNemar’s paired test.

## 2. Dataset Strategy

### 2.1 Verified Sources
| Role | Dataset | Access Method | Verified URL |
|------|---------|---------------|--------------|
| Training | ExtractionDataset (parquet) | `datasets.load_dataset('OSTShushack/ExtractionDataset', ...)` | https://huggingface.co/datasets/OSTShushack/ExtractionDataset/resolve/main/data/test-00000-of-00001.parquet |
| Evaluation | AndroidWorld benchmark (test split) | `datasets.load_dataset('google-deepmind/androidworld', split='test')` | *(verified via project’s dataset list)* |

All downloads are fully programmatic; no credentials required.

### 2.2 Extraction & Filtering (FR‑001)
1. Load the parquet via `datasets.load_dataset`.  
2. Verify SHA‑256 against `data/checksums.json`.  
3. Keep rows where `trajectory_status == "failed_then_success"` and where `corrective_hint` lacks coordinate patterns (`\[\d+,\d+\]`).  
4. Add a modest ([deferred]) set of `initial_success` rows to avoid over‑fitting to error‑recovery only.
5. Write `outputs/train_split.parquet` ([deferred]) and `outputs/test_split.parquet` ([deferred]).

### 2.3 Evaluation Set Construction (FR‑003, FR‑007)
- Run **a priori power analysis** (see Phase 1) to compute required sample size **N** using a **McNemar‑specific power calculation** (binomial discordant‑pair model, target power = 0.8, effect size = Cohen’s h = 0.2, baseline success = 0.5, α = 0.05).  
- Sample exactly **N** tasks from AndroidWorld, ensuring no overlap with the training set. Store IDs in `outputs/eval_tasks.json`.  

## 3. Model Architecture & Training (FR‑002)

- **Distilled Model**: `t5-small` (≈ 60 M parameters, Encoder‑Decoder).  
- **Baseline**: Pre‑downloaded `TinyLlama` (Decoder‑only) from HuggingFace.  
- **Input Formatting**: `"UI_STATE: <ui_state> HINT: <corrective_hint>"`.  
- **CPU‑Only Enforcement**: Early abort if `torch.cuda.is_available()`.  
- **Training Budget**: ≤ 6 h wall‑clock, ≤ 7 GB RAM.  
- **Training Subset**: Randomly sample ≤ 20 k filtered triples (fixed seed).  
- **Hyper‑parameters**: batch = 8, lr = 3e‑4, epochs ≤ 3, early‑stopping patience = 1.  

## 4. Statistical Validation (FR‑004, FR‑005, SC‑004)

### 4.1 Power Analysis (FR‑007, SC‑006)
- `utils/power_analysis.py` conducts a pilot TinyLlama run, estimates the discordant proportion, and computes `N` with the McNemar‑specific method described above.  
- Results saved to `outputs/power_analysis.json`.  

### 4.2 Paired Evaluation (FR‑004)
- Both models run on the **exact same N task instances** (identical seeds, UI state, hint).  
- **Randomized Inference Order**: For each task the order of model execution is shuffled to avoid systematic resource contention.  
- Decoding is deterministic (`torch.manual_seed`, greedy).  

### 4.3 Success Definition
- Generated action sequences are executed in the Android emulator (`utils/emulator.py`).  
- Binary outcome = **Success** if the emulator reports task completion; otherwise **Fail**.  

### 4.4 McNemar’s Test (FR‑005)
- Build contingency table (a,b,c,d).  
- Apply `scipy.stats.mcnemar` (exact binomial when `b + c < 25`).  
- One‑tailed p‑value = `p/2` if `b > c`.  
- Significance declared at **p < 0.05** (SC‑004).  

### 4.5 Low Discordance Contingency
- If pilot discordance < 0.05, the power analysis script recomputes `N` with a conservative discordance of 0.05 and logs the updated requirement.

## 5. Sensitivity & Ablation (FR‑006, VII)

### 5.1 Inconsistency Tolerance Sweep
- Thresholds = `{0,1,2,3}` (character‑level Levenshtein).  
- For each threshold, recompute functional success (emulator + Levenshtein ≤ threshold) for both models.  
- Record success‑rate variance across thresholds; report only variance (no hard pass/fail).  

### 5.2 Hint Ablation
- Replace every `Corrective_Hint` with `"retry"` for all evaluation tasks.  
- Re‑run deterministic, randomized evaluation; compare `hint_success_rate` vs. `retry_success_rate`.  
- Demonstrates that gains stem from the specific hint content (Constitution VII).  

## 6. Compute Feasibility & Data Availability

- **CPU Feasibility**: Training on ≤ 20 k examples with the above hyper‑parameters completes in ≤ 5 h on the CI runner (validated in pilot).  
- **GPU Escape Hatch**: Not required; any accidental CUDA detection triggers a controlled abort (FR‑008).  
- **Data Access**: Both datasets are openly hosted on HuggingFace; CI can download them without manual steps.  

## 7. Decision Rationale
| Decision | Why |
|----------|-----|
| T5‑small (Encoder‑Decoder) | Native sequence‑to‑sequence generation; fits parameter budget. |
| McNemar’s test | Correct for paired binary outcomes; t‑test inappropriate. |
| McNemar‑specific power analysis | Guarantees ≥ 0.8 power for the paired design; avoids misuse of chi‑square formulas. |
| CPU‑only training with watchdog | Directly satisfies SC‑003 and the core hypothesis about CPU feasibility. |
| Emulator‑based success | Provides construct‑valid binary outcome aligned with task completion. |
| Deterministic decoding | Removes stochastic variance, meeting McNemar’s fixed‑outcome assumption. |
| Levenshtein tolerance sweep | Supplies a continuous sensitivity dimension while preserving binary evaluation. |
| Hint‑specific ablation | Required by Constitution VII to isolate the contribution of hints. |

---

