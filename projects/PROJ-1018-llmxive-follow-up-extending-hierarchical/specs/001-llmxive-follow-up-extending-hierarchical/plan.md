# Implementation Plan: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

**Branch**: `001-llmxive-static-distillation` | **Date**: 2026-10-26 | **Spec**: `specs/001-llmxive-static-distillation/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-static-distillation/spec.md`

## Summary
The project implements a **static distillation** of the dynamic Hierarchical Sparse (HiLS) attention mechanism:

1. **Dynamic Baseline Extraction** – run the pre‑trained HiLS model on a deterministic validation split of PG‑19, extract per‑chunk retrieval‑score matrices, and aggregate them into **canonical relevance profiles** (FR‑001).  
2. **Static Index Construction** – apply PCA → CPU‑optimized K‑Means clustering on the relevance profiles to produce a **static lookup table** (FR‑002).  
3. **Comparative Evaluation** – run inference with the static lookup on a disjoint test split, compute log‑perplexity, **optionally** long‑context QA accuracy (if a suitable dataset is supplied), latency, and memory; perform a paired statistical test and an equivalence test (FR‑003‑FR‑008).  

All steps are fully reproducible, use only open datasets, and respect the GitHub Actions free‑tier compute budget (CPU‑first, optional Kaggle GPU escape hatch for the HiLS checkpoint).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0` (CPU‑only), `transformers==4.44.0`, `datasets==2.20.0`, `scikit-learn==1.5.0`, `numpy`, `pandas`, `tqdm`, `tracemalloc` (stdlib)  
- **Storage**: `data/` hierarchy (raw, interim, processed, reports)  
- **Testing**: `pytest` + contract validation (see `contracts/`)  
- **Target Platform**: Linux CI runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)  
- **Constraints**: CPU‑first; only switch to a Kaggle GPU if the HiLS checkpoint refuses to run on CPU.  
- **Scale/Scope**: Process the full PG‑19 validation and test sets that satisfy a ≥ 32 k token length requirement; stream data to stay within RAM limits.

## Constitution Check
| Principle | Status | How satisfied |
|-----------|--------|----------------|
| I. Reproducibility | ✅ | Fixed seeds (`SEED=42`), deterministic splits, all scripts callable via CLI, `requirements.txt` pins versions. |
| II. Verified Accuracy | ✅ | Citations limited to the verified URLs listed in the spec; no invented references. |
| III. Data Hygiene | ✅ | Every derived artifact is written to a new file, SHA‑256 checksummed, and never mutates the raw source. |
| IV. Single Source of Truth | ✅ | All figures/tables in the eventual paper are read directly from the JSON reports produced by the pipeline. |
| V. Versioning Discipline | ✅ | `state/projects/PROJ-1018-...yaml` will be updated with content hashes of all artifacts. |
| VI. Distillation Fidelity | ✅ | Validation split (used for clustering) is disjoint from the test split (used for evaluation). |
| VII. Hardware‑Aware Latency | ✅ | Latency measured on the exact target hardware (2‑core CPU) with warm‑up runs; reduction factor recorded. |

## Functional Requirement Mapping
| FR # | Requirement | Plan Phase / Script |
|------|-------------|----------------------|
| FR‑001 | Extract retrieval score matrices for every chunk in the validation set and aggregate to relevance profiles | Phase 1: `src/extraction.py` (dynamic mode) → Phase 2: `src/aggregation.py` |
| FR‑002 | Build static lookup table via K‑Means clustering | Phase 3: `src/clustering.py` |
| FR‑003 | Modify inference to use static index instead of dynamic retrieval | Phase 4: `src/inference.py` (static mode) |
| FR‑004 | Compute perplexity on held‑out test set (dynamic & static) | Phase 5: `src/evaluation.py` |
| FR‑005 | Perform paired t‑test on per‑document perplexities (p < 0.05) | Phase 5: `src/evaluation.py` |
| FR‑006 | Measure inference latency reduction factor (a multi‑kilotoken input, 10 runs, Several warm‑ups) | Phase 5: `src/evaluation.py` |
| FR‑007 | **(Optional) Evaluate on a downstream long‑context QA task** | Phase 5: `src/evaluation.py` – executed only if a verified long‑context QA dataset is supplied; otherwise the `qa_accuracy` fields are recorded as `null`/`N/A`. |
| FR‑008 | Sensitivity sweep over K ∈ {50, 100, 200} and report trade‑offs | Phase 6: `src/sensitivity.py` + Phase 7: `src/report_sweep.py` |

## Success Criterion Mapping
| SC # | Metric | Produced By |
|------|--------|--------------|
| SC‑001 | Δlog PPL (static vs. dynamic) | `evaluation_report.json` |
| SC‑002 | Latency reduction factor | `evaluation_report.json` |
| SC‑003 | Paired test p‑value < 0.05 (or explicit “not significant”) | `evaluation_report.json` |
| SC‑004 | QA accuracy difference (if QA dataset provided) | `evaluation_report.json` |
| SC‑005 | Memory footprint of retrieval module (tracemalloc) | `evaluation_report.json` |
| SC‑006 | Trade‑off curves for K = 50/100/200 | `sweep_report.json` |

## Project Structure
```text
specs/001-llmxive-static-distillation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── evaluation_report.schema.yaml
│   ├── relevance_profile.schema.yaml
│   ├── static_index.schema.yaml
│   └── split_definition.schema.yaml
└── tasks.md            # generated later by /speckit-tasks

projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/
├── src/
│   ├── __init__.py
│   ├── config.py                # seeds, paths, flags
│   ├── data_loader.py           # deterministic split creation, streaming PG‑19
│   ├── extraction.py            # dynamic HiLS inference, writes .pt tensors
│   ├── aggregation.py           # builds RelevanceProfile JSON
│   ├── clustering.py            # PCA + K‑Means, writes StaticIndex JSON
│   ├── inference.py             # static‑HiLS inference wrapper
│   ├── evaluation.py            # perplexity, QA, latency, memory, stats
│   ├── sensitivity.py           # K‑sweep driver
│   ├── report_sweep.py          # aggregates sweep results
│   └── logging_utils.py         # llmxive_toolkit.get_logger wrapper
├── tests/
│   ├── test_extraction.py
│   ├── test_aggregation.py
│   ├── test_clustering.py
│   ├── test_inference.py
│   └── test_evaluation.py
├── data/
│   ├── raw/                     # streamed PG‑19 (no local copy)
│   ├── interim/
│   │   ├── filtered_pg19.json          # validation & test IDs, conforms to SplitDefinition
│   │   └── relevance_profiles.json
│   └── processed/
│       ├── static_index_k50.json
│       ├── static_index_k100.json
│       └── static_index_k200.json
│   └── reports/
│       ├── evaluation_report.json
│       └── sweep_report.json
├── requirements.txt
└── run_pipeline.sh
```

## Detailed Phase Breakdown
| Phase | Script(s) | Key Inputs | Key Outputs | Notes |
|-------|-----------|------------|-------------|-------|
| **0. Data Loading & Splitting** | `src/data_loader.py` | PG‑19 via `datasets.load_dataset(..., streaming=True)` | `data/interim/filtered_pg19.json` (validation & test ID lists, SHA‑256 checksum) | Documents < 32 k tokens are **skipped** (`PAD_SHORT_DOCS=False`). Deterministic split: shuffle with `SEED=42`, then assign first [deferred] to validation, next [deferred] to test. |
| **1. Dynamic Baseline Extraction** | `src/extraction.py` (`--mode dynamic`) | Validation IDs, HiLS checkpoint (`llmxive/hils-base`) | `data/interim/raw_scores/<doc_id>.pt` (torch tensor of shape `N_chunks × N_tokens`) | Runs on CPU; if `torch.cuda.is_available()` raises, automatically loads the checkpoint with `load_in_8bit=True` on a Kaggle GPU (real off‑load). |
| **2. Relevance Profile Aggregation** | `src/aggregation.py` | All `.pt` files from Phase 1 | `data/interim/relevance_profiles.json` (list of RelevanceProfile objects, each with `checksum`) | Checks for NaN/Inf, logs any empty chunks. |
| **3. Static Index Construction** | `src/clustering.py` | Relevance profiles JSON | `data/processed/static_index_k{K}.json` (StaticIndex, one per K) | **PCA** – reduce to 64 components (captures > 95 % variance). **K‑Means** – CPU‑optimized `sklearn.cluster.KMeans` with cosine distance, `n_init=10`, `max_iter=300`. **Convergence Safeguard** – up to three random seeds; empty‑cluster detection triggers a retry. Failure after three attempts aborts with a clear error message. |
| **4. Static‑HiLS Inference** | `src/inference.py` (`--mode static`) | Test IDs, chosen StaticIndex | Temporary logits (kept in memory, not persisted) | Identical tokenization to dynamic baseline; uses cluster centroids to select attention patterns. |
| **5. Evaluation & Statistics** | `src/evaluation.py` | Dynamic logits, static logits, long‑context QA dataset (if provided) | `data/reports/evaluation_report.json` (conforms to EvaluationReport schema) | Computes log‑perplexity, **optionally** QA exact‑match (if a verified QA dataset is supplied), latency (10 runs, 2 warm‑ups), memory via `tracemalloc`. Performs **normality check** (Shapiro‑Wilk). If normal (p ≥ 0.05) → paired t‑test; else → Wilcoxon signed‑rank test. Records method, p‑value, confidence interval. Also conducts **Equivalence Test (TOST)** with Δlog PPL < 0.1 and power analysis. Applies Bonferroni correction to the four secondary metrics (QA accuracy, latency, memory, latency‑reduction factor). Stores raw and corrected p‑values, effect sizes, and power warnings. |
| **6. Sensitivity Sweep** | `src/sensitivity.py` → `src/report_sweep.py` | Relevance profiles, list of K values | `data/reports/sweep_report.json` (aggregated metrics for K = 50, 100, 200) | Re‑runs Phases 3‑5 for each K, aggregates Δlog PPL, ΔQA (or `null`), latency, and memory. |
| **7. Final Reporting** | `src/report_sweep.py` | Sweep JSON | Human‑readable CSV/JSON for paper tables | No manual transcription; single source of truth. |

## Statistical Rigor Enhancements
1. **Normality Check** – Shapiro‑Wilk test on per‑document log‑perplexity differences; if p ≥ 0.05, use paired t‑test, otherwise Wilcoxon signed‑rank test. The chosen method and its parameters are recorded in `evaluation_report.json.statistical_test.method`.  
2. **Equivalence Test** – Two‑One‑Sided‑Tests (TOST) with equivalence margin Δlog PPL < 0.1 (practically negligible degradation). Power analysis ensures ≥ 80 % power to detect this margin given the sample size; if power is insufficient, the report flags the limitation.  
3. **Multiple‑Comparison Correction** – Bonferroni correction (α / 4) applied to the four secondary metrics (QA accuracy, latency, memory, latency‑reduction factor). Both raw and corrected p‑values are saved.  
4. **Effect‑Size Reporting** – Cohen’s d (or r for Wilcoxon) and TOST‑specific effect size are stored alongside p‑values.  
5. **Power Analyses** –  
   - **Perplexity** – Detecting a large effect (Cohen’s d = 0.8) requires N ≈ 30 documents (expected to be satisfied).  
   - **QA Accuracy** – Medium effect (Cohen’s h = 0.5) requires N ≈ 45; if fewer, the report flags reduced power.  
   - **Memory** – Medium effect (d = 0.5) requires N ≈ 40; similarly flagged if insufficient.  

## Compute Feasibility
- All CPU‑bound steps stay below 7 GB RAM limit by streaming PG‑19 and processing in small batches.  
- K‑Means on ≤ 10 k profiles (after PCA) fits comfortably in memory.  
- The HiLS checkpoint is CPU‑compatible; if a CUDA‑only build is encountered, the pipeline automatically switches to an 8‑bit quantized variant or off‑loads to a Kaggle GPU (real GPU, not a fabricated stub).  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient long documents | Validation/test sets may be too small for statistical power. | Skip short docs, log counts, abort with power‑warning if < 30 docs remain. |
| HiLS checkpoint requires CUDA | CPU run fails. | Use 8‑bit quantization or Kaggle GPU escape hatch; both are real computations. |
| OOM during aggregation | CI runner crashes. | Stream documents, write partial aggregates to disk, load in chunks. |
| K‑Means empty clusters | Convergence failure. | Retry up to 3 seeds; fallback to lower K if still failing. |
| Power shortage for QA/memory | Inconclusive secondary tests. | Report detectable effect size limits; include power analysis in the final report. |
| High dimensionality hurting clustering | Poor centroids. | Mandatory PCA to 64 components before clustering. |

## Success Criteria Alignment
- **SC‑001** – Δlog PPL computed and stored in `evaluation_report.json`.  
- **SC‑002** – Latency reduction factor (`latency_dynamic / latency_static`) stored in `evaluation_report.json`.  
- **SC‑003** – Paired test p‑value (< 0.05) or explicit “not significant” flag recorded in `evaluation_report.json`.  
- **SC‑004** – QA accuracy difference stored in `evaluation_report.json` **if** a verified QA dataset is supplied; otherwise the field is `null` and the metric is marked “N/A”.  
- **SC‑005** – Retrieval‑module memory usage (bytes) stored in `evaluation_report.json`.  
- **SC‑006** – Sweep report (`sweep_report.json`) contains trade‑offs for K = 50, 100, 200.  

---

