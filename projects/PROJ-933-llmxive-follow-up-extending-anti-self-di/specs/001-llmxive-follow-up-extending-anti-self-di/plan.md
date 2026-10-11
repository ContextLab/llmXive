# Implementation Plan: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

**Branch**: `001-llmxive-followup` | **Date**: 2026-10-11 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary
The project tests whether the *deliberation reward* of Anti‑Self‑Distillation (AntiSD) generalizes to non‑verifiable reasoning domains. It does so by (1) ingesting the **UltraFeedback** and **Dolly** datasets, (2) filtering prompts that have **≥ 4** distinct high‑quality rationales, (3) randomly selecting one rationale as the *privileged context* and treating the remaining rationales as the *target distribution*, (4) computing a teacher distribution from the unselected rationales (Inference‑Only Pass), (5) training a small transformer with a custom PyTorch loop that **maximizes** Jensen‑Shannon (JS) divergence for AntiSD (gradient inversion) and **minimizes** it for standard self‑distillation, and (6) evaluating diversity, deliberation token frequency, and reasoning quality via a Human Evaluation Proxy. All steps run on the GitHub Actions free‑tier CPU runner; a hard timeout of 5.5 h guarantees compliance with CI limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0+cpu`, `transformers==4.41.2`, `datasets==2.19.0`, `scikit-learn==1.5.0`, `nltk==3.8.1`, `sentence‑transformers==2.2.2`, `pandas==2.2.2`, `numpy==1.26.4`, `matplotlib==3.8.4`. All versions are pinned in `requirements.txt`.  
- **Storage**: Ephemeral `/tmp` for streaming shards; persistent `data/` for raw, processed, and results files.  
- **Testing**: `pytest` for unit tests; integration tests for the custom training loop and gradient‑inversion logic.  
- **Target Platform**: Linux (GitHub Actions free tier).  
- **Project Type**: Computational research pipeline.  
- **Performance Goals**: Complete the full pipeline (data → analysis) ≤ 6 h, peak RAM < 6.5 GB.  
- **Constraints**: CPU‑only; no GPU fallback is required.  
- **Scale/Scope**: Process up to ~40 prompts (≥ 30 meeting the ≥ 4‑trace requirement) with 250 training steps each.

## Constitution Check
| Principle | Status | Action / Reference |
|---|---|---|
| **I. Reproducibility** | ✅ | Fixed random seeds (`config/settings.yaml`), deterministic dataset download via HuggingFace, `requirements.txt` pins all packages. |
| **II. Verified Accuracy** | ✅ | Only the three URLs listed in the “Verified datasets” block are used (see `research.md`). |
| **III. Data Hygiene** | ✅ | Checksums recorded in `data/raw/checksums.json`; all transformations write new files (`data/processed/…`). |
| **IV. Single Source of Truth** | ✅ | Every figure/metric is derived from files validated against the JSON/YAML contracts. |
| **V. Versioning Discipline** | ✅ | Artifacts are hashed; `state/projects/…yaml` will be updated automatically after each run. |
| **VI. Multi‑Solution Context Simulation** | ✅ | Random privileged‑context sampling (FR‑002) and retention of the remaining rationales (FR‑014) are explicitly implemented. |
| **VII. Token‑Level Entropy & Diversity** | ✅ | Deliberation‑token counting, pairwise BLEU, and sentence‑transformer similarity are computed (FR‑005, FR‑009). |

## Project Structure
```
specs/001-llmxive-followup/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── training_output.schema.yaml
    ├── analysis_results.schema.yaml
    ├── output.schema.yaml
    └── teacher_logits.schema.yaml
```

```
projects/PROJ-933-llmxive-followup-extending-anti-self-di/code/
├── data/
│   ├── download.py          # fetches & checksums UltraFeedback/Dolly
│   ├── preprocess.py        # filters ≥4‑trace prompts, creates context split
│   └── raw/                 # cached shards (read‑only)
├── models/
│   ├── anti_sd_loop.py      # custom training loop with gradient inversion
│   ├── inference_only.py    # teacher‑distribution (logits) computation
│   └── metrics.py           # BLEU, semantic similarity, token counting, JS
├── analysis/
│   ├── statistical_test.py  # Wilcoxon + Benjamini‑Hochberg FDR correction
│   └── visualize.py         # loss/JS curves, diversity plots
├── config/
│   └── settings.yaml        # seeds, hyper‑params, timeout
├── main.py                  # orchestrates the pipeline
└── requirements.txt
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| **Custom training loop** | FR‑008 requires token‑level gradient inversion; existing RL libraries cannot express this directly. | Using a generic RL library would either hide the gradient‑inversion step or require extensive hacking, breaking reproducibility. |
| **Streaming dataset** | UltraFeedback > 7 GB; loading whole set would OOM (Principle III). | Loading full dataset would exceed RAM limits and cause CI failures. |
| **Wilcoxon test** | FR‑017 mandates a non‑parametric test; small N makes t‑test assumptions untenable. | A t‑test would risk inflated Type I error under non‑normality. |

## Phase Breakdown & FR/SC Coverage
| Phase | Tasks | Covered FR(s) | Covered SC(s) |
|---|---|---|---|
| **Phase 0 – Research & Data Verification** | Audit UltraFeedback/Dolly for ≥4 rationales, compute achievable N, run power analysis (FR‑013, FR‑018). | FR‑001, FR‑016, FR‑013, FR‑018 | SC‑007 |
| **Phase 1 – Data Model & Contracts** | Define schemas (dataset, teacher‑logits, training output, analysis results). | FR‑002, FR‑005, FR‑014, FR‑015 | — |
| **Phase 2 – Implementation** | • `download.py` & `preprocess.py` (FR‑001, FR‑002, FR‑012, FR‑016) <br> • `inference_only.py` (FR‑014) <br> • `anti_sd_loop.py` (FR‑003, FR‑004, FR‑008) <br> • Timeout & checkpointing (FR‑007) | FR‑001‑008, FR‑012‑016 | — |
| **Phase 3 – Execution** | Run pipeline on CI, collect per‑prompt logs (`training_output.schema.yaml`). | FR‑003‑009, FR‑010‑011, FR‑014 | SC‑001‑006 |
| **Phase 4 – Analysis & Reporting** | Compute BLEU, semantic similarity, deliberation token frequency, Human‑Eval Proxy, Pearson r, Wilcoxon tests, FDR correction, power reporting (FR‑006‑018). | FR‑005‑011, FR‑013‑018 | SC‑001‑007 |
| **Phase 5 – Validation** | Verify contracts, ensure no fabricated metrics, confirm `teacher_logits_raw.jsonl` exists and conforms to schema. | — | — |

### Fabricated‑Metric Fix
The previous placeholder “Mock Score Validation” has been removed. All reported metrics are derived from **real** computations defined in `analysis/` (BLEU, semantic similarity, JS divergence, deliberation token counts, Human Evaluation Proxy scores). No synthetic or hard‑coded scores remain.

---
