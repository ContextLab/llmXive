# Implementation Plan: llmXive Follow-up: Dynamic Socio-Cognitive State Injection

**Branch**: `001-dynamic-state-injection` | **Date**: 2026-10-12 | **Spec**: `specs/001-dynamic-state-injection/spec.md`  
**Input**: Feature specification from `/specs/001-dynamic-state-injection/spec.md`

## Summary
Implement a CPU‑only research pipeline that (1) generates synthetic conflict trajectories with targeted oversampling of high‑emotional‑reactivity and culturally diverse scenarios, (2) splits the generated set into a classifier‑training subset and an experiment subset, (3) trains a lightweight logistic‑regression classifier on the training subset, (4) injects dynamic style instructions derived from those states into LLM system prompts (adapter condition) while keeping a static baseline, (5) runs eight quantized LLMs on the experiment trajectories under both conditions with **randomized/counterbalanced condition order per trajectory**, (6) evaluates each output with the “consensus gap closure” metric, and (7) performs paired statistical testing (t‑test or Wilcoxon) with Holm‑Bonferroni correction across models. All steps are reproducible, data‑hygienic, and respect the Constitution, especially Principle VII (dynamic‑state injection isolation).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets`, `scikit-learn`, `transformers` (CPU‑only, 8‑bit quantization), `sentence-transformers`, `pandas`, `numpy`, `scipy`, `statsmodels`, `pyyaml`  
- **Storage**: Local file system (JSONL / Parquet) under `data/`  
- **Testing**: `pytest` (unit, integration, contract validation)  
- **Target Platform**: Linux GitHub Actions free tier (2 vCPU, ≈7 GB RAM, ≈few GB disk)  
- **Performance Goals**: ≤45 s per trajectory inference; ≥40 trajectories / hour per model on CPU (average on the order of tens of seconds observed).  
- **Constraints**: No CUDA / GPU libraries; all models quantized to fit ≤7 GB RAM; strict checksum logging; reproducible random seeds.  

## Constitution Check
| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | ✅ | Random seeds pinned; `requirements.txt` provided; data fetched from canonical URLs. |
| II. Verified Accuracy | ✅ | All citations to SoCRATES and open‑source libraries verified. |
| III. Data Hygiene | ✅ | Checksums recorded; no in‑place mutation; PII scan enforced. |
| IV. Single Source of Truth | ✅ | Every statistic traces to a row in `data/results/` and a script in `code/`. |
| V. Versioning Discipline | ✅ | Content hashes stored in `state/...yaml`. |
| VI. Low‑Resource Feasibility | ✅ | Logistic regression, 8‑bit quantized LLMs, and MiniLM run on CPU only. |
| VII. Dynamic State Injection Isolation | ✅ | Adapter and static conditions use identical trajectories and LLMs; **all adapter runs, including neutral‑monitoring, are included in the primary paired analysis**. |

## Project Structure
```
specs/001-dynamic-state-injection/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── experiment.schema.yaml
│   ├── experiment_log.schema.yaml
│   └── report.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```
projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/
├─ src/
│  ├─ data/
│  │  ├─ generate_trajectories.py      # SoCRATES wrapper + oversampling
│  │  ├─ split_dataset.py              # **T018**: train/experiment split
│  │  ├─ classifier_training.py        # LR training & feature extraction
│  │  └─ classifier_output.jsonl       # T019 output
│  ├─ models/
│  │  ├─ state_classifier.py           # inference wrapper
│  │  └─ evaluator.py                  # consensus‑gap metric
│  ├─ experiments/
│  │  ├─ runner.py                     # **T027** CPU‑only inference loop with randomized condition order
│  │  └─ prompts.py                    # static & dynamic templates
│  └─ analysis/
│     ├─ stats_utils.py                # normality, tests, correction
│     └─ report_generator.py           # final JSON report
├─ tests/
│  ├─ unit/
│  │  ├─ test_classifier.py
│  │  ├─ test_evaluator.py
│  │  └─ test_data_flow.py            # **T046** generic unit‑test suite (covers former T043a/b)
│  ├─ integration/
│  │  └─ test_full_pipeline.py
│  └─ contract/
│     └─ test_schemas.py
├─ data/
│  ├─ raw/
│  ├─ processed/
│  │  ├─ filtered_trajectories.jsonl   # experiment set (A substantial proportion of high‑difficulty.)
│  │  ├─ classifier_training_set.jsonl # training set for classifier
│  │  └─ generation_stats.json         # **T013** generation statistics
│  └─ results/
└─ requirements.txt
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Dual condition (Adapter vs. Static) | Required by FR‑003, FR‑007, and Constitution VII. | Single condition would not isolate the dynamic injection effect. |
| Holm‑Bonferroni correction | Required by FR‑007 to control family‑wise error across 8 LLMs. | No correction would inflate Type I error. |
| CPU‑only execution | Required by Constitution VI and Assumption 2. | GPU would exceed CI limits and break low‑resource goal. |
| Randomized condition order | Needed to avoid order effects (methodology‑82dc3c25). | Fixed order would confound the paired design. |
| Train/experiment split | Prevents data‑leakage (scientific_soundness‑b2402598). | Using the same trajectories for training and testing would bias results. |
| Reduced trajectory count | Ensures wall‑clock ≤6 h on free CI (data_resources‑dad99afd). | Full 500‑trajectory run would exceed the budget. |

## Mapping of Functional & Success Criteria to Plan Elements
| ID | Requirement | Plan Phase / Task |
|----|-------------|-------------------|
| FR‑001 | ≥40 % oversampling of high‑emotion or diverse‑culture trajectories | Phase 0 – T014/T015 (generation & oversampling verification) |
| FR‑002 | Logistic‑regression state classifier trained on dialogue text only | Phase 0 – T018 (split) → T019/T020 (training) |
| FR‑003 | Dynamic injection of state‑derived instructions | Phase 1 – T045a/T045b (prompt logic) → T027 (runner) |
| FR‑004 | CPU‑only inference for 8 LLMs, no CUDA/bitsandbytes | Phase 1 – T027 (full inference loop) |
| FR‑005 | Consensus‑gap metric independent of state labels | Phase 1 – T033/T033b (evaluator & independence audit) |
| FR‑006 | Normality check → paired t‑test or Wilcoxon | Phase 2 – T038a‑T038c (statistical workflow) |
| FR‑007 | Multiple‑comparison correction across LLMs | Phase 2 – T038c (Holm‑Bonferroni) |
| SC‑001 | Paired significance testing | T038c/T038d |
| SC‑002 | Verify dataset‑variable fit | T014/T015 (generation stats) |
| SC‑003 | Inference ≤45 s, ≥40 traj/hr | T051 (throughput measurement) |
| SC‑004 | Family‑wise error correction applied | T038c |
| SC‑005 | Sensitivity sweep of classifier confidence | T050 (added) |

## Detailed Task List (including revised and new tasks)

### Phase 0 – Data & Feasibility
| Task | Description | Dependencies | Deliverable |
|------|-------------|--------------|-------------|
| **T014** | Generate conflict trajectories using SoCRATES prompts; apply oversampling flags. | – | `data/processed/filtered_trajectories.jsonl` |
| **T015** | Verify oversampling: compute % of high‑emotion or diverse‑culture samples; fail if < 40 %. | T014 | `data/results/oversampling_report.json` |
| **T013** | **NEW** Write generation statistics (total trajectories, high‑emotion count, oversampling ratio). | T014 | `data/processed/generation_stats.json` |
| **T018** | **NEW** Randomly split the generated trajectories into (i) `classifier_training_set.jsonl` ([deferred] of data) for LR training and (ii) `filtered_trajectories.jsonl` ([deferred]) for the mediation experiments. Ensure no overlap. | T014 | `data/processed/classifier_training_set.jsonl` |
| **T019** | Extract sliding‑window (last N turns) text features → training rows for classifier (uses only the training split). | T018 | `data/processed/classifier_training_data.json` |
| **T020** | Train scikit‑learn LogisticRegression on TF‑IDF of extracted windows; persist model. | T019 | `models/state_classifier.pkl` |
| **T020b** | **NEW** Audit feature independence: ensure that none of the TF‑IDF tokens encode `emotional_reactivity` or `cultural_identity`. | T020 | `data/results/feature_independence_audit.json` |

### Phase 1 – Implementation
| Task | Description | Dependencies | Deliverable |
|------|-------------|--------------|-------------|
| **T033** | Implement consensus‑gap evaluator using `sentence‑transformers` (MiniLM). | – | `src/models/evaluator.py` |
| **T033b** | Verify evaluator does not reference state labels (independence audit). | T033 | `data/results/evaluator_independence_audit.json` |
| **T045a** | Refactor `runner.py` to share prompt‑building logic between conditions. | – | Updated `src/experiments/runner.py` |
| **T045b** | Add unit test for refactored split logic. | T045a | `tests/unit/test_data_flow.py` |
| **T046** | **NEW** Generic unit‑test suite covering classifier, evaluator, and data‑flow (consolidates former T043a/T043b). | – | `tests/unit/test_classifier.py`, `tests/unit/test_evaluator.py`, `tests/unit/test_data_flow.py` |
| **T027** | **NEW** Full CPU‑only inference loop: (i) load quantized GGUF model with `device="cpu"`; (ii) enforce no bitsandbytes/CUDA imports; (iii) for each trajectory **randomly shuffle** the order of the two conditions (Adapter, Static) to avoid order effects; (iv) run classifier; (v) if confidence < threshold, inject neutral‑monitoring instruction; (vi) log `run_id`, `model_name`, `condition`, `injected_state`, `llm_output`, `consensus_gap_score`, `status`; (vii) write/append `data/results/scope_adjustments.json` summarizing any skipped/timeout trajectories. | T020, T033, T018 | `data/results/experiment_logs/.../*.jsonl`, `data/results/scope_adjustments.json` |

### Phase 2 – Execution & Analysis
| Task | Description | Dependencies | Deliverable |
|------|-------------|--------------|-------------|
| **T028** | Run full experiment (Adapter + Static) for all 8 LLMs on the **experiment** trajectories; respect CPU‑only constraints; retry on timeout (exponential back‑off). | T027 | `data/results/experiment_logs/` |
| **T038a** | Ingest all experiment logs; assemble paired dataset per trajectory & model. | T028 | In‑memory DataFrame |
| **T038b** | Perform Shapiro‑Wilk normality test on Adapter‑Static difference scores; record p‑value. | T038a | `normality_p_value` in report |
| **T038c** | If normal (p > 0.05) → paired t‑test on **logit‑transformed** gap scores; else → Wilcoxon signed‑rank test. Apply Holm‑Bonferroni across the 8 models. **Include all adapter runs**, even those with neutral‑monitoring. Generate `data/results/statistical_report.json`. | T038b | `data/results/statistical_report.json` |
| **T038d** | Generate human‑readable JSON/Markdown summary. | T038c | `data/results/statistical_report.json` |
| **T050** | **NEW** Sensitivity sweep: vary classifier confidence threshold (0.5‑0.9); recompute effect size & significance for high‑confidence subset; store in `threshold_sensitivity_report.json`. | T038c | `data/results/threshold_sensitivity_report.json` |
| **T051** | **NEW** Measure per‑model inference time & throughput; write `throughput_report.json`. | T028 | `data/results/throughput_report.json` |

### Phase 3 – Validation
| Task | Description |
|------|-------------|
| **T044** (removed) | — |
| **T045** (implicit) | End‑to‑end quickstart validation is covered by the integration test `tests/integration/test_full_pipeline.py`. |

## Neutral‑Monitoring Inclusion Policy
The spec’s edge‑case description states that when the classifier lacks confidence the system must fall back to a neutral “monitoring” instruction rather than discarding the run. Consequently **all adapter runs, including neutral‑monitoring, are retained in the primary paired comparison** (T038c). A **post‑hoc sensitivity analysis** (T050) isolates high‑confidence injections to explore potential dilution effects, but it does not alter the main hypothesis test.

## Compute Feasibility Rationale
All heavy computation (LLM inference, sentence‑transformer embeddings) uses 8‑bit GGUF models (≈ 2 GB RAM each) and MiniLM (≈ 80 MB). We will process **A sufficient number of trajectories.** (≈ a substantial number of inference calls per condition). Assuming an average inference time of **~20 s** per call, the total wall‑clock time on a Multi‑CPU runner (≈ several parallel threads) is:

```
1,200 calls × 20 s ÷ 2 ≈ several hours ≈ 3.3 h
```

well within the Multi‑hour CI limit. No GPU is required; the pipeline would off‑load to a Kaggle GPU only if a future extension needed a larger model, but the current design **does not** require it.

---

