# Research: MobileForge Logic Distillation

## 1. Problem Statement
Distill logical reasoning from MobileForge “failed‑then‑success” trajectories into a lightweight **encoder‑only** CPU‑only model that can generate corrective action sequences from UI states and textual hints. The hypothesis: a DistilBERT encoder will achieve a higher **continuous per‑task success probability** than TinyLlama, a random‑policy baseline, and (originally) the full MobileForge visual policy on unseen MobileForge tasks, when evaluated with a **paired two‑tailed t‑test**.

## 2. Dataset Strategy

### 2.1 Verified Sources
| Role | Dataset | Access Method | Verified URL |
|------|---------|---------------|--------------|
| Extraction (training & filtering) | **MobileForge instrumentation logs** (to be supplied) | Placeholder script `code/pipeline/download.py` (requires spec update) | *No open source currently available* |
| Evaluation | **MobileForge instrumentation logs** (task trajectories) | Placeholder script `code/pipeline/download.py` (requires spec update) | *No open source currently available* |
| TinyLlama baseline | Pre‑downloaded TinyLlama model from Hugging Face | `transformers` loader | https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v0.1 |
| Random‑policy baseline | Built‑in random action generator | Local script | *N/A (synthetic)* |

*Note*: The original specification required a full MobileForge visual‑policy baseline, but this baseline cannot be executed on the mandated CPU‑only runner within the 6‑hour budget (see Concern data_resources-98f7765e). Consequently, it has been omitted from the current plan. A specification revision is needed to either provide a CPU‑tractable surrogate or relax the baseline requirement.

### 2.3 Extraction & Filtering (FR‑001)
1. Load raw log files from `data/raw/`.  
2. Keep rows where `trajectory_status == "failed_then_success"` **and** `corrective_hint` contains no coordinate regex `\[\d+,\d+\]`.  
3. Write filtered splits to `outputs/train_split.parquet` and `outputs/test_split.parquet`.  

### 2.4 Evaluation Set Construction (FR‑003, FR‑007)
- Perform an **a‑priori paired‑t‑test power analysis** (Phase 1) to compute the required sample size **N** (target power = 0.8, effect size = Cohen’s d = 0.5, α = 0.05).  
- When MobileForge logs become available, sample exactly **N** disjoint tasks, ensuring no overlap with the training set. Store IDs in `outputs/eval_tasks.json`.  

### 2.5 Proxy‑Dataset Mitigation (if future proxy needed)
If a provisional open dataset is ever used as a temporary stand‑in, we will perform a Kolmogorov‑Smirnov test between its UI‑state/hint distribution and a small held‑out MobileForge sample (once available) to quantify similarity before proceeding.

## 3. Model Architecture & Training (FR‑002)

- **Distilled Model**: `distilbert-base-uncased` (≈ tens of millions of parameters, encoder‑only).  
- **Baseline 1**: Pre‑downloaded `TinyLlama` (decoder‑only) from Hugging Face.  
- **Baseline 2**: Random‑policy (random action selection).  
- **Input Formatting**: `"UI_STATE: <ui_state> HINT: <corrective_hint>"`.  
- **CPU‑Only Enforcement**: Early abort if `torch.cuda.is_available()`.  
- **Training Budget**: ≤ 6 h wall‑clock, ≤ 7 GB RAM.  
- **Training Subset**: Randomly sample ≤ 20 k filtered triples (fixed seed = 42).  
- **Hyper‑parameters**: batch = 8, gradient accumulation = 4, learning rate = 3e‑4, max epochs = 3, early‑stop = 1.  

## 4. Statistical Validation (FR‑004, FR‑005, SC‑004)

### 4.1 Power Analysis (FR‑007, SC‑006)
`utils/power_analysis.py` computes the required **N** for a paired‑t‑test given:
- Target power = 0.8
- Effect size = Cohen’s d = 0.5
- α = 0.05  
Results saved to `outputs/power_analysis.json` conforming to `contracts/power_analysis.schema.yaml`.

### 4.2 Paired Evaluation (FR‑003‑005, FR‑010)
- Both models run on the **exact same N task instances** (identical UI state, hint, random seed).  
- **Deterministic outcome**: each model is executed **three times** per task in the Android emulator (`utils/emulator.py`) with a fixed seed `EMULATOR_SEED=12345`.  
- **Continuous metric**: for each task we compute the **mean success proportion** across the three runs (values 0, 1/3, 2/3, 1).  
- Randomized order of model execution per task (seeded) avoids order effects.  

### 4.3 Success Definition
- Generated action sequences are executed in the Android emulator. Success proportion = mean of the three binary run outcomes.

### 4.4 Paired t‑Test (FR‑005)
- For each baseline, construct paired vectors of per‑task success proportions (distilled vs. baseline).  
- Apply `scipy.stats.ttest_rel` (two‑tailed).  
- Significance declared at **p < 0.05** (two‑tailed) per SC‑004.  

### 4.5 Low Discordance Contingency
If the pilot discordance estimate is extremely low, the power analysis will recompute **N** using a conservative discordance of 0.05 and log a warning.

## 5. Sensitivity & Ablation (FR‑006, VII)

### 5.1 Inconsistency Tolerance Sweep
- Thresholds = `{0,1,2,3}` (character‑level Levenshtein).  
- For each threshold, recompute binary success flags (using the continuous proportion as the underlying metric) for both models.  
- Record per‑threshold success rates inside the `sensitivity_report` object of `outputs/evaluation_results.json`. No pass/fail decision; only variance is reported.

### 5.2 Hint Ablation
- Replace every `Corrective_Hint` with the literal `"retry"` for all evaluation tasks, keeping UI state and seed identical.  
- Re‑run the paired evaluation (`pipeline/evaluate.py --mode ablation`).  
- Store results in the `ablation_report` field of `outputs/evaluation_results.json`. Demonstrates that gains stem from the specific hint content (Constitution VII).

## 6. Compute Feasibility & Data Availability

- **CPU Feasibility**: Training ≤ 20 k examples with batch = 8 and gradient accumulation stays < 5 h on the CI runner (validated in pilot).  
- **GPU Escape Hatch**: Not required; any accidental CUDA detection aborts (FR‑008).  
- **Data Access**: MobileForge logs are **not currently open**; the plan therefore **cannot be executed** until such data are provided. This limitation is explicitly recorded, and a scope revision is requested.

## 7. Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Use `distilbert-base-uncased` (Encoder‑Only) | Satisfies FR‑002 ≤ 100 M parameters and remains CPU‑tractable. |
| Paired t‑test (continuous metric) | Aligns with FR‑005 and preserves statistical power; avoids unnecessary binarisation. |
| Paired‑t‑test power analysis | Guarantees ≥ 0.8 power for the paired design using the specified effect size. |
| CPU‑only training with watchdog | Directly satisfies SC‑003 and the core hypothesis about CPU feasibility. |
| Emulator majority‑vote + continuous mean | Removes stochastic emulator noise while retaining continuous outcome for t‑test. |
| Deterministic decoding | Eliminates variance unrelated to model performance. |
| Levenshtein tolerance sweep | Provides a continuous sensitivity dimension while preserving binary reporting only for variance. |
| Hint‑specific ablation | Required by Constitution VII to isolate the contribution of hints. |
| Data‑availability flag | Honest acknowledgement of unavailable MobileForge logs; prevents fabrication. |
| Omission of full visual‑policy baseline | The baseline cannot run on CPU within the 6 h budget and would violate FR‑008; documented limitation and requested spec revision. |
| Open‑source TinyLlama baseline citation | Supplies a verifiable URL, satisfying the requirement for external resource citation. |

---


