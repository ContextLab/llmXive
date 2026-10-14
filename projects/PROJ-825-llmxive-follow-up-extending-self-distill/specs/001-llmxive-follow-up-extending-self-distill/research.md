# Research: llmXive follow‑up: extending "Self‑Distilled Agentic Reinforcement Learning"

## Executive Summary
We evaluate whether a **Student‑Only Gating** mechanism—using token entropy \(H_t\) and retrieved‑context stability \(S_t\) — can replace the teacher‑student confidence gap in Self‑Distilled Agentic Reinforcement Learning (SDAR) while preserving most of the performance gains. The hypothesis is that the student‑only heuristic retains **≥ 80 %** of the baseline improvement over GRPO and yields a **≥ 60 %** reduction in per‑step CPU cost.

## Background & Motivation
* **SDAR** achieves strong task performance by distilling a teacher’s confidence gap into a student model, but the teacher’s forward pass doubles inference cost, limiting deployment on edge devices.  
* **Student‑Only Gating** proposes to compute a gate \(g_t = \sigma(\alpha H_t + \beta S_t)\) where:
  * \(H_t = -\sum_i p_i \log p_i\) (token‑level entropy from the student’s softmax).
  * \(S_t = \cos\!\big(\text{emb}(\text{retrieved\_context}), \text{emb}(\text{current\_state})\big)\) (cosine similarity using a MiniLM retriever).
* If the heuristic approximates the teacher‑student gap, the costly teacher pass can be omitted.

## Research Questions
| ID | Question |
|----|----------|
| **RQ1** | Is Student‑Only gating **associated with** ≥ 80 % of the baseline SDAR performance gain over the GRPO baseline? *(associative claim)* |
| **RQ2** | Does Student‑Only reduce per‑step CPU time by **≥ 60 %** compared to Baseline SDAR? *(associative claim)* |
| **RQ3** | Is the Pearson correlation between the student‑only gate and the teacher‑student gap sufficiently strong to justify the heuristic? |

## Methodology

### Experimental Setup
| Component | Choice | Verification |
|-----------|--------|--------------|
| **Environments** | ALFWorld, WebShop | Installed via `pip install alfworld` and `pip install webshop` (open, programmatic). |
| **Student Model** | Qwen2.5‑0.5B (8‑bit quantized) | Downloadable from Hugging Face Hub (`Qwen/Qwen2.5-0.5B`). |
| **Retriever** | `sentence‑transformers/all‑MiniLM‑L6‑v2` (quantized) | Verified via HF Hub; reference: *all‑MiniLM‑L6‑v2* (source 2). |
| **Baselines** | GRPO (no distillation), Dual‑model SDAR (teacher + student) | Implemented in `code/agents/`. |
| **Hardware** | CPU‑only GitHub Actions (2 vCPU, ≈ 7 GB RAM) | No GPU fallback; runs must complete within 6 h. |

### Training Protocol
* **Seeds**: Fixed per run (e.g., 42‑46).  
* **Maximum steps**: 2 M or early‑stop when average per‑episode reward ≥ 0.8 for three consecutive episodes.  
* **Runs per variant**: **10** independent runs per environment (total 60 runs) to improve statistical power.  
* **Logging**: Per‑step `H_t`, `S_t`, `g_t`, CPU time (`process_time`), RSS memory (`psutil`). Logs written to `data/processed/<run_id>.jsonl`.  

### Statistical Analysis
* **Primary metric**: Cumulative reward per episode (continuous).  
* **Secondary metric**: Binary task success (1 = goal reached).  
* **Tests**:
  * **Bootstrapping** (1 000 resamples) on cumulative‑reward distributions to obtain 95 % confidence intervals and Cohen’s d effect sizes.  
  * **Mann‑Whitney U** for binary success rates (non‑parametric).  
* **Multiple‑comparison correction**: Three hypothesis tests (performance retention, cost reduction, correlation) → **Bonferroni correction** → adjusted α = 0.05 / 3 ≈ 0.0167.  
* **Power justification**: With N = 10 paired runs per variant, power remains modest; we acknowledge this limitation and report effect sizes alongside confidence intervals.  
* **Causal inference**: Observational; claims are strictly associative.  
* **Measurement validity**: Qwen2.5 token‑probability outputs are standard; MiniLM retrieval has published validation (source 2).  
* **Collinearity note**: \(H_t\) and \(S_t\) may be correlated; we report their Pearson correlation and treat them jointly in the sigmoid gate.

### Paired Trajectory Analysis (Constitution VII)
* Save baseline trajectories (state, action, teacher‑student gap).  
* Replay each trajectory through the Student‑Only agent **without** re‑sampling, generating paired gating scores.  
* Compute Pearson r between `g_t` and the original teacher‑student gap across all paired steps.  

## Dataset Strategy
| Dataset / Resource | Source | Verified? | Use |
|--------------------|--------|-----------|-----|
| **ALFWorld** | `pip install alfworld` | ✅ (PyPI) | Text‑based household task environment. |
| **WebShop** | `pip install webshop` | ✅ (PyPI) | Text‑based e‑commerce interaction environment. |
| **Qwen2.5‑0.5B** | Hugging Face Hub `Qwen/Qwen2.5-0.5B` | ✅ (HF) | Student model for all variants. |
| **Retriever Model** | Hugging Face Hub `sentence-transformers/all‑MiniLM‑L6‑v2` | ✅ (HF) | Computes context stability \(S_t\). |
| **GRPO Baseline Code** | Internal implementation | N/A | Control condition. |

*All resources are openly downloadable without credentials, satisfying the compute‑feasibility requirement.*

## Ethical Considerations & Limitations
* **Synthetic environments**: Results may not transfer directly to real‑world domains; external validity is limited.  
* **Model size**: Qwen2.5‑0.5B is modest; scaling to larger models may alter the entropy‑stability relationship.  
* **Sample size**: N = 10 per variant limits statistical power; we explicitly report confidence intervals and effect sizes.  
* **Resource constraints**: Early‑stopping may truncate long‑tail learning dynamics; we note this in the discussion.  

## References
1. **Self‑Distilled Agentic Reinforcement Learning (SDAR)** – original paper (to be verified during implementation).  
2. **ALFWorld** – Shridhar et al., “ALFWorld: Aligning Text and Embodied Environments for Interactive Learning.” (Verified via PyPI).  
3. **WebShop** – Yan et al., “WebShop: Towards Scalable Real‑World Web Interaction with Grounded Language Agents.” (Verified via PyPI).  
4. **Qwen2.5 Technical Report** – Qwen Team, Hugging Face Hub.  
5. **Sentence‑BERT** – Reimers & Gurevych, “Sentence‑BERT: Sentence Embeddings using Siamese BERT‑Networks.” (Verified source 2).  

---

