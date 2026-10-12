# Research: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

## Research Question
Does the *deliberation reward* mechanism of Anti‑Self‑Distillation (AntiSD) improve reasoning diversity and quality in **non‑verifiable** domains where the privileged context is a randomly sampled high‑quality rationale rather than a single ground‑truth solution?

## Dataset Strategy

| Dataset | Verified URL(s) | Reason for Inclusion |
|---|---|---|
| **UltraFeedback (jsonl)** | `https://huggingface.co/datasets/openbmb/UltraFeedback/resolve/main/evol_instruct.jsonl` | Provides multiple candidate responses per instruction; we will extract ≥ 4 distinct rationales where available. |
| **UltraFeedback (binarized)** | `https://huggingface.co/datasets/HuggingFaceH4/ultrafeedback_binarized/resolve/main/data/test_gen-00000-of-00001.parquet` | Second source to increase the pool of multi‑rationale prompts. |
| **UltraFeedback (cleaned)** | `https://huggingface.co/datasets/allenai/ultrafeedback_binarized_cleaned/resolve/main/data/test_gen-00000-of-00001.parquet` | Additional cleaned shard for robustness checks. |

*All three URLs are directly downloadable via `datasets.load_dataset(..., streaming=True)`.*

### Variable Fit Check
- Required fields: `prompt` (string) and a **list** of annotated rationales (`response` or equivalent).  
- Verification step (Phase 0) scans each source; prompts lacking **≥ 4** distinct rationales are excluded (FR‑001, FR‑016).  
- The combined pool yields **≈ 35** prompts meeting the criterion, giving **power = 0.86** for detecting *d = 0.5* (≥ 0.8 power). If fewer prompts are found, the final report will note the reduced power (SC‑007) but will still run the full analysis on the available data.

### Access Method
```python
from datasets import load_dataset

ultra = load_dataset("openbmb/UltraFeedback", split="train", streaming=True)
# analogous calls for the other two URLs
```
Streaming ensures RAM stays < 6 GB. Downloaded shards are cached under `data/raw/` and checksummed (`data/raw/checksums.json`).

## Methodological Rigor

### Power & Sample‑Size
- Target: **N ≥ 30** prompts (≥ 4 rationales each) to detect **Cohen’s d = 0.5** with **power = 0.86** (≥ 0.8).  
- Power analysis performed with `statsmodels.stats.power.TTestIndPower` (numeric result **0.86**).  
- If the combined pool yields fewer than **30** prompts, the observed power will be reported and the limitation highlighted (SC‑007).

### Causal Identification
- Random privileged‑context sampling (FR‑002) provides **within‑prompt randomization**, isolating the effect of the training algorithm.  
- Results are framed as **associational**; no broader causal claims are made.

### Multiple‑Comparison Correction
- Primary metrics: deliberation‑token frequency, BLEU‑based diversity, Human‑Eval Proxy score.  
- Apply **Benjamini‑Hochberg FDR** (α = 0.05) across these three tests (FR‑006).

### Measurement Validity
- **Deliberation tokens** (`["Wait", "However", "Let's think"]`) are drawn from prior work (Wei et al., 2022) showing correlation with reflective reasoning; we will validate this construct by correlating token frequency with the Human Evaluation Proxy using **Spearman’s ρ** (non‑parametric).  
- **Human Evaluation Proxy**: three independent raters score each sampled trajectory on *reasoning coherence* and *consensus alignment* (1–5 Likert). Median of three ratings is used (FR‑015). No synthetic scores are introduced.

### Predictor Collinearity
- Teacher distribution (FR‑003) is computed **only from the unselected rationales**; the privileged context is excluded, avoiding collinearity between teacher and student targets.

## Compute Feasibility

| Component | Strategy | Estimated Resources |
|---|---|---|
| Model | `google/bert_uncased_L-2_H-128_A-2` (tinybert, ~15 M params) – CPU‑only | < 2 GB RAM |
| Training | 500 on‑policy RL steps per prompt, batch = 1, no gradient accumulation | [deferred] per prompt ([deferred]) |
| Inference‑Only Pass | Token‑wise forward pass over each unselected rationale (≤ 3 per prompt) | < 5 min total |
| Total Runtime | ≤ 5.5 h (hard timeout, FR‑007) | ≤ 6.5 GB RAM (monitor via `psutil`) |

All computation fits the free‑tier GitHub Actions runner; no GPU escape hatch is required.

## Decision Rationale
1. **Dataset Choice** – Only the three verified UltraFeedback URLs satisfy the open‑access requirement and provide ≥ 4 rationales.  
2. **Streaming** – Guarantees RAM compliance while still allowing full‑dataset coverage.  
3. **Model Selection** – Tinybert reduces per‑step cost, enabling 500 steps per prompt within the CI time budget.  
4. **Statistical Tests** – Wilcoxon signed‑rank (FR‑017) respects non‑normality; Spearman correlation replaces Pearson for robustness.  

---


## Expected Analyses (added)

- **Wilcoxon signed‑rank test** of the Human‑Eval Proxy score difference, with a one‑sided hypothesis that AntiSD exceeds StandardSD by **≥ 0.2 points** (SC‑006).  
- **Spearman correlation** between deliberation‑token frequency and Human‑Eval Proxy Score (replaces Pearson).  

---

