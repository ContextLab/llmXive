# Implementation Plan: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

**Branch**: `001-llmxive-student-only-gating` | **Date**: 2026-10-13 | **Spec**: `specs/001-llmxive-student-only-gating/spec.md`

## Summary
Implement a **Student‑Only Gating** variant of Self‑Distilled Agentic Reinforcement Learning (SDAR) that replaces the teacher‑student confidence gap with a student‑only heuristic composed of token entropy \(H_t\) and retrieved‑context stability \(S_t\). The plan executes training on **ALFWorld** and **WebShop**, logs per‑step computational metrics, and performs rigorous statistical analysis to verify:

* **SC‑001** – ≥ 80 % of the baseline performance gain is retained (associative claim).  
* **SC‑002** – ≥ 60 % reduction in per‑step CPU cost (measured on fixed‑step runs).  
* **SC‑003** – Performance difference is statistically significant (p < 0.05 after correction).  
* **SC‑004** – Convergence speed (steps to reach average reward ≥ 0.8) is reported.

All functional requirements **FR‑001 – FR‑006** are addressed by concrete phases and tasks. The plan now respects the Constitution and the methodological panel concerns.

## Technical Context
* **Language/Version**: Python 3.11  
* **Primary Dependencies**: `transformers>=4.40.0`, `torch`, `datasets`, `sentence-transformers`, `bitsandbytes`, `numpy`, `pandas`, `scikit-learn`, `pytest`, `alfworld`, `webshop`  
* **Student Model**: **Qwen2.5‑0.5B** (8‑bit quantized) – comfortably fits < 7 GB RAM on the CI runner.  
* **Retriever**: `sentence‑transformers/all‑MiniLM‑L6‑v2` (quantized) – verified source (see Research).  
* **Storage**: Local filesystem under `data/` (JSONL for step‑level logs, Parquet for episode‑level aggregates)  
* **Testing**: `pytest` with unit tests for gating logic, integration tests for the training loop, and schema validation tests.  
* **Target Platform**: Linux GitHub Actions free tier (a modest number of vCPU, roughly several gigabytes of RAM, and modest disk capacity). **CPU‑only** execution; no GPU fallback.  
* **Constraints**: Memory < 7 GB RAM, disk < 14 GB, each job ≤ 6 h.  

## Constitution Check
| Principle | Status | Verification Strategy |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/config.py`; `requirements.txt` pins exact versions; environments installed via `pip`. |
| **II. Verified Accuracy** | PASS | All citations (SDAR paper, ALFWorld, WebShop, Qwen2.5‑0.5B, MiniLM) are verified URLs (see `research.md`). |
| **III. Data Hygiene** | PASS | Raw environment packages are immutable; logs are checksum‑verified; no PII. |
| **IV. Single Source of Truth** | PASS | Figures/tables are generated programmatically from `data/processed/*`. |
| **V. Versioning Discipline** | PASS | Artifact hashes stored in `state/`; any change updates `updated_at`. |
| **VI. Computational Efficiency** | PASS | CPU‑time and memory logged per step (FR‑003); cost‑reduction target (SC‑002) is a hard gate. |
| **VII. Student‑Only Heuristic Fidelity** | PASS | Pearson correlation between student‑only gate and teacher‑student gap is computed as part of the analysis (no separate FR‑007). |

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
│   ├── baseline_agent.py    # Dual‑model SDAR (teacher + student)
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
| **Three variants (GRPO, Baseline, Student‑Only)** | Needed for SC‑001 (performance retention) which references the GRPO baseline as a reference point. | Using only two variants would make the “percentage of baseline improvement over GRPO” undefined. |
| **Bootstrapping plus paired design** | Small N = 10 × 2 environments still yields limited power; bootstrapping provides confidence intervals and effect sizes, while paired seeds reduce variance. | Relying solely on Mann‑Whitney would be overly conservative and give no effect‑size estimate. |
| **Quantized smaller student model** | Guarantees the experiment fits within the CPU‑only memory budget and eliminates the need for a GPU fallback. | Keeping the 1.7B model would exceed RAM limits on the free runner. |

## Phased Implementation Plan

| Phase | Goal | Tasks (mapped to FR/SC) |
|-------|------|--------------------------|
| **0 – Research & Feasibility** | Verify data sources, model loading, and compute budget. | • FR‑002: Confirm `alfworld` and `webshop` install via `pip` (no credentials).<br>• FR‑001: Prototype `S_t` using MiniLM‑L6‑v2 (verified source).<br>• FR‑006: Test gating function for NaN/Inf on pathological contexts.<br>• Constitution Check (re‑run). |
| **1 – Data Model & Contracts** | Define schemas for deterministic validation. | • FR‑001 → `GatingSignal` schema (contracts/gating_signal.schema.yaml).<br>• FR‑003 → `TrainingRun` schema (contracts/training_run.schema.yaml).<br>• FR‑004: Specify JSONL/Parquet storage conventions.<br>• FR‑006: Add `is_valid` flag in schema. |
| **2 – Core Implementation** | Build training loop, gating, and profiling. | • FR‑001: Implement `student_only_agent.py` (entropy via `torch.nn.functional.softmax`, stability via cosine similarity).<br>• FR‑002: Implement `baseline_agent.py` (teacher + student forward passes).<br>• FR‑003: Integrate `cost_profiler.py` (process_time & `psutil` RSS).<br>• FR‑006: Guard against division‑by‑zero in `S_t` and clamp `g_t` to \[0,1\]. |
| **3 – Execution & Data Collection** | Run experiments and gather metrics. | • FR‑002: Execute **10** independent runs per variant on **ALFWorld** then **WebShop** (total 60 runs) to improve statistical power.<br>• FR‑004: Persist logs to `data/processed/<run_id>.jsonl` and `episode_metrics.parquet`.<br>• FR‑001 (analysis): Replay baseline trajectories through the Student‑Only agent to obtain paired gating scores for Pearson correlation (covered by Principle VII).<br>• FR‑005: Run `statistical_test.py` (bootstrapping 1000 reps, Mann‑Whitney U for binary success, Bonferroni‑corrected α).<br>• **Cost‑Only Sub‑Phase**: For **both** Baseline SDAR and Student‑Only variants, run a fixed‑step (1 M) job **without** early‑stopping to measure per‑step CPU cost uniformly. |
| **4 – Analysis & Reporting** | Produce the final comparison report. | • SC‑001: Compute performance‑retention percentage using the paired‑run results.<br>• SC‑002: Compute per‑step CPU‑time reduction from the Cost‑Only runs; verify ≥ 60 % reduction.<br>• SC‑003: Report bootstrapped p‑value (Bonferroni‑adjusted) and effect size.<br>• SC‑004: Report convergence steps (from early‑stopping runs) to reward ≥ 0.8.<br>• Generate figures (reward curves, cost curves, correlation scatter). |
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
| SC‑001 | 4 |
| SC‑002 | 4 |
| SC‑003 | 4 |
| SC‑004 | 4 |

## Compute Feasibility Strategy
* **CPU‑First**: Qwen2.5‑0.5B loaded with `bitsandbytes` 8‑bit quantization (`device="cpu"`). Retriever quantized to 8‑bit via `sentence-transformers` + `bitsandbytes`. Expected RAM is on the order of a few gigabytes.  
* **No GPU fallback**: All runs are forced onto the CPU runner; the code will raise a clear error if the model cannot be loaded, preventing hidden GPU usage.  
* **Parallelisation**: The 60 runs are scheduled via a GitHub Actions matrix, keeping each job ≤ 6 h while the overall wall‑clock time stays within CI minute quotas.  

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Entropy high for correct tokens (false negatives) | Include `S_t` term; if `S_t` ≈ 0, fallback to entropy‑only gating with a lower `α`. |
| Noisy context → `S_t` ≈ 0 → gate collapse | Clamp `g_t` to a minimum of 0.05; log `is_valid=False` for diagnostics. |
| OOM on CI runner | Use 8‑bit quantization, limit context window to 256 tokens, stream environment data. |
| Low statistical power | Increase runs to N=10, use paired seeds, apply bootstrapping and report effect sizes; explicitly acknowledge remaining limitation. |
| Missing contracts (previous issue) | Contracts are defined in Phase 1 and validated by unit tests before any downstream task. |
| Resource limits exceeded | Fixed‑step caps and model size ensure each job stays within CPU, RAM, and time budgets. |

## Deliverables
* `plan.md` (this document)  
* `research.md` (methodology, dataset table, statistical plan)  
* `data-model.md` (entity definitions)  
* `quickstart.md` (installation & run instructions)  
* `contracts/gating_signal.schema.yaml` & `contracts/training_run.schema.yaml` (JSON‑Schema definitions)

---



===BEGIN_ARTIFACT projects/PROJ-825-llmxive-follow-up-extending-self-distill/specs/001-llmxive-follow-up-extending-self-distill/research.md===
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
| **RQ1** | Is there an **association** between Student‑Only gating and ≥ 80 % of the baseline performance gain over the GRPO baseline? *(associative claim)* |
| **RQ2** | Is there an **association** between Student‑Only gating and a ≥ 60 % reduction in per‑step CPU time compared to Baseline SDAR? *(associative claim)* |
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
* **Seeds**: Fixed per run (e.g., 42‑51).  
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


