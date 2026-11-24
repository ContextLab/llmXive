# Implementation Plan: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

**Branch**: `001-llmxive-student-only-gating` | **Date**: 2026-10-13 | **Spec**: `specs/001-llmxive-student-only-gating/spec.md`

## Summary
Implement a **Student‑Only Gating** variant of Self‑Distilled Agentic Reinforcement Learning (SDAR) that replaces the teacher‑student confidence gap with a student‑only heuristic composed of token entropy \(H_t\) and retrieved‑context stability \(S_t\). The plan runs training on **ALFWorld** and **WebShop**, logs per‑step computational metrics, and performs rigorous statistical analysis to verify:

* **SC‑001** – ≥ 80 % of the *baseline SDAR* improvement over the GRPO baseline is retained (i.e., \((\text{Success}_{\text{Student}} - \text{Success}_{\text{GRPO}}) / (\text{Success}_{\text{Baseline}} - \text{Success}_{\text{GRPO}}) \ge 0.80\)). This requires a GRPO (no‑distillation) control condition.
* **SC‑002** – ≥ 60 % reduction in per‑step CPU cost (measured on fixed‑step runs).
* **SC‑003** – Performance difference is statistically significant (p < 0.05 after Bonferroni correction).
* **SC‑004** – Convergence speed (steps to reach average reward ≥ 0.8) is reported.
* **SC‑005** – Pearson correlation between student‑only heuristic scores and teacher‑student gap is ≥ 0.6.

All functional requirements **FR‑001 – FR‑009** are addressed by concrete phases and tasks.

> **Spec discrepancy (flagged for kickback)**: the current `spec.md` SC‑001 still states the circular formula \((\text{Success}_{\text{Student}} - \text{Success}_{\text{Baseline}}) / \text{Success}_{\text{Baseline}} \ge 0.80\), and its Assumptions state "20 independent runs per variant (40 total)". This plan uses the gain‑retention formula above and **20 runs per variant per environment (120 total)** for the three‑variant, two‑environment design. The spec should be updated to match; this plan does not silently follow the inconsistent spec text.

## Technical Context
* **Language/Version**: Python 3.11
* **Primary Dependencies**: `transformers>=4.40.0`, `torch`, `bitsandbytes`, `datasets`, `sentence-transformers`, `numpy`, `pandas`, `scikit-learn`, `pytest`, `alfworld`, `webshop`, `psutil`
* **Student Model**: **Qwen2.5‑0.5B** (8‑bit quantized) – fits < 7 GB RAM on the CI runner.
* **Retriever**: `sentence‑transformers/all-MiniLM-L6-v2` (quantized) – verified source (see Research).
* **Storage**: Local filesystem under `data/` (JSONL for step‑level logs, Parquet for episode‑level aggregates).
* **Testing**: `pytest` with unit, integration, and schema‑validation tests.
* **Target Platform**: Linux GitHub Actions free tier (≈2 vCPU, ≈7 GB RAM, ≤6 h per job). **CPU‑only** execution; any attempt to fall back to GPU aborts with a clear error (FR‑009).
* **Constraints**: Memory < 7 GB RAM, disk < 14 GB, each job ≤ 6 h.

## Constitution Check
| Principle | Status | Verification Strategy |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/config.py`; `requirements.txt` pins exact versions; environments installed via `pip`. |
| **II. Verified Accuracy** | PASS | All citations (SDAR paper, ALFWorld, WebShop, Qwen2.5‑0.5B, MiniLM) are verified URLs (see `research.md`). |
| **III. Data Hygiene** | PASS | Raw environment packages are immutable; logs are checksum‑verified; no PII. |
| **IV. Single Source of Truth** | PASS | Figures/tables are generated programmatically from `data/processed/*`. |
| **V. Versioning Discipline** | PASS | Artifact hashes stored in `state/`; any change updates `updated_at`. |
| **VI. Computational Efficiency** | PASS | CPU‑time and memory logged per step (FR‑003); cost‑reduction target (SC‑002) is a hard gate. |
| **VII. Student‑Only Heuristic Fidelity** | PASS | Pearson correlation between student‑only gate and teacher‑student gap is computed as part of the analysis (FR‑007), preceded by a pilot construct-validity check (Phase 0b). |

## Project Structure
### Documentation (this feature)
```
specs/001-llmxive-student-only-gating/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── gating_signal.schema.yaml
    └── training_run.schema.yaml
```

### Source Code (repository root)
```
projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/
├── __init__.py
├── config.py                # seeds, hyper‑parameters, variant flags
├── main.py                  # CLI entry point
├── models/
│   ├── student_model.py     # Qwen2.5‑0.5B wrapper (8‑bit CPU)
│   └── retriever.py         # Quantized MiniLM retriever
├── agents/
│   ├── base_agent.py        # Abstract RL loop
│   ├── grpo_agent.py        # GRPO baseline
│   ├── baseline_agent.py    # Dual‑model SDAR (teacher + student)
│   └── student_only_agent.py# Student‑Only gating implementation
├── environments/
│   ├── __init__.py
│   ├── alfworld_env.py      # ALFWorld wrapper
│   └── webshop_env.py       # WebShop wrapper
├── metrics/
│   ├── cost_profiler.py     # CPU‑time & RSS tracking
│   └── statistical_test.py  # Bootstrapping & Mann‑Whitney U
├── utils/
│   ├── logging.py           # JSON/CSV logger
│   └── gating.py            # `g_t = σ(αH_t+βS_t)` implementation
└── tests/
    ├── test_gating.py
    ├── test_training_loop.py
    ├── test_environment_wrappers.py
    └── contract/
        ├── test_gating_schema.py
        └── test_training_run_schema.py
```

**Structure Decision**: A single‑project layout under `code/` keeps the CI runner footprint minimal and avoids cross‑package import overhead.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **Three variants (GRPO, Baseline, Student‑Only)** | Needed for SC‑001 (performance retention) which references the GRPO baseline as a reference point. | Using only two variants would make the "percentage of baseline improvement over GRPO" undefined. |
| **Bootstrapping plus paired design** | Small N = 20 × 2 environments still yields limited power; bootstrapping provides confidence intervals and effect sizes, while paired seeds reduce variance. | Relying solely on Mann‑Whitney would be overly conservative and give no effect‑size estimate. |
| **Quantized smaller student model** | Guarantees the experiment fits within the CPU‑only memory budget and eliminates the need for a GPU fallback. | Keeping the 1.7B model would exceed RAM limits on the free runner. |

## Phased Implementation Plan

| Phase | Goal | Tasks (mapped to FR/SC) |
|-------|------|--------------------------|
| **0 – Research & Feasibility** | Verify data sources, model loading, and compute budget. | • FR‑002: Confirm `alfworld` and `webshop` install via `pip` (no credentials).<br>• FR‑001: Prototype `S_t` using MiniLM‑L6‑v2 (verified source).<br>• FR‑006: Test gating function for NaN/Inf on pathological contexts.<br>• **Runner Pinning**: Use `runs-on: ubuntu-latest` matrix; record `lscpu` output and `psutil.cpu_freq` for each job to control hardware variance.<br>• **Power Analysis**: Using a medium effect size (d≈0.5) and α = 0.05, a two‑sample Mann‑Whitney test requires ≈18 runs per group for [deferred] power; we plan **20** runs per variant per environment (120 total, seeds 42‑61). |
| **0b – Pilot Correlation Analysis** | Empirically confirm that \(H_t\) and \(S_t\) correlate with the teacher‑student confidence gap before the main study. | • Run a short (2k steps) Baseline SDAR session on each environment.<br>• Compute per‑step teacher‑student gap, \(H_t\), and \(S_t\).<br>• Perform Pearson correlation; require \(r \ge 0.4\) as a minimal sanity check before proceeding. |
| **1 – Data Model & Contracts** | Define schemas for deterministic validation. | • FR‑001 → `GatingSignal` schema (contracts/gating_signal.schema.yaml).<br>• FR‑003 → `TrainingRun` schema (contracts/training_run.schema.yaml).<br>• FR‑004: Specify JSONL/Parquet storage conventions for **EpisodeMetrics** and **ComparisonReport** entities (see `data-model.md`).<br>• FR‑006: Add `is_valid` flag in schema. |
| **2 – Core Implementation** | Build training loop, gating, and profiling. | • FR‑001: Implement `student_only_agent.py` (entropy via `torch.nn.functional.softmax`, stability via cosine similarity).<br>• FR‑002: Implement `baseline_agent.py` (teacher + student forward passes).<br>• FR‑003: Integrate `cost_profiler.py` (process_time & `psutil` RSS).<br>• FR‑006: Guard against division‑by‑zero in `S_t` and clamp `g_t` to [0,1]. |
| **3 – Execution & Data Collection** | Run experiments and gather metrics. | • FR‑002: Execute **20** independent runs per variant per environment on **ALFWorld** then **WebShop** (total 120 runs, seeds 42‑61) to achieve ≥ 0.8 power.<br>• FR‑004: Persist logs to `data/processed/<run_id>.jsonl` and **EpisodeMetrics** to `episode_metrics.parquet` (used for bootstrapping in Phase 4).<br>• FR‑001 (analysis): Replay baseline trajectories through the Student‑Only agent to obtain paired gating scores for Pearson correlation (Principle VII).<br>• FR‑005: Run `statistical_test.py` (bootstrapping 1000 reps, Mann‑Whitney U for binary success, Bonferroni‑corrected α).<br>• **Cost‑Only Sub‑Phase**: For both Baseline SDAR and Student‑Only variants, run a fixed‑step job **without** early‑stopping to measure per‑step CPU cost uniformly. |
| **4 – Analysis & Reporting** | Produce the final comparison report. | • SC‑001: Compute performance‑retention percentage using the gain‑retention formula \((\text{Success}_{\text{Student}} - \text{Success}_{\text{GRPO}}) / (\text{Success}_{\text{Baseline}} - \text{Success}_{\text{GRPO}})\).<br>• SC‑002: Compute per‑step CPU‑time reduction from the Cost‑Only runs; verify ≥ 60 % reduction.<br>• SC‑003: Report bootstrapped p‑value (Bonferroni‑adjusted) and effect size (Cohen’s d), computed from the persisted **EpisodeMetrics**.<br>• SC‑004: Report convergence steps (from early‑stopping runs) to reward ≥ 0.8.<br>• SC‑005: Report Pearson r (must be ≥ 0.6).<br>• A **ComparisonReport** entity (see `data-model.md`) is generated in this phase and saved as `data/processed/comparison_report.json`. |
| **5 – Validation & Packaging** | Ensure reproducibility and schema compliance. | • Run pytest suite (unit, integration, contract validation).<br>• Verify SHA‑256 checksums of all `data/processed/*` files.<br>• Update `state/` artifact hashes. |

### Mapping of FR/SC to Phases
| FR / SC | Phase(s) |
|---------|----------|
| FR‑001 | 1, 2, 3, 4 |
| FR‑002 | 0, 3 |
| FR‑003 | 2, 3 |
| FR‑004 | 1, 3 |
| FR‑005 | 3, 4 |
| FR‑006 | 2, 3 |
| FR‑007 | 4 (paired‑trajectory analysis) |
| FR‑008 | 3 (baseline success metric logged as `final_success_rate` and stored for comparison) |
| FR‑009 | 0, 2 (CPU‑only guard) |
| SC‑001 | 4 |
| SC‑002 | 4 |
| SC‑003 | 4 |
| SC‑004 | 4 |
| SC‑005 | 4 |

## Compute Feasibility Strategy
* **CPU‑First**: Qwen2.5‑0.5B loaded with `bitsandbytes` 8‑bit quantization (`device="cpu"`). Retriever quantized to 8‑bit via `sentence-transformers` + `bitsandbytes`. Expected RAM ≈ 4 GB.
* **No GPU fallback**: All runs are forced onto the CPU runner; the code raises a clear `RuntimeError` if `torch.cuda.is_available()` is true, preventing hidden GPU usage.
* **Parallelisation**: The 120 runs are scheduled via a GitHub Actions matrix, keeping each job ≤ 6 h while the overall wall‑clock time stays within CI minute quotas.

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Entropy high for correct tokens (false negatives) | Include the `S_t` term; if `S_t` ≈ 0, fallback to entropy‑only gating with a lower `α`. |
| Noisy context → `S_t` ≈ 0 → gate collapse | Clamp `g_t` to a minimum of 0.05; log `is_valid=False` for diagnostics. |
| OOM on CI runner | Use 8‑bit quantization, limit context window to 256 tokens, stream environment data. |
| Low statistical power | Power analysis justifies N=20 per variant per environment (120 total); bootstrapping and paired seeds increase effective power; we explicitly report confidence intervals. |
| Runner‑to‑runner hardware variance confounding CPU‑time measurements (SC‑002) | Runner pinning via `runs-on: ubuntu-latest`; `lscpu` and `psutil.cpu_freq()` recorded per job and stored with logs; verify < 5 % hardware variance and treat it as a covariate if exceeded. |
| Missing contracts (previous issue) | Contracts are defined in Phase 1 and validated by unit tests before any downstream task. |
| Resource constraints exceeded | Fixed‑step caps and model size ensure each job stays within CPU, RAM, and time budgets. |

## Deliverables
* `plan.md` (this document)
* `research.md` (methodology, dataset table, statistical plan)
* `data-model.md` (entity definitions)
* `quickstart.md` (installation & run instructions)
* `contracts/gating_signal.schema.yaml` & `contracts/training_run.schema.yaml` (JSON‑Schema definitions)

---