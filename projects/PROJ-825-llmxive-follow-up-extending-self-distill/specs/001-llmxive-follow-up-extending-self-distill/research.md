# Research: llmXive follow‑up: extending "Self‑Distilled Agentic Reinforcement Learning"

## Executive Summary
We evaluate whether a **Student‑Only Gating** mechanism—using token entropy \(H_t\) and retrieved‑context stability \(S_t\) — can replace the teacher‑student confidence gap in Self‑Distilled Agentic Reinforcement Learning (SDAR) while preserving most of the performance gains. The hypothesis is that the student‑only heuristic retains **≥ 80 %** of the baseline improvement over GRPO and yields a **≥ 60 %** reduction in per‑step CPU cost.

## Background & Motivation
* **SDAR** achieves strong task performance by distilling a teacher’s confidence gap into a student model, but the teacher’s forward pass doubles inference cost, limiting deployment on edge devices.
* **Student‑Only Gating** proposes to compute a gate \(g_t = \sigma(\alpha H_t + \beta S_t)\) where:
  * \(H_t = -\sum_i p_i \log p_i\) (token‑level entropy from the student’s softmax).
  * \(S_t = \cos\!\big(\text{emb}(\text{retrieved\_context}), \text{emb}(\text{current\_state})\big)\) (cosine similarity using a MiniLM retriever).
* If the heuristic approximates the teacher‑student gap, the costly teacher pass can be omitted.

## Research Questions
| ID | Question |
|----|----------|
| **RQ1** | Is Student‑Only gating **associated with** ≥ 80 % of the baseline SDAR performance gain over the GRPO baseline? *(associative claim)* |
| **RQ2** | Does Student‑Only reduce per‑step CPU time by **≥ 60 %** compared to Baseline SDAR? *(associative claim)* |
| **RQ3** | Is the Pearson correlation between the student‑only gate and the teacher‑student gap sufficiently strong to justify the heuristic? |

## Methodology

### Experimental Setup
| Component | Choice | Verification |
|-----------|--------|--------------|
| **Environments** | ALFWorld, WebShop | Installed via `pip install alfworld` and `pip install webshop` (open, programmatic). |
| **Student Model** | Qwen2.5‑0.5B (8‑bit quantized) | Downloadable from Hugging Face Hub (`Qwen/Qwen2.5-0.5B`). |
| **Retriever** | `sentence‑transformers/all-MiniLM-L6-v2` (quantized) | Verified via HF Hub; reference: *all‑MiniLM‑L6‑v2* (source 2). |
| **Baselines** | GRPO (no distillation), Dual‑model SDAR (teacher + student) | Implemented in `code/agents/`. |
| **Hardware** | CPU‑only GitHub Actions (2 vCPU, ≈ 7 GB RAM) | No GPU fallback; runs must complete within 6 h. |
| **Runner Pinning** | Use `runs-on: ubuntu-latest` matrix; record `lscpu` output and `psutil.cpu_freq()` at start of each job to capture CPU model and frequency. These metadata are stored alongside logs and used to verify that hardware variance is negligible (target < 5 % variation); if exceeded, it is treated as a covariate in the cost analysis. |

### Pilot Correlation Analysis (Phase 0b)
Before the full experiment we run a **pilot** (≈ 2k steps) of the Baseline SDAR on each environment to collect teacher‑student gap scores, \(H_t\), and \(S_t\). We compute Pearson r for each pair; a minimum \(r \ge 0.4\) is required to proceed. This validates the construct of the student‑only heuristic (addresses concern methodology‑61d25d22).

### Training Protocol
* **Seeds**: Fixed per run (42‑61).
* **Maximum steps**: 2M or early‑stop when average per‑episode reward ≥ 0.8 for three consecutive episodes.
* **Runs per variant**: **20** independent runs per variant per environment (total **120** runs).
* **Power justification**: Assuming a medium effect size (Cohen’s d ≈ 0.5) for both performance retention and cost reduction, a two‑sample Mann‑Whitney test with α = 0.05 requires ≈ 18 runs per group for [deferred] power. We round up to 20 to provide a safety margin.
* **Logging**: Per‑step `H_t`, `S_t`, `g_t`, CPU time (`process_time`), RSS memory (`psutil`). Logs written to `data/processed/<run_id>.jsonl`. Runner hardware metadata are added to each log record.

### Statistical Analysis
* **Primary metric**: Cumulative reward per episode (continuous).
* **Secondary metric**: Binary task success (1 = goal reached).
* **Performance retention (SC‑001)**: computed with the gain‑retention formula \((\text{Success}_{\text{Student}} - \text{Success}_{\text{GRPO}}) / (\text{Success}_{\text{Baseline}} - \text{Success}_{\text{GRPO}}) \ge 0.80\) — the proportion of the original SDAR improvement over the GRPO control that the Student‑Only variant preserves. This requires the GRPO control condition; the earlier circular formula \((\text{Success}_{\text{Student}} - \text{Success}_{\text{Baseline}}) / \text{Success}_{\text{Baseline}}\) is NOT used.
* **Tests**:
  * **Bootstrapping** (1 000 resamples) on cumulative‑reward distributions to obtain 95 % confidence intervals and Cohen’s d effect sizes.
  * **Mann‑Whitney U** for binary success rates (non‑parametric).
* **Multiple‑comparison correction**: Three hypothesis tests (performance retention, cost reduction, correlation) → **Bonferroni correction** → adjusted α = 0.05 / 3 ≈ 0.0167.
* **Power justification**: With N = 20 paired runs per variant per environment, power remains ≥ 0.8 for medium effects; we report effect sizes and confidence intervals alongside p‑values.
* **Causal inference**: Observational; claims are strictly associative.
* **Measurement validity**: Qwen2.5 token‑probability outputs are standard; MiniLM retrieval has published validation (source).
* **Collinearity note**: \(H_t\) and \(S_t\) may be correlated; we report their Pearson correlation and treat them jointly in the sigmoid gate.

### Paired Trajectory Analysis (Constitution VII)
* Save baseline trajectories (state, action, teacher‑student gap).
* Replay each trajectory through the Student‑Only agent **without** re‑sampling, generating paired gating scores.
* Compute Pearson r between `g_t` and the original teacher‑student gap across all paired steps.

## Dataset Strategy
| Dataset / Resource | Source | Verified? | Use |
|--------------------|--------|-----------|-----|
| **ALFWorld** | `pip install alfworld` | ✅ (PyPI) | Text‑based household task environment. |
| **WebShop** | `pip install webshop` | ✅ (PyPI) | Text‑based e‑commerce interaction environment. |
| **Qwen2.5‑0.5B** | Hugging Face Hub `Qwen/Qwen2.5-0.5B` | ✅ (HF) | Student model for all variants. |
| **Retriever Model** | Hugging Face Hub `sentence-transformers/all-MiniLM-L6-v2` | ✅ (HF) | Computes context stability \(S_t\). |
| **GRPO Baseline Code** | Internal implementation | N/A | Control condition required by the SC‑001 gain‑retention formula. |

*All resources are openly downloadable without credentials, satisfying the compute‑feasibility requirement.*

## Ethical Considerations & Limitations
* **Synthetic environments**: Results may not transfer directly to real‑world domains; external validity is limited.
* **Model size**: Qwen2.5‑0.5B is modest; scaling to larger models may alter the entropy‑stability relationship.
* **Sample size**: Although powered for medium effects, smaller effect sizes may remain undetected; we explicitly report confidence intervals.
* **Resource constraints**: Early‑stopping may truncate long‑tail learning dynamics; we note this in the discussion.

## Spec Discrepancy Note (flagged for kickback)
`spec.md` SC‑001 still contains the circular formula \((\text{Success}_{\text{Student}} - \text{Success}_{\text{Baseline}}) / \text{Success}_{\text{Baseline}} \ge 0.80\), and its Assumptions state "20 independent runs per variant (40 total)". This research document uses the gain‑retention formula (with the GRPO control) and **20 runs per variant per environment (120 total)**. The spec should be corrected to match.

## References
1. **Self‑Distilled Agentic Reinforcement Learning (SDAR)** – original paper (to be verified during implementation).
2. **ALFWorld** – Shridhar et al., “ALFWorld: Aligning Text and Embodied Environments for Interactive Learning.” (Verified via PyPI).
3. **WebShop** – Yan et al., “WebShop: Towards Scalable Real‑World Web Interaction with Grounded Language Agents.” (Verified via PyPI).
4. **Qwen2.5 Technical Report** – Qwen Team, Hugging Face Hub.
5. **Sentence‑BERT** – Reimers & Gurevych, “Sentence‑BERT: Sentence Embeddings using Siamese BERT‑Networks.” (Verified source 2).

---