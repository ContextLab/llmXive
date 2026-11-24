# Implementation Plan: llmXive follow‑up: extending “Anti‑Self‑Distillation for Reasoning RL via Pointwise Mutual Information”

**Branch**: `001-llmxive-follow-up-extending-anti-self-di` | **Date**: 2026‑10‑11 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-anti-self-di/spec.md`

## Summary
The project investigates whether the *deliberation reward* (Anti‑Self‑Distillation, AntiSD) improves reasoning diversity and quality in **non‑verifiable** domains where the privileged context is a randomly sampled high‑quality rationale rather than a single ground‑truth solution.

Key steps (updated to address reviewer concerns):

1. **Data acquisition & filtering** – download verified open‑source datasets, retain **only** prompts with **≥ 3** rationales (FR‑001). If fewer than 30 prompts survive, abort the run and report insufficient data (strict enforcement, no relaxation).  
2. **Privileged‑context simulation** – randomly sample one rationale per prompt as the teacher context `c`; compute a simple quality score for each sampled rationale (log‑length × token‑type‑ratio) and stratify sampling to keep teacher quality comparable across prompts. Remaining rationales become the target distribution.  
3. **Custom training loop** – compute PMI‑weighted KL loss, Jensen‑Shannon divergence (JSD), invert the JSD gradient for AntiSD, and update **only** the projection head. Log **all** fields required by `training_output.schema.yaml`: loss, JSD, gradient dot product, generated trajectory, deliberation tokens, entropy per token, training time, and peak memory.  
4. **Trajectory generation** – generate **20** trajectories per prompt per condition (reduced from 50) and store them under `data/results/trajectories/`.  
5. **Metric collection** – compute (i) deliberation‑token frequency (FR‑008), (ii) pairwise BLEU‑4 (FR‑009), (iii) MiniLM‑L6‑v2 cosine similarity (FR‑009), (iv) Human‑Evaluation‑Proxy (mean ROUGE‑L F1) (FR‑010), (v) token‑level entropy (FR‑015).  
6. **Statistical analysis** – perform Wilcoxon signed‑rank tests for each metric, apply **Benjamini‑Hochberg FDR correction across all five tests**, report effect sizes (Cliff’s δ). Additionally, compute Spearman correlation between deliberation‑token frequency and the Human‑Evaluation‑Proxy to assess construct validity (exploratory).  
7. **Reporting** – assemble `results/final_report.json` (SSoT) containing aggregated metrics, statistical outcomes, correlation results, and a concise conclusion (FR‑014).  

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `requirements.txt`):  
  `torch==2.3.0+cpu`, `transformers==4.41.2`, `datasets==2.19.0`, `scikit-learn==1.5.0`, `nltk==3.8.1`, `sentence‑transformers==2.2.2`, `pandas==2.2.2`, `numpy==1.26.4`, `matplotlib==3.8.4`, `psutil==5.9.8`.  
- **Model**: `google/bert_uncased_L-2_H-128_A-2` (≈15 M parameters, CPU‑friendly).  
- **Storage**: Files under `data/` (raw, processed, results).  
- **Testing**: `pytest` for unit tests; integration tests for the training loop and gradient inversion.  
- **Target Platform**: Linux GitHub Actions free tier (2 vCPU, ≤ 7 GB RAM, ≤ 14 GB disk).  
- **Constraints**: CPU‑only; no GPU fallback required.

## Compute Feasibility (updated)
| Component | Strategy | Estimated Resources |
|---|---|---|
| Model | TinyBERT (a compact model with on the order of tens of millions of parameters) – CPU‑only | < 2 GB RAM |
| Training | 200 on‑policy steps per prompt, batch = 1, projection‑head‑only updates | ≤ 3 h total (per‑prompt timeout 5 h) |
| Inference‑Only Pass | Forward pass over each privileged rationale (≤ 3 per prompt) | < 10 min total |
| Trajectory Generation | 20 trajectories per prompt per condition | ≤ 1 h total |
| Total Runtime | ≤ 4 h wall‑clock (well under 5 h CI limit) | ≤ 5 GB RAM (monitored via `psutil`) |

All computation fits the free‑tier runner; no GPU escape hatch is needed.

## Constitution Check (updated)
| Principle | Status | Action / Reference |
|---|---|---|
| I. Reproducibility | ✅ | Fixed seeds (`2026`) in `config/settings.yaml`; deterministic dataset download via HuggingFace; all dependencies pinned. |
| II. Verified Accuracy | ✅ | All citations use the verified URLs listed in the “Verified datasets” block. No deviation. |
| III. Data Hygiene | ✅ | Checksums recorded in `data/raw/checksums.json`; every transformation writes a new file. |
| IV. Single Source of Truth | ✅ | `results/final_report.json` is the SSoT for all figures, tables, and conclusions. |
| V. Versioning Discipline | ✅ | All artifacts hashed; `state/projects/...yaml` updated automatically. |
| VI. Multi‑Solution Context Simulation | ✅ | Random privileged‑context sampling with quality‑score stratification (FR‑002). |
| VII. Token‑Level Entropy & Diversity | ✅ | Deliberation‑token counting, entropy logging, BLEU & MiniLM similarity computed against **unselected** rationales (FR‑008, FR‑009, FR‑015). |
| **FR‑001 Compliance** | ✅ | The pipeline **strictly** filters for prompts with ≥ 3 rationales, skips any that fail, and aborts if fewer than 30 prompts remain, preserving the multi‑solution requirement. |

## Phase Breakdown & FR/SC Coverage (updated)
| Phase | Tasks | Covered FR(s) | Covered SC(s) |
|---|---|---|---|
| **Phase 0 – Data Verification** | • Download verified datasets via `datasets.load_dataset(..., streaming=True)`. <br>• Scan for prompts with **≥ 3** rationales; retain only those, log shortfalls. <br>• Abort run if filtered prompts < 30 (hard stop). <br>• Perform non‑parametric power simulation for Wilcoxon (effect size ≈ 0.5, α = 0.05). | FR‑001 (strict), FR‑012, FR‑013 | SC‑007 (power), SC‑004 (runtime) |
| **Phase 1 – Schema Definition** | Define contracts for dataset, context split, teacher logits, training output, analysis results. | FR‑002‑FR‑006, FR‑014‑FR‑015 | — |
| **Phase 2 – Data Prep** | `download.py` & `preprocess.py` – filter, split privileged context, compute teacher quality score, generate `context_split.jsonl`. <br>`inference_only.py` – compute teacher logits for each privileged rationale, store `teacher_logits_raw.jsonl`. | FR‑001‑FR‑006, FR‑012 | — |
| **Phase 3 – Training Loop** | `anti_sd_loop.py` – custom PyTorch loop (200 steps per prompt). Implements PMI‑weighted KL, JSD, gradient inversion, updates projection head only. Logs **all** fields required by `training_output.schema.yaml` (loss, JSD, gradient dot product, generated_trajectory, deliberation_tokens, entropy_per_token, training_time_seconds, peak_memory_mb). | FR‑003‑FR‑005, FR‑015, FR‑013 | SC‑001‑SC‑003 (Wilcoxon later) |
| **Phase 4 – Trajectory Generation** | Generate 20 trajectories per prompt per condition; store under `data/results/trajectories/`. | FR‑007 | — |
| **Phase 5 – Metric Computation** | Compute (i) deliberation‑token frequency (FR‑008), (ii) pairwise BLEU‑4 (FR‑009), (iii) MiniLM cosine similarity (FR‑009), (iv) ROUGE‑L F1 Human‑Eval‑Proxy (FR‑010), (v) token‑level entropy (FR‑015). | FR‑008‑FR‑010, FR‑015 | — |
| **Phase 6 – Statistical Analysis** | Wilcoxon signed‑rank tests for each metric, Benjamini‑Hochberg correction across all five tests, Cliff’s δ effect sizes, Spearman correlation (deliberation ↔ quality) for construct validity. | FR‑011 | SC‑001‑SC‑003, SC‑006 (effect‑size threshold) |
| **Phase 7 – Reporting** | Assemble `results/final_report.json` (SSoT) with aggregated metrics, statistical outcomes, correlation results, and concise conclusion (FR‑014). | FR‑014 | SC‑001‑SC‑006 |
| **Phase 8 – Validation** | Contract validation for all output files; checksum verification for `teacher_logits_raw.jsonl`. | — | — |

All functional requirements (FR‑001 → FR‑015) are now explicitly mapped to concrete tasks, and every success criterion (SC‑001 → SC‑007) is addressed in the pipeline.

## Additional Mitigations
- **Privileged‑Context Quality Control**: quality scores are logged in `context_split.jsonl`; downstream analyses can condition on these scores.
- **Exploratory Deliberation Metric**: correlation with Human‑Eval‑Proxy reported; not used as a primary hypothesis test.
- **Multiple‑Comparison Coverage**: BH correction applied to all five Wilcoxon tests, ensuring controlled FDR.
- **Power Analysis Alignment**: non‑parametric simulation matches the planned Wilcoxon tests.

---

