# Implementation Plan: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-20 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project quantifies the *Prejudice Gap* for the 27 Multimodal Large Language Models (MLLMs) listed in Table 2 of arXiv:2605.22109 on a video personality-perception dataset, then evaluates whether injecting a static JSON knowledge base of social priors (Context-Grounded Chain-of-Thought) reduces that gap. The pipeline consists of:

1. **Data acquisition** – download/verify the open HuggingFace dataset `mmbench/ocean` (validation split, ~350–400 videos; the verified open substitute for MM-OCEAN, which has no verified public URL). All reported results use this dataset; MM-OCEAN is a future supplemental replication only.
2. **Knowledge-base construction** – static JSON of social priors, validated against `contracts/context_profile.schema.yaml`.
3. **Baseline prompting** – standard prompt on every model–video pair; outputs validated against `contracts/model_output.schema.yaml`.
4. **Context-Grounded prompting** – retrieve relevant context profile, inject into prompt.
5. **Random-noise control** – inject gibberish instead of context.
6. **Metric computation** – compute Prejudice Rate (PR), Holistic-Grounding Rate (HR), Integration-failure Rate (IR) per model & condition, handling invalid/uncertain samples. Grounding validity is assessed by **calibrated semantic similarity** (sentence-embedding cosine ≥ 0.70, threshold swept in sensitivity analysis). No external LLM judge is used (no paid APIs).
7. **Statistical analysis** – **video-level primary test** (mixed-effects model with video and model as random effects; explicit power calculation, see Phase 6), model-level paired t-test/Wilcoxon as secondary, Bonferroni correction, sensitivity sweep over grounding thresholds, and quantisation-impact control (FR-021).
8. **Quantisation-impact control** – run a representative subset of 5 models at 8-bit (and a tiny full-precision sample) to verify quantisation does not bias baseline vs. context differences.
9. **Resource monitoring & predefined fallback** – a 10-video pilot measures per-model throughput; a PRE-INFERENCE projection decides whether the pre-registered fallback (top-15 models + 10-frame-per-video sampling) is applied uniformly to all conditions before any inference data is produced. No mid-experiment changes.
10. **Condition order randomisation** – per model–video pair, the order of the three conditions (baseline, context, noise) is randomly permuted using a fixed seed (`np.random.seed(42)`).
11. **Reporting** – generate CSV/JSON tables, figures, and `results.md`. All steps live under `src/pipeline/` and are orchestrated by `python -m src.pipeline.run_all`. The order respects data dependencies (download → knowledge base → inference → metrics → analysis → reporting).

**Spec-rooted items flagged for kickback** (plan deviates from spec.md pending spec amendment): (a) FR-001 names MM-OCEAN as primary data source, but it has no verified public URL — the open `mmbench/ocean` dataset is used as primary; (b) the spec's grounding-validity assumption names a `gpt-4-turbo` judge — removed here (paid API, bias source); (c) FR-018's PR denominator (# correct ratings) is retained per spec, with a supplementary denominator-inclusive metric `PR_all` reported alongside to address selection bias; (d) spec US-4 assumes 200 videos; the power analysis requires a few hundred videos, which the open dataset provides within the runtime budget.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `transformers>=4.40`, `datasets>=2.18`, `torch>=2.2` (CPU-only), `bitsandbytes>=0.43` (4-bit quantisation), `sentence-transformers>=2.2`, `scikit-learn>=1.5`, `statsmodels>=0.14`, `pandas>=2.2`, `pyyaml>=6.0`, `tqdm`, `jsonschema`, `psutil`
- **Storage**: File-based under `data/` (raw streamed metadata, derived CSV/JSON).
- **Testing**: `pytest` with contract validation (`jsonschema`) against all four contracts.
- **Target Platform**: Linux GitHub Actions runner (CPU-only).
- **Performance Goals**: Complete 27 models × ~350–400 videos × 3 conditions in ≤ 6 h wall-clock (~4 h projected), peak RAM ≤ 7 GB.
- **Constraints**: CPU-only quantised inference; batch size ≤ 20; pre-registered top-15 models + 10-frame sampling fallback decided by pre-inference projection only.

## Constitution Check
| Principle | Satisfaction / Reference |
|-----------|---------------------------|
| **I. Reproducibility** | All scripts are deterministic (fixed seeds in `src/pipeline/utils.py`). External data fetched from the canonical verified HuggingFace URL. |
| **II. Verified Accuracy** | No new citations beyond those in the spec; all references are verified by the Reference-Validator. |
| **III. Data Hygiene** | Raw files checksummed; transformations write new files under `data/derived/`. |
| **IV. Single Source of Truth** | Every figure/table is generated directly from CSV/JSON artifacts produced by the pipeline; each pipeline stage validates its inputs/outputs against the contract schemas in `contracts/`. |
| **V. Versioning Discipline** | Content hashes recorded automatically by the platform; any change updates the project's state file. |
| **VI. Context-Grounded Evaluation** | Metrics (PR, HR, IR) explicitly require detection of injected context phrases; Integration-failure Rate captures this. |
| **VII. Resource-Constrained Inference Discipline** | 4-bit quantised models, batch limits, and pre-inference-projection fallback keep RAM < 7 GB and runtime ≤ 6 h. |
| **Dataset Availability** | MM-OCEAN has **no verified public URL**; the verified open dataset `mmbench/ocean` (https://huggingface.co/datasets/mmbench/ocean) is the PRIMARY data source for all reported results. MM-OCEAN is a future supplemental replication only. This deviates from spec FR-001 (flagged for kickback). |

## Phase Mapping (FR ↔ SC Coverage)

Every pipeline stage validates its artifacts against the corresponding contract in `contracts/`: `video_metadata.schema.yaml` (Phase 0), `context_profile.schema.yaml` (Phase 2), `model_output.schema.yaml` (Phases 3–5), `metric_record.schema.yaml` (Phase 6). Contract tests (`pytest -m contract`) enforce compliance at every stage boundary.

| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **0. Data Acquisition** | Download/verify `mmbench/ocean` (primary dataset), compute checksum, validate each record against `contracts/video_metadata.schema.yaml`. | FR-001 (via open substitute; spec gap flagged) | SC-004, SC-009 |
| **1. Knowledge-Base Construction** | Load static JSON, validate every context profile against `contracts/context_profile.schema.yaml`, enable fast lookup. | FR-002 | SC-006 |
| **2. Baseline Prompting** | Run standard prompt on each model–video pair; store raw JSON output validated against `contracts/model_output.schema.yaml`. | FR-003, FR-010, FR-018 | SC-004, SC-008 |
| **3. Context-Grounded Prompting** | Retrieve appropriate context profile (schema-validated in Phase 1), inject into prompt, run inference; outputs validated against `contracts/model_output.schema.yaml`. | FR-004, FR-008, FR-009 | SC-006, SC-007 |
| **4. Random-Noise Control** | Replace context profile with random noise string; run inference; outputs validated against `contracts/model_output.schema.yaml`. | FR-006 | SC-002 |
| **5. Metric Computation** | Derive PR (spec FR-018 denominator), HR, IR, plus supplementary `PR_all` and per-model accuracy, per model & condition; filter invalid/uncertain samples. Grounding validity judged by **calibrated semantic similarity** (cosine ≥ 0.70, kappa-calibrated on a 30-sample pilot, threshold swept). | FR-008–FR-011, FR-018, FR-020 | SC-001, SC-003, SC-005 |
| **6. Statistical Analysis** | **Video-level primary test**: mixed-effects model with video and model as random effects; explicit power calculation (≥ 0.80 for d = 0.5, see research.md). Model-level paired t-test/Wilcoxon as secondary (power ≈ 0.65, reported as limitation). Bonferroni correction, confidence intervals, sensitivity sweep. | FR-005, FR-019 | SC-001, SC-002, SC-005, SC-010 |
| **7. Quantisation-Impact Control** | Run a subset of 5 models at 8-bit (and a tiny full-precision sample) to confirm quantisation does not bias the intervention effect. | FR-021 | SC-011 |
| **8. Resource Monitoring & Predefined Fallback** | 10-video pilot measures throughput; PRE-INFERENCE projection decides whether the pre-registered fallback (top-15 models, 10-frame sampling) is applied — uniformly across all conditions, before any inference data exists. | FR-007, FR-022 | SC-003 |
| **9. Condition Order Randomisation** | Randomly permute condition order per model–video pair (fixed seed) to eliminate order effects. | FR-023 | SC-012 |
| **10. Reporting** | Write CSV/JSON tables, generate figures, produce `results.md` including dataset-substitution note, power report, and resource-budget status. | (deliverable) | SC-001–SC-012 |

Each phase lives in its own module under `src/pipeline/` and is orchestrated by `python -m src.pipeline.run_all`. The order respects data dependencies (download → knowledge base → inference → metrics → analysis → reporting).

## Risk & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| MM-OCEAN not publicly downloadable | FR-001 as written unmet | Verified open substitute `mmbench/ocean` is the primary dataset for all reported results; spec FR-001 flagged for kickback; MM-OCEAN noted as future replication. |
| CPU inference exceeds time budget | Failure of SC-003 | 4-bit quantisation, batch size 20, pre-inference-projection fallback (uniform across conditions, decided before any inference). |
| Missing context tags → higher IR | Potential violation of SC-006 | Neutral-context fallback (FR-009) logged; IR counts only successful retrievals. |
| Invalid JSON from models | Inflates exclusion rate, threatens SC-008 | Strict JSON schema, retry up to 2 times, then mark invalid (FR-010). |
| Multiple-comparison inflation | False positives | Bonferroni correction across the three primary hypothesis tests. |
| Under-powered model-level test | False negative at model level | Video-level primary test with explicit power ≥ 0.80 (design-effect calculation in research.md); model-level test reported as secondary with power ≈ 0.65 acknowledged. |
| PR denominator selection bias | PR unstable for low-accuracy models | Primary PR follows spec FR-018; supplementary `PR_all` (all valid predictions) and per-model accuracy reported; primary test at video level dilutes per-model instability. Spec change flagged for kickback. |
| Fallback bias | Selection bias | Fallback decided by pre-inference projection from a 10-video pilot; applied uniformly to all conditions; no mid-experiment model dropping. |
| Order effects | Confound paired comparisons | Randomise condition order per model–video pair (counterbalancing, fixed seed). |