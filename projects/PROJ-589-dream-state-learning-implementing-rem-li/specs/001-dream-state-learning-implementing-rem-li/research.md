# Research: Dream-State Learning: Implementing REM-like Consolidation in Language Models

## Executive Summary
We investigate whether an oscillatory **wake/dream** training schedule—mirroring REM‑like consolidation—improves few‑shot generalization of a small transformer (DistilBERT‑base‑uncased) relative to continuous supervised fine‑tuning. Consolidation is operationalized as the model’s ability to reconstruct masked, self‑generated pseudo‑samples (a denoising auto‑encoder objective). The study is a **pilot**: 3 random seeds for the primary analysis (with a fixed temperature = 1.0) and a limited temperature sweep as a secondary ablation, each run both experimental (wake/dream) and baseline (continuous) regimes. All experiments run on a 2‑CPU, ≤7 GB RAM GitHub Actions runner.

## Theoretical Background & Logical Depth
- **Digital Consolidation**: In biology, REM sleep stabilizes synaptic changes via replay. Here, the model **replays its own predictions**, then learns to reconstruct the original inputs, creating a closed loop of “prediction → noisy reconstruction → correction.” This loop adds *logical depth*: the model must internalize a representation that survives self‑generated perturbations, akin to synaptic stabilization.
- **Hypothesis**: The wake/dream loop yields a lower reconstruction error after each cycle, which correlates with improved downstream few‑shot accuracy on an unseen task.

## Dataset Strategy
Verified GLUE datasets are accessed via the HuggingFace `datasets` library (programmatic loading; no direct verified URLs for the specific splits).

| Role | GLUE Subset | Loader | Verified URL |
|------|-------------|--------|--------------|
| Wake‑phase training | **MNLI** (train split) | `datasets.load_dataset('glue', 'mnli', split='train', streaming=True)` | *No verified URL; loaded via HuggingFace library* |
| Few‑shot evaluation | **QNLI** (validation split) | `datasets.load_dataset('glue', 'qnli', split='validation', streaming=True)` | *No verified URL; loaded via HuggingFace library* |

*Streaming* is employed when the full split exceeds RAM; otherwise a deterministic random sample (≤2000 examples) is cached under `data/raw/`. No gated datasets are required.

## Methodology

### Experimental Design
| Variable | Values |
|----------|--------|
| **Training Regime** | `wake_dream` (4 wake : 1 dream) vs. `baseline` (continuous) |
| **Warm‑up Steps** | 20 wake‑only steps before first dream |
| **Dream Temperature** | Fixed **1.0** for primary analysis; optional sweep `[0.5, 1.0, 1.5, 2.0]` as secondary ablation |
| **Random Seeds** | 0, 1, 2 (primary); 3, 4 optional if resources allow |
| **Total Gradient Steps** | 100 (fixed across all runs) |
| **Batch Size** | 4 (CPU‑friendly) |
| **Memory Cap** | 6.3 GB RSS (hard abort) |
| **Wall‑clock Cap** | 5 h per full experiment |

### Training Loop (high‑level pseudocode)
```
for step in range(total_steps):
    if step < warmup_steps:
        run_wake_step()
    elif (step - warmup_steps) % (wake_steps + dream_steps) < wake_steps:
        run_wake_step()
    else:
        pseudo = generate_pseudo_sample(temperature=current_temp)
        if entropy(pseudo) < 0.5:
            retry up to 3 times; if still low → skip dream step (log)
        if perplexity(pseudo) > 50:
            skip dream step (log)
        run_dream_step(pseudo)   # masked reconstruction + distillation loss
        # Record reconstruction error for later correlation analysis
```
All loss values are logged; dream‑step skips are recorded in `dream_event.schema.yaml`. When a dream step is skipped, a dummy wake step is inserted to keep **real‑token exposure** identical between regimes.

### Baseline
Identical total steps and real‑token count; dream steps are replaced by additional wake steps. If the experimental run skips a dream step, the baseline adds a corresponding wake step to preserve token parity.

### Evaluation
- After training, load the final checkpoint, evaluate on **QNLI** (few‑shot: 5 examples per class) and compute **accuracy**.
- Repeat for each seed and regime.
- Perform a **paired two‑tailed t‑test** (`scipy.stats.ttest_rel`) across the 3 seed pairs.
- Compute **Cohen’s d** for effect size.
- Additionally, compute the **Pearson correlation** between average reconstruction error (logged during training) and final accuracy to validate the consolidation construct.

### Statistical Rigor
- **Multiple Comparisons**: Only one evaluation set is used for the primary hypothesis; no correction needed. The temperature sweep is a secondary analysis and reported separately.
- **Power**: With `n = 3` seed pairs, power to detect `d = 0.8` is ≈ 0.45. The study is explicitly framed as a **pilot**; we report effect size, confidence interval, and note the limited power rather than asserting definitive significance.
- **Assumptions**: Observational (no randomization beyond seed); claims limited to *associational* improvements.

## Edge‑Case Handling
1. **Low‑Entropy Collapse** – average token entropy < 0.5 bits ⇒ retry up to 3 times; if still low, discard batch and log `discarded: true`.
2. **High Perplexity** – perplexity > 50 ⇒ skip dream step, log reason.
3. **Insufficient Evaluation Samples** – if the few‑shot QNLI subset contains < 5 examples for a seed, the paired t‑test is omitted; the result file will contain `"note": "insufficient power"` per `statistical_report_schema.yaml`.
4. **Memory/Time Overrun** – `memory_monitor.py` aborts with status `oom_abort`; `train.py` tracks wall‑clock and aborts with `timeout` status if > 5 h. Aborted runs are flagged and automatically re‑run with reduced step count.

## Decision Rationale
| Decision | Reason |
|----------|--------|
| **DistilBERT‑base‑uncased** | ≤ 100 M params, fits CPU memory budget, matches FR‑001 requirement for a “small” model. |
| **4:1 Wake/Dream Ratio** | Implements the *theta‑like* oscillation mandated by Constitution Principle VI. |
| **20‑step Warm‑up** | Prevents early garbage generation (Edge Case). |
| **Fixed Temperature = 1.0 for Primary Analysis** | Avoids confounding temperature with the core hypothesis (Methodology‑320f1153). |
| **Temperature Sweep as Secondary** | Satisfies FR‑006 while keeping primary analysis clean. |
| **3 Seeds (Pilot)** | Keeps total compute within the 5 h wall‑clock budget (Methodology‑d17abfbb). |
| **Token‑balance Handling** | Guarantees identical real‑token exposure despite dream‑step skips (Methodology‑fc66a14b). |
| **Abort Handling & Re‑run** | Prevents biased comparisons if one regime aborts early (Methodology‑fe6e93e4). |
| **Reconstruction Error Correlation** | Provides construct validity for “consolidation” (Methodology‑c0a928d2). |
| **Pilot framing** | Honest acknowledgement of limited power (Methodology‑83598387). |

---

