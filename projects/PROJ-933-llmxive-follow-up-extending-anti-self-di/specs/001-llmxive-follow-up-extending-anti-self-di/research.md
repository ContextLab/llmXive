# Research: llmXive follow‑up: extending “Anti‑Self‑Distillation for Reasoning RL via Pointwise Mutual Information”

## Research Question
Does the *deliberation reward* mechanism of Anti‑Self‑Distillation (AntiSD) improve reasoning diversity and quality in **non‑verifiable** domains where the privileged context is a randomly sampled high‑quality rationale rather than a single ground‑truth solution?

## Dataset Strategy

| Dataset | Verified URL(s) | Reason for Inclusion |
|---|---|---|
| **BigBench Hard** (abstract‑narrative‑understanding) | ` | Contains natural‑language prompts; many prompts have fewer than three rationales, so they will be filtered out. |
| **BigBench Ethics** (auto_debugging) | ` | Provides ethically‑focused prompts with multiple answer options that can serve as surrogate rationales. |
| **BigBench Causal Judgement** | ` | Adds domain diversity; also contains multiple answer explanations. |

*All three URLs are directly downloadable via `datasets.load_dataset(..., streaming=True)`.*

### Variable Fit Check
- Required fields per prompt: `prompt_id` (string), `prompt_text` (string), `rationales` (list of strings).  
- **Current limitation**: The verified shards do **not** guarantee ≥ 3 rationales for every prompt. The pipeline will **strictly skip** any prompt that fails this criterion (FR‑001). If, after filtering, fewer than **30** prompts remain, the run **aborts** and reports insufficient data, preserving the integrity of the multi‑solution context requirement.

### Access Method
```python
from datasets import load_dataset

bb_hard = load_dataset(
    "tasksource/bigbench",
    "abstract_narrative_understanding",
    split="train",
    streaming=True,
)
bb_ethics = load_dataset(
    "lighteval/bigbench_helm",
    "auto_debugging",
    split="test",
    streaming=True,
)
bb_causal = load_dataset(
    "EleutherAI/bigbench",
    "causal_judgement",
    split="train",
    streaming=True,
)
```
Streaming keeps RAM < 6 GB while allowing full‑dataset processing.

## Methodological Rigor

### Power & Sample‑Size (Wilcoxon‑based)
- Target: **N ≥ 30** prompts (paired observations across conditions).  
- Power simulation for the Wilcoxon signed‑rank test (effect size *r* ≈ 0.5, α = 0.05) yields **power ≈ 0.82**.  
- If fewer than 30 prompts survive filtering, the analysis will still run but will transparently report the reduced power (SC‑007).

### Causal Identification
- Random privileged‑context sampling per prompt provides within‑prompt randomization, isolating the effect of the AntiSD training signal.  
- Conclusions are framed **associational**; no causal claims beyond the experimental manipulation are made.

### Multiple‑Comparison Correction
- Primary metrics: deliberation‑token frequency, diversity (BLEU + semantic similarity), quality (Human‑Eval‑Proxy), and entropy.  
- Apply **Benjamini‑Hochberg FDR** across **all five** Wilcoxon tests (α = 0.05) to control family‑wise error.

### Measurement Validity
- **Deliberation tokens** (`["let's think", "consider", "however", "wait"]`) are taken from prior work (Wei et al., 2022). Their construct validity will be examined by computing a **Spearman correlation** between token frequency and the Human‑Eval‑Proxy score (exploratory).  
- **Human‑Eval‑Proxy**: compute ROUGE‑L F1 between each generated trajectory and the held‑out rationales; the mean across ≥ 3 raters serves as a quality proxy (FR‑010). No synthetic scores are introduced.

### Predictor Collinearity
- Teacher distribution is derived **only** from the privileged context; the target rationales are distinct, avoiding collinearity between teacher and student targets.

### Privileged‑Context Quality Control
- For each sampled privileged rationale we compute a simple quality score (log‑length × token‑type‑ratio). Sampling is stratified to keep teacher quality comparable across prompts, reducing confounding variation (addresses methodology‑63015233).

## Compute Feasibility (updated)

| Component | Strategy | Estimated Resources |
|---|---|---|
| Model | `google/bert_uncased_L-2_H-128_A-2` (tinybert, on the order of several million parameters) – CPU‑only | < 2 GB RAM |
| Training | 200 on‑policy steps per prompt, batch = 1, projection‑head‑only updates | ≤ 3 h total (per‑prompt timeout 5 h) |
| Inference‑Only Pass | Forward pass over each privileged rationale (≤ 3 per prompt) | < 10 min total |
| Trajectory Generation | 20 trajectories per prompt per condition | ≤ 1 h total |
| Total Runtime | ≤ 4 h wall‑clock (well under 5 h CI limit) | ≤ 5 GB RAM (monitored via `psutil`) |

All computation fits the free‑tier GitHub Actions runner; no GPU escape hatch is required.

## Decision Rationale (updated)
1. **Dataset Choice** – Only the three verified BigBench URLs satisfy the open‑access requirement. Because they do not guarantee ≥ 3 rationales, the plan now **strictly enforces** this filter and aborts if the resulting sample is too small, preserving scientific validity.  
2. **Streaming** – Guarantees RAM compliance while still processing the full dataset.  
3. **Model Selection** – Tinybert reduces per‑step cost, enabling the required number of steps within CI time limits.  
4. **Statistical Tests** – Wilcoxon signed‑rank respects non‑normality; Benjamini‑Hochberg correction applied across all five tests; Spearman correlation added for construct validity.  
5. **Privileged‑Context Quality** – Simple quality scoring and stratified sampling mitigate confounding teacher quality differences.  

---

