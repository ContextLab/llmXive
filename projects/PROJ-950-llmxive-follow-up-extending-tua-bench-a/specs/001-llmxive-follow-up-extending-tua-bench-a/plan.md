# Implementation Plan: llmXive follow-up: extending "TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents"

**Branch**: `001-llmxive-procedural-memory` | **Date**: 2026-10-20 | **Spec**: [spec.md](../specs/001-llmxive-procedural-memory/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-procedural-memory/spec.md`

## Summary
The project must (1) run a baseline Llama large‑parameter agent on 24 scientific workflow tasks, (2) run the same agent augmented with a retrieval‑augmented “Procedural Memory Bank” (50 verified command sequences) under configurable top‑k values (k = 1, 3, 5), (3) record detailed binary outcomes and failure modes, (4) compute false‑positive retrieval rates, and (5) perform a statistically rigorous comparison (McNemar’s exact test with Holm‑Bonferroni correction). All steps must be reproducible on a GitHub Actions free‑tier runner using **CPU‑only** execution for the LLM (4‑bit quantization) and respect the 6‑hour batch timeout.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers==4.44.0`, `bitsandbytes==0.43.1`, `sentence-transformers==3.0.1`, `datasets==2.21.0`, `scipy==1.14.0`, `pandas==2.2.2`, `numpy==2.1.0`, `tqdm==4.66.5`, `jsonschema==4.23.0`  
**Storage**: Files under `data/` (TUA‑Bench tasks, procedural memory bank, result JSONs)  
**Testing**: `pytest` (contract validation)  
**Target Platform**: Linux (GitHub Actions runner) – **CPU‑only** (model quantized to 4‑bit)  
**Constraints**: Per‑task timeout 15 min, per‑batch timeout 6 h, deterministic seeds, no external data beyond verified URLs.  

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | All scripts are deterministic; seeds are pinned; data is fetched programmatically from verified sources. |
| II. Verified Accuracy | No new citations introduced. |
| III. Data Hygiene | All data files are checksummed; transformations produce new files. |
| IV. Single Source of Truth | Every figure/table traces back to a single row in `data/` and a single line in `code/`. |
| V. Versioning Discipline | Artifacts are content‑hashed; `state/projects/...yaml` updated automatically. |
| VI. Deterministic Execution‑Only Evaluation | Success defined solely by deterministic TUA‑Bench validation scripts. |
| VII. Procedural Memory Bank Integrity | Memory bank consists of 50 hand‑curated command strings; no model‑generated entries. |

## Project Structure
```text
specs/001-llmxive-procedural-memory/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── execution_result.schema.yaml
├── data/
│   ├── synthetic_tasks.json            # generated from official TUA‑Bench
│   ├── memory_bank.json                # 50 verified command sequences
│   ├── relevance_map.json              # ground‑truth relevance mapping
│   ├── baseline_results/              # per‑seed JSONs + aggregated file
│   └── augmented_results/              # per‑seed JSONs per k + aggregated files
└── code/
    ├── run_baseline.py
    ├── run_augmented.py
    ├── retrieval.py
    ├── stats.py
    ├── utils.py
    └── generate_synthetic_tasks.py
```

## Phase 0 – Data Preparation (addresses FR‑001, FR‑003, FR‑010)
| Step | Description | FR/SC | Output |
|------|-------------|-------|--------|
| 0.1 | **Download the official TUA‑Bench dataset** via `datasets.load_dataset("tua_bench")`. Verify that it contains at least 24 tasks with the required fields (`description`, `validation_script`, `task_type`). Randomly select a comparable set of complex and routine tasks, preserving their original IDs.. | FR‑001 | `data/synthetic_tasks.json` (selected subset) |
| 0.2 | Create the **Procedural Memory Bank** (`data/memory_bank.json`) with 50 hand‑written shell command entries, each with a human‑written description and pre‑computed sentence‑embedding (via `sentence-transformers/all-MiniLM-L6-v2`). | FR‑003, FR‑010 | `data/memory_bank.json` |
| 0.3 | **Ground‑truth relevance mapping**: two independent annotators label which memory entries are relevant to each task. Compute Cohen’s κ; resolve any disagreements. Store mapping in `data/relevance_map.json`. | FR‑010 | `data/relevance_map.json` |

## Phase 1 – Baseline Execution (addresses FR‑001, FR‑002, FR‑005, FR‑008, FR‑009, SC‑004)
| Step | Description | FR/SC | Output |
|------|-------------|-------|--------|
| 1.1 | Load Llama 3.1 8B **on CPU** using 4‑bit quantization (`bitsandbytes` CPU mode). Set deterministic seed. | FR‑002 | Model loaded on CPU |
| 1.2 | For each of the 5 seeds, **randomize the order** of task execution to avoid systematic warm‑up effects. Run the baseline agent on all 24 tasks with only in‑context prompting. Enforce a 15‑min per‑task timeout and a 6‑h per‑batch timeout. Record wall‑clock time for the whole batch. | FR‑001, FR‑002, FR‑008, FR‑009, SC‑004 | `baseline_results/seed_{i}.json` |
| 1.3 | Record binary success/fail, error type, and execution time for each task. | FR‑005 | Structured JSON entries |
| 1.4 | Aggregate across seeds to produce `baseline_results/aggregated.json` containing overall success rate, failure‑mode breakdown, and total batch runtime (checked against SC‑004). | FR‑005, SC‑004 | `baseline_results/aggregated.json` |

## Phase 2 – Retrieval‑Augmented Execution (addresses FR‑004, FR‑006, FR‑007, FR‑008, FR‑009, FR‑011, FR‑012, SC‑004)
| Step | Description | FR/SC | Output |
|------|-------------|-------|--------|
| 2.1 | Implement retrieval (`retrieval.py`) that encodes the task description, computes cosine similarity against memory embeddings, and returns top‑k entries (configurable). | FR‑004 | Retrieval function |
| 2.2 | For each top‑k setting (k = 1, 3, 5) and each of the 5 seeds, **randomize the execution order** (baseline vs. augmented) per seed. Run the augmented agent on all 24 tasks, appending retrieved entries to the prompt. Log “retrieval miss” when no hits and “false positive retrieval” when any retrieved entry is not in the relevance map. Enforce the same timeouts and record batch runtime. | FR‑004, FR‑010, FR‑012, FR‑009, SC‑004 | `augmented_results/k_{k}/seed_{i}.json` |
| 2.3 | Record per‑task success/fail, retrieval metadata (retrieved IDs, relevance flag), and error type. | FR‑005, FR‑011 | Structured JSON |
| 2.4 | Aggregate per‑k across seeds to produce `augmented_results/k_{k}/aggregated.json` with success rate, false‑positive retrieval rate, retrieval‑miss rate, and total batch runtime. | FR‑011, SC‑004 | Aggregated JSON |

## Phase 3 – Statistical Analysis (addresses FR‑006, FR‑007, SC‑001, SC‑003, SC‑005, SC‑002)
| Step | Description | FR/SC | Output |
|------|-------------|-------|--------|
| 3.1 | Load baseline and augmented aggregated JSONs. Build **per‑task majority‑vote outcomes** across the five seeds (success if ≥3 seeds succeeded). Construct paired binary tables (baseline vs. augmented) at the task level. | FR‑006 | In‑memory tables |
| 3.2 | Perform **McNemar’s exact test** on the paired majority‑vote outcomes for the primary k = 3 condition. Report test statistic and p‑value. | FR‑006, SC‑001 | `stats/mcnemar_k3.json` |
| 3.3 | Conduct an **exploratory Wilcoxon signed‑rank test** on the paired binary outcomes (treated as 0/1). Clearly label it exploratory and note its limitations for binary data. | FR‑006 | `stats/wilcoxon_k3.json` |
| 3.4 | Apply **Holm‑Bonferroni correction** across the three k‑conditions (k = 1, 3, 5) for the primary McNemar tests. | FR‑007, SC‑005 | `stats/holm_corrected.json` |
| 3.5 | Compute **task‑type specific gains**: (augmented success – baseline success) for complex and routine subsets. Compare gains to the (deferred) thresholds of SC‑002 and report them. | SC‑002 | `stats/gain_complex.json`, `stats/gain_routine.json` |
| 3.6 | Verify **false‑positive retrieval rate** (< 20 %) using the aggregated data; report in `stats/false_positive.json`. | SC‑003 | `stats/false_positive.json` |
| 3.7 | Summarize all statistics, p‑values, effect sizes, and compliance statements in `results/summary.md`. | SC‑001‑SC‑005 | `results/summary.md` |

## Phase 4 – Reporting & Artifact Generation (covers all SC)
| Step | Description | SC | Output |
|------|-------------|----|--------|
| 4.1 | Generate figures (bar plots of success rates, false‑positive rate, p‑value heatmap) using `matplotlib` (CPU‑friendly). | SC‑001, SC‑003, SC‑005 | `figures/*.png` |
| 4.2 | Assemble a **JSON manifest** (`data/manifest.json`) listing checksums of all data and result files for reproducibility. | I. Reproducibility | `data/manifest.json` |
| 4.3 | Validate all result files against the contract schema (`contracts/execution_result.schema.yaml`) via `jsonschema`. | I. Reproducibility | CI test pass |

## Phase 5 – Clean‑up & Handoff
| Step | Description | SC |
|------|-------------|----|
| 5.1 | Commit all generated artifacts, update `state/projects/PROJ-950-...yaml` with new `artifact_hashes` and `updated_at`. | V. Versioning Discipline |
| 5.2 | Provide hand‑off notes for the downstream paper pipeline (paths to figures, tables, and summary). | VI. Deterministic Execution‑Only Evaluation |

## Mapping of Functional & Success Criteria to Phases
| ID | Requirement | Phase(s) |
|----|-------------|----------|
| FR‑001 | Load 24 tasks | Phase 0 (official TUA‑Bench download) |
| FR‑002 | CPU‑only per‑task timeout, batch timeout | Phase 1 & 2 (enforced) |
| FR‑003 | Build Procedural Memory Bank (50 entries) | Phase 0 |
| FR‑004 | Retrieval & context augmentation | Phase 2 |
| FR‑005 | Record binary outcomes & failure modes | Phase 1 & 2 |
| FR‑006 | McNemar’s exact test + Wilcoxon (exploratory) | Phase 3 |
| FR‑007 | Holm‑Bonferroni across k‑sweep | Phase 3 |
| FR‑008 | Five seeds per condition | Phase 1 & 2 |
| FR‑009 | Graceful batch termination on 6 h limit | Phase 1 & 2 |
| FR‑010 | Ground‑truth relevance mapping | Phase 0 |
| FR‑011 | Record false‑positive retrieval rate | Phase 2 & 3 |
| FR‑012 | Configurable top‑k (k = 1, 3, 5) | Phase 2 |
| SC‑001 | Significance p < 0.05 | Phase 3 |
| SC‑002 | Complex task gain ≥ [deferred]; routine gain ≤ [deferred] | Phase 3 (Step 3.5) |
| SC‑003 | False‑positive rate < 20 % | Phase 3 (Step 3.6) |
| SC‑004 | Batch compute ≤ 6 h, overall ≤ 30 h | Phase 1, 2, 3 (timing checks) |
| SC‑005 | Sensitivity to k (variance reporting) + Holm‑Bonferroni | Phase 3 (Step 3.4) |
