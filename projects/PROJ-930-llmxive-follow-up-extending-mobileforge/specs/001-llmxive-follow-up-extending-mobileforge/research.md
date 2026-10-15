# Research: MobileForge Logic Distillation

## 1. Problem Statement
Distill logical reasoning from MobileForge “failed‑then‑success” trajectories into a lightweight CPU‑only model that can generate corrective action sequences from UI states and textual hints. The hypothesis is that a small Encoder‑Decoder (T5‑small) can outperform a larger Decoder‑only baseline (TinyLlama) on unseen AndroidWorld tasks when evaluated with rigorous statistical methods.

## 2. Dataset Strategy

### 2.1 Verified Sources
| Role | Dataset | Access Method | Verified URL |
|------|---------|---------------|--------------|
| Training | ExtractionDataset (parquet) | `datasets.load_dataset('OSTShushack/ExtractionDataset', ...)` | https://huggingface.co/datasets/OSTShushack/ExtractionDataset/resolve/main/data/test-00000-of-00001.parquet |
| Evaluation | AndroidWorld benchmark (test split) | `datasets.load_dataset('google-deepmind/androidworld', split='test')` | *(verified via project’s dataset list)* |

All downloads are programmatic; no credentials required.

### 2.2 Extraction & Filtering (FR‑001)
1. Load the parquet file, verify SHA‑256 against `data/checksums.json`.  
2. Keep only rows where `trajectory_status == "failed_then_success"`.  
3. Validate `corrective_hint` contains no coordinate patterns (regex `\[\d+,\d+\]`).  
4. Add a control subset of “initial_success” trajectories (approximately a modest proportion of the data) to avoid over‑fitting to error‑recovery only.  
5. Output two Parquet files: `train_splits.parquet` and `test_splits.parquet`.

### 2.3 Evaluation Set Construction (FR‑003, FR‑007)
- Perform **a priori power analysis** (see Phase 1) to compute required sample size **N** using a **McNemar‑specific** calculation (expected discordant proportion).  
- Sample **N** tasks from AndroidWorld ensuring no overlap with training trajectories.  
- Store the list in `data/eval_tasks.json`.

## 3. Model Architecture & Training (FR‑002)

- **Distilled Model**: T5‑small (≈ 60 M parameters, Encoder‑Decoder).  
- **Baseline**: TinyLlama (Decoder‑only, pre‑downloaded from HuggingFace).  
- **Input Parity**: Both models receive the concatenated string `"UI_STATE: <ui_state> HINT: <corrective_hint>"`.  
- **CPU‑Only Enforcement**: Training script aborts if `torch.cuda.is_available()`; a watchdog terminates after 6 h (SC‑003).  
- **Training Hyper‑parameters** (pilot‑validated): batch = 8, lr = 3e‑4, epochs ≤ 3, gradient accumulation to stay within ~7 GB RAM, and a maximum of **20 k** training examples to respect the CPU budget. Early stopping with patience = 1 epoch further guarantees the 6‑hour wall‑clock limit.

## 4. Statistical Validation (FR‑004, FR‑005, SC‑004)

### 4.1 Power Analysis (FR‑007, SC‑006)
- Use a **McNemar‑specific** a‑priori power calculation (`utils/power_analysis.py`) with `power=0.8`, `effect_size=0.2` (Cohen’s h on discordant pairs), `alpha=0.05`, and a pilot estimate of discordant proportion from multiple baseline runs (or fallback 0.05).  
- Output `state/validated_n.json` containing `n_required` and the full parameter set.  
- The script aborts if it cannot write the file, preventing downstream execution.

### 4.2 Paired Evaluation (FR‑004)
- Both models are run on the **exact same N task instances** (identical seeds, UI state, hint).  
- **Deterministic Decoding**: `torch.manual_seed(RANDOM_SEED)`, greedy decoding (`num_beams=1`, `do_sample=False`, `temperature=0`).  

### 4.3 Functional Success Definition
- Generated action sequences are **executed** in the Android emulator (`utils/emulator.py`).  
- Binary outcome per task = **Success** if the emulator reports task completion; otherwise **Fail**. This avoids penalising semantically equivalent sequences that differ textually.

### 4.4 McNemar’s Test (FR‑005)
- Build 2×2 table:  
  - a: both succeed  
  - b: distilled succeeds, baseline fails  
  - c: distilled fails, baseline succeeds  
  - d: both fail  
- Apply `scipy.stats.mcnemar` (exact binomial when `b + c < 25`).  
- One‑tailed p‑value = `p/2` if `b > c`; significance declared at **p < 0.05** (SC‑004).

### 4.5 Contingency for Low Discordance
- After the pilot, if the observed discordant proportion is < 0.05, the power analysis script automatically recomputes `N` with a conservative estimate and logs the updated required sample size.

## 5. Sensitivity & Ablation (FR‑006, VII)

### 5.1 Inconsistency Tolerance Sweep
- Thresholds = {0, 1, 2, 3} (character‑level Levenshtein).  
- For each threshold, re‑evaluate functional success (emulator + Levenshtein ≤ threshold) for both models.  
- Report success‑rate variance across thresholds; no binary pass/fail decision (SC‑005).

### 5.2 Hint Ablation
- Replace every `Corrective_Hint` with the generic prompt `"retry"` for all evaluation tasks.  
- Re‑run deterministic evaluation; compare `hint_success_rate` vs. `retry_success_rate`.  
- Demonstrates that gains stem from the specific hint content (Constitution VII).

## 6. Compute Feasibility & Data Availability

- **CPU Feasibility**: Training on ≤ 20 k examples with the above hyper‑parameters completes in ≤ 5 h on the CI runner (validated in pilot).  
- **GPU Escape Hatch**: Not required; all steps run on CPU. If CUDA is unexpectedly detected, the script aborts (FR‑008).  
- **Data Access**: Both datasets are openly hosted on HuggingFace; CI can `wget`/`datasets.load_dataset` without manual steps.

## 7. Decision Rationale
| Decision | Why |
|----------|-----|
| T5‑small (Encoder‑Decoder) | Native sequence‑to‑sequence generation; fits parameter budget. |
| McNemar’s test | Binary paired outcomes; t‑test inappropriate. |
| McNemar‑specific power analysis | Guarantees ≥ 0.8 power for the paired design; avoids misuse of independent‑samples formulas. |
| CPU‑only training with timeout | Directly satisfies SC‑003 and the core hypothesis. |
| Functional emulator‑based success | Provides construct‑valid binary outcome aligned with task completion. |
| Deterministic decoding | Removes stochastic variance, meeting McNemar’s fixed‑outcome assumption. |
| Levenshtein tolerance sweep | Supplies a continuous sensitivity dimension while preserving binary evaluation. |
| Hint‑specific ablation | Required by Constitution VII to isolate the contribution of hints. |

---


