# Research: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

## Overview
This document details the research-ready design, data strategy, model selection, statistical methodology, and compute plan required to answer the primary hypothesis:

> **H₁**: Injecting explicit, text-based social priors into MLLM prompts reduces the *Prejudice Rate* (PR) relative to the baseline prompting protocol.

A secondary hypothesis (**H₂**) asserts that a random-noise control does **not** reduce PR, confirming that any observed effect is due to meaningful context rather than prompt length.

## Dataset Strategy
| Dataset | Access Method | Verified URL | Notes |
|---------|---------------|--------------|-------|
| **`mmbench/ocean`** (HuggingFace, validation split) — **PRIMARY data source for all reported results** | `datasets.load_dataset("mmbench/ocean", split="validation")` | https://huggingface.co/datasets/mmbench/ocean | Open, directly downloadable; contains video references, transcripts, setting, culture, and behavior tags compatible with the required schema (a substantial set of videos). Used for the full study: power analysis, all three conditions, and all reported results. |
| **MM-OCEAN validation subset** | — | *No verified URL* | Not publicly downloadable. Demoted to a **future supplemental replication** if an official open mirror is released; no reported result depends on it. spec.md FR-001 still names it as primary — flagged for kickback. |

**Decision:** The entire study (all reported results) runs on the verified open `mmbench/ocean` dataset. The dataset-substitution note appears in `results.md`. This is the only honest executable design given MM-OCEAN's unavailability.

## Model Selection & Inference Strategy
- **Model pool:** The 27 models listed in Table 2 of arXiv:2605.22109 (e.g., LLaVA-1.5-7B, Mini-GPT-4-7B). All are open-source and loadable via `transformers`.
- **Quantisation:** 4-bit (`bitsandbytes`) on CPU; falls back to 8-bit if 4-bit fails. Keeps RAM ≤ 7 GB.
- **Batching:** Process videos in batches of 20 per model; streaming avoids loading full files into memory.
- **Runtime estimate:** ≈ 0.8 s per inference on a 7B quantised model → ~4 h total wall-clock for 27 × ~350–400 × 3 runs, under the 6 h limit.
- **GPU escape hatch:** Not required for the main pipeline. If a model cannot load on CPU, the inference module catches the `RuntimeError` and the platform automatically re-runs that model on a free Kaggle GPU (`device="cuda"`), processing a sampled subset of videos to stay within the free-GPU time budget.

## Prompt Templates (stored in `src/pipeline/prompts.py`)
- **Baseline:** `"You are shown a short video. Based on visual cues, rate the target's openness on a 1-5 scale. Provide a brief reasoning and a grounding score (0–1) derived from the video metadata."`
- **Context-Grounded:** `"Context: {context_profile}\n[Baseline prompt]"`
- **Random-Noise Control:** `"Context: {random_noise}\n[Baseline prompt]"` where `random_noise` is a 20-word gibberish string.

All prompts are deterministic and version-controlled.

## Metric Definitions (grounding assessed by **calibrated semantic similarity**; no external LLM judge)
| Metric | Formula | Required Fields |
|--------|---------|-----------------|
| **Prejudice Rate (PR)** — primary, per spec FR-018 | `#(correct rating ∧ grounding invalid) / #(correct rating)` | `rating_correct`, `grounding_valid` |
| **PR_all** — supplementary (selection-bias check) | `#(grounding invalid) / #(valid predictions)` | `grounding_valid` |
| **Holistic-Grounding Rate (HR)** | `#(correct rating ∧ grounding valid) / #(correct rating)` | same |
| **Integration-failure Rate (IR)** | `#(output does NOT cite any phrase from the injected context) / #samples with context-injection` | `context_cited` flag |

**PR denominator note (selection-bias concern):** The spec-mandated FR-018 denominator conditions on correct ratings, which can make PR unstable for low-accuracy models. Because spec.md is the single source of truth and FR-018 cannot be amended at this stage, the primary PR follows the spec definition; the pipeline **additionally** reports `PR_all` (invalid-grounding rate over all valid predictions) and per-model rating accuracy so readers can assess the selection effect, and the primary hypothesis test is run at the video level (below), which dilutes per-model accuracy instability. A spec amendment changing the FR-018 denominator is flagged for kickback.

**Grounding validity** is judged solely by semantic similarity: the model's reasoning string and the ground-truth behavioral evidence tags are embedded with the validated open `sentence-transformers/all-MiniLM-L6-v2` model (Reimers & Gurevych 2020); cosine similarity ≥ 0.70 counts as *valid grounding* (FR-020). The threshold is not arbitrary: it is **calibrated on a 30-sample pilot** against hand-labelled valid/invalid grounding decisions, requiring Cohen's κ ≥ 0.8 between the similarity-based decision and the labels; the SC-005 sweep over {0.65, 0.70, 0.75} reports how PR/HR and false-positive/false-negative rates vary. **No external LLM judge and no paid API is used anywhere** (the spec's gpt-4-turbo assumption is spec-rooted and flagged for kickback).

**Correct rating** is determined by exact match to the expert-annotated trait label provided in the metadata (FR-018).

Ambiguous samples (≥ 2 contradictory behavior tags) are flagged as *grounding-uncertainty* (FR-011) and excluded from primary PR/HR calculations.

## Statistical Methodology (covers SC-001, SC-002, SC-005, SC-010)

### Primary analysis: video-level mixed-effects model
The primary test is run at the **video level**, not the model level, so that statistical power is driven by the number of videos rather than the fixed 27 models. For each video *v*, we compute the per-video contribution to PR under each condition (aggregated across the model ensemble), giving paired video-level observations (PR_baseline(v), PR_context(v)). The primary model is a mixed-effects regression (`statsmodels` `MixedLM`) with random intercepts for video ID and model, testing the fixed effect of condition.

### Explicit power calculation (FR-019, SC-010)
- Video-level paired comparison: n = ~350–400 video pairs. For Cohen's d = 0.5, α = 0.05 (two-sided), `statsmodels.stats.power.TTestPower` gives power > 0.99.
- **Clustering adjustment:** per-video PR values are averages over 27 models, so video-level effects are not fully independent. Assuming a conservative intra-video ICC = 0.10 with cluster size 27, the design effect is DEFF = 1 + (27 − 1) × 0.10 = 3.6, reducing the effective sample size to ~350 / 3.6 ≈ 97 independent pairs. TTestPower for d = 0.5, α = 0.05, n = 97 still yields power ≈ 0.85 ≥ 0.80. **SC-010 is satisfied by the video-level primary analysis.**
- The a-priori analysis (with the target power recorded as `[deferred]` per FR-019 conventions, computed at design time from the above parameters) is attached to the final deliverable; observed power is recomputed post hoc.

### Secondary analysis: model-level paired test
Paired comparison of PR between baseline and context conditions across the 27 models: paired *t*-test if the distribution of differences is approximately normal, otherwise Wilcoxon signed-rank. **Power limitation acknowledged:** with n = 27 models and d = 0.5, power ≈ 0.65 < 0.80; this test is secondary and its power is reported alongside the result.

### Other components
- **Multiple-comparison correction:** Bonferroni across the three primary comparisons (baseline vs context, baseline vs noise, context vs noise).
- **Confidence intervals:** 95 % CI via bootstrapping (10 000 resamples).
- **Sensitivity analysis (SC-005):** sweep grounding-similarity threshold over {0.65, 0.70, 0.75}; recompute PR/HR and report false-positive/false-negative rates.
- **Quantisation-impact control (FR-021, SC-011):** run a representative subset of 5 models at 8-bit precision (and a tiny full-precision sample) for both baseline and intervention; report ΔPR (must be ≤ 5 %).

All statistical code resides in `src/pipeline/analysis.py`.

## Resource-Budget Monitoring (SC-003, FR-007)
- **Timer:** `time.perf_counter()` at start/end of each phase; aggregated in `data/derived/runtime_log.json`.
- **Memory:** `psutil.Process().memory_info().rss` sampled every 5 s; peak recorded.
- **Pre-inference projection (fallback bias eliminated):** Before any full inference, a **10-video pilot** measures per-model throughput and peak RAM. The orchestrator projects total runtime (27 × N_videos × 3 × measured seconds). If the projection exceeds 5.5 h or 6.5 GB, the **pre-registered fallback** (top-15 models chosen a priori + fixed 10-frame-per-video sampling) is applied **uniformly to all three conditions before any inference data is produced**. The projection, the decision, and the applied configuration are logged; no mid-experiment model dropping or data reduction ever occurs, so the between-condition comparison cannot be biased by the fallback.
- **Fallback trigger:** as above; the final results markdown includes a "Resource-Constraint Note" stating the applied configuration.

## Condition Order Randomisation (internal validity, SC-012)
For each model–video pair, the order of the three conditions (baseline, context, noise) is **randomly permuted** using a fixed random seed (`np.random.seed(42)`) to ensure reproducibility while counterbalancing potential order effects. Logs (`data/derived/randomisation_log.json`) record the exact order per pair.

## Validation & Contracts
Four JSON schemas in `contracts/` cover every artifact stage:
- `video_metadata.schema.yaml` — validated on dataset acquisition (Phase 0).
- `context_profile.schema.yaml` — validated on knowledge-base construction (Phase 1/2).
- `model_output.schema.yaml` — validated on every inference output (Phases 2–4).
- `metric_record.schema.yaml` — validated on metric computation (Phase 5/6).

Contract tests (`pytest -m contract`) enforce schema compliance at every stage boundary and guarantee that every figure/table traces back to a single row in the metric CSVs (Principle IV).

## Deliverables
- CSVs: `baseline_metrics.csv`, `context_metrics.csv`, `noise_metrics.csv` (each row schema-valid against `contracts/metric_record.schema.yaml`, including supplementary `PR_all` and `rating_accuracy` columns).
- Figures: PR reduction bar plot, IR histogram, sensitivity-analysis line chart.
- `results.md` summarising hypothesis-test outcomes, effect sizes, observed power, the dataset-substitution note (open `mmbench/ocean` as primary), and resource-budget status.