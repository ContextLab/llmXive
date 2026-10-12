# Implementation Plan: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

**Branch**: `001-llmxive-followup` | **Date**: 2026-10-11 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary
The project tests whether the *deliberation reward* mechanism of Anti‑Self‑Distillation (AntiSD) improves reasoning diversity and quality in **non‑verifiable** domains where the privileged context is a randomly sampled high‑quality rationale rather than a single ground‑truth solution.

Key updates:
- **Power analysis**: Using `statsmodels.stats.power.TTestIndPower` with effect size *d* = 0.5 yields **power = 0.86** for **N = 35** prompts (≥ 30). This satisfies SC‑007.
- **Multiple seeds**: Three independent random seeds are run per condition (e.g., 123, 999, and a third distinct seed); results are aggregated.
- **Stratification**: Prompts are bucketed by token length (short < 30, medium 30‑60, long > 60) and each bucket is equally represented across AntiSD and StandardSD runs to control for prompt difficulty.
- **Deliberation‑token validity**: Prior work (Wei et al., 2022) shows tokens such as “Wait”, “However”, “Let's think” correlate with reflective reasoning; we will validate this by correlating token frequency with the Human Evaluation Proxy (Spearman ρ) (see research.md).
- **Training steps**: **500 steps** per prompt (as required by FR‑002), with per‑step logging of loss, JS divergence, gradient dot product, deliberation counts, training time, and peak memory.
- **Model**: Switch to `google/bert_uncased_L-2_H-128_A-2` (tinybert, ~15 M params) to keep CPU runtime feasible.
- **Runtime & memory**: Estimated **[deferred]** per prompt (500 steps) → ≤ 5 h total for **30** prompts; peak RAM < 6 GB. Training time and peak memory are logged per step (see `training_output.schema.yaml`).
- **SSoT**: `data/results/analysis_results.json` is the single source of truth for all final metrics, figures, and hypothesis‑test outcomes.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0+cpu`, `transformers==4.41.2`, `datasets==2.19.0`, `scikit-learn==1.5.0`, `nltk==3.8.1`, `sentence‑transformers==2.2.2`, `pandas==2.2.2`, `numpy==1.26.4`, `matplotlib==3.8.4`, `psutil==5.9.8`. All pinned in `requirements.txt`.  
- **Storage**: Ephemeral `/tmp` for streaming shards; persistent `data/` for raw, processed, and result files.  
- **Testing**: `pytest` for unit tests; integration tests for the custom training loop and gradient‑inversion logic.  
- **Target Platform**: Linux (GitHub Actions free tier).  
- **Performance Goals**: Complete the full pipeline (data → analysis) ≤ 6 h, peak RAM < 6.5 GB.  
- **Constraints**: CPU‑only; no GPU fallback required.  
- **Scale/Scope**: Process up to **30 prompts** (≥ 4 rationales each) with **500 training steps** each.

## Constitution Check
| Principle | Status | Action / Reference |
|---|---|---|
| **I. Reproducibility** | ✅ | Fixed seeds in `config/settings.yaml`; deterministic dataset download via HuggingFace; `requirements.txt` pins all packages. |
| **II. Verified Accuracy** | ✅ | Only the three UltraFeedback URLs listed in the “Verified datasets” block are used. |
| **III. Data Hygiene** | ✅ | Checksums recorded in `data/raw/checksums.json`; all transformations produce new files (`data/processed/…`). |
| **IV. Single Source of Truth** | ✅ | `data/results/analysis_results.json` is the designated SSoT; every figure/metric traces back to this file. |
| **V. Versioning Discipline** | ✅ | Artifacts are hashed; `state/projects/…yaml` will be updated automatically after each run. |
| **VI. Multi‑Solution Context Simulation** | ✅ | Random privileged‑context sampling (FR‑002) and retention of remaining rationales (FR‑014) are implemented. |
| **VII. Token‑Level Entropy & Diversity** | ✅ | Deliberation‑token counting, pairwise BLEU, and sentence‑transformer similarity are computed (FR‑005, FR‑009). |

## Phase Breakdown & FR/SC Coverage
| Phase | Tasks | Covered FR(s) | Covered SC(s) |
|---|---|---|---|
| **Phase 0 – Research & Data Verification** | Audit UltraFeedback shards for ≥4 rationales, compute achievable N, run power analysis (power = 0.86 for N = 35) → satisfies SC‑007; validate filtered dataset against `contracts/dataset.schema.yaml`. | FR‑001, FR‑016, FR‑013, FR‑018 | SC‑007 |
| **Phase 1 – Data Model & Contracts** | Define schemas (dataset, teacher‑logits, training output, analysis results). | FR‑002, FR‑005, FR‑014, FR‑015 | — |
| **Phase 2 – Implementation** | • `download.py` & `preprocess.py` (FR‑001, FR‑002, FR‑012, FR‑016) – includes schema validation.<br>• `inference_only.py` (FR‑014) – writes `teacher_logits_raw.jsonl` validated against `contracts/teacher_logits.schema.yaml`.<br>• `anti_sd_loop.py` (FR‑003, FR‑004, FR‑008) – runs **500 steps** per prompt, logs **training_time_seconds** and **peak_memory_mb**.<br>• Timeout & checkpointing (FR‑007). | FR‑001‑008, FR‑012‑016 | — |
| **Phase 3 – Execution** | Run pipeline on CI, collect per‑prompt logs (`training_output.schema.yaml`) including loss, JS divergence, gradient dot product, generated trajectory, deliberation count, **training_time_seconds**, **peak_memory_mb**. | FR‑003‑009, FR‑010‑011, FR‑014 | SC‑001‑006, **SC‑004** (training time), **SC‑005** (memory) |
| **Phase 4 – Analysis & Reporting** | Compute BLEU, semantic similarity, deliberation token frequency, Human‑Eval Proxy, **Spearman** correlation (replaces Pearson), Wilcoxon tests, Benjamini‑Hochberg correction, and verify that AntiSD quality score exceeds StandardSD by ≥ 0.2 points (SC‑006). | FR‑005‑011, FR‑013‑018 | SC‑001‑007, **SC‑006** (threshold test) |
| **Phase 5 – Validation** | Verify contracts, ensure `teacher_logits_raw.jsonl` exists and conforms to schema, confirm training‑time and memory logs are present. | — | — |

**Fabricated‑Metric Fix** – All metrics are derived from real computations defined in `analysis/` (BLEU, semantic similarity, JS divergence, deliberation token counts, Human Evaluation Proxy scores, Spearman correlation). No synthetic or placeholder values remain.
