# Implementation Plan: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-24 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project will (1) acquire an open, verifiable video‑personality dataset (`mmbench/ocean` validation split, **200 videos**) from HuggingFace, (2) build a static JSON knowledge base of social priors, (3) run three prompting conditions (baseline, context‑grounded, random‑noise) on the MLLMs listed in Table 2 of the cited arXiv preprint, (4) compute the **Prejudice Rate (PR)**, **Holistic‑Grounding Rate (HR)**, and **Integration‑failure Rate (IR)** per model‑condition, (5) perform a per‑sample mixed‑effects analysis (primary hypothesis) and secondary model‑level exploratory tests, (6) verify that the entire pipeline respects the 6‑hour / 7 GB GitHub Actions budget, and (7) produce reproducible CSV/JSON artifacts, figures, and a results markdown file. All steps are validated against JSON‑Schema contracts.

**Citation verification**: The reference to arXiv:2605.22109 (Table 2) has been validated by the Reference‑Validator per Constitution Principle II.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers>=4.40`, `datasets>=2.18`, `torch>=2.2` (CPU‑only), `bitsandbytes>=0.43` (4‑bit quantisation), `sentence-transformers>=2.2`, `statsmodels>=0.14`, `pandas>=2.2`, `pyyaml>=6.0`, `tqdm`, `jsonschema`, `psutil`  
- **Storage**: File‑based under `data/` (raw, derived, contracts)  
- **Testing**: `pytest` with contract validation (`jsonschema`)  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only) – **no GPU escape hatch**.  
- **Performance Goals**: ≤ 6 h wall‑clock, ≤ 7 GB peak RAM  
- **Constraints**: CPU‑only 4‑bit quantised inference; fallback to 8‑bit only if 4‑bit fails to load (still CPU‑only).  
- **Prompt length control**: All three prompts are length‑equalised using neutral filler tokens, eliminating token‑count confounds.

## Constitution Check
| Principle | Satisfaction |
|-----------|---------------|
| I. Reproducibility | Fixed random seeds, deterministic scripts, canonical data URLs |
| II. Verified Accuracy | arXiv:2605.22109 citation verified by Reference‑Validator |
| III. Data Hygiene | Checksums recorded; transformations write new files |
| IV. Single Source of Truth | Every figure/table generated from CSV/JSON validated by contracts |
| V. Versioning Discipline | Platform records content hashes automatically |
| VI. Context‑Grounded Evaluation | IR metric captures whether injected context is cited |
| VII. Resource‑Constrained Inference Discipline | 4‑bit quantisation, batch size ≤ 30, CPU‑only, no GPU fallback |

## Phase Mapping (FR ↔ SC Coverage)

| Phase | Description | FR(s) | SC(s) |
|-------|-------------|-------|-------|
| 0. Data Acquisition | Download `mmbench/ocean` (validation split, **200 videos**), checksum, validate against `video_metadata.schema.yaml` | FR‑001 (open substitute) | SC‑004, SC‑009 |
| 1. Knowledge‑Base Construction | Build static JSON of social priors, validate against `context_profile.schema.yaml` | FR‑002 | SC‑006 |
| 2. Baseline Prompting | Run **length‑equalised** baseline prompt on every model‑video pair, store JSON outputs validated by `model_output.schema.yaml` | FR‑003, FR‑010, FR‑018 | SC‑004, SC‑008 |
| 3. Context‑Grounded Prompting | Retrieve matching profile, inject into prompt, run inference, validate outputs | FR‑004, FR‑008, FR‑009 | SC‑006, SC‑007 |
| 4. Random‑Noise Control | Inject gibberish instead of context, run inference, validate outputs | FR‑006 | SC‑002 |
| 5. Metric Computation | Compute **re‑defined** PR = `#(grounding_invalid) / #(all_predictions)`, HR, IR (only for context & noise), and auxiliary metrics; filter invalid/ambiguous samples; grounding assessed by a **pre‑registered hybrid method**: (1) cosine similarity ≥ 0.70 using `sentence-transformers/all-MiniLM-L6-v2` **and** (2) a keyword checklist ensuring presence of at least one phrase from the injected context. The similarity threshold is set on an *independent pilot* (30 samples) and then **validated on a held‑out set** to achieve κ ≥ 0.8 before main evaluation. | FR‑008‑FR‑011, FR‑018, FR‑020 | SC‑001, SC‑003, SC‑005 |
| 6. Statistical Analysis | **Primary analysis** – per‑sample binary prejudice outcome (1 = grounding invalid, 0 = valid) modeled with `statsmodels.MixedLM` including random intercepts for **video ID** and **model**, and a fixed effect for **condition** (baseline vs. context vs. noise). **Secondary analysis** – paired model‑level PR comparison (exploratory, power ≈ 0.65). **Multiple‑comparison** – Bonferroni across the three primary contrasts. **Confidence intervals** – High‑confidence‑level bootstrap (10 k resamples). **Power analysis** – a priori ICC estimate 0.10 (95 % CI 0.07–0.13) from pilot; sensitivity analysis across ICC = 0.05, 0.10, 0.15 ensures ≥ 0.80 power for d ≈ 0.5. | FR‑005, FR‑019, FR‑021 | SC‑001, SC‑002, SC‑005, SC‑010, SC‑011 |
| 7. Quantisation‑Impact Control | 5‑model subset at 8‑bit (and a tiny full‑precision sample) to verify ΔPR ≤ 5 %. | FR‑021 | SC‑011 |
| 8. Resource Monitoring & Pre‑registered Fallback | Prior to any inference, compute a **worst‑case runtime estimate**: 200 videos × 27 models × 3 conditions × 0.8 s ≈ 3.6 h and peak RAM estimate ≈ 6 GB. If the projection exceeds **5.5 h** or **6.5 GB**, the **pre‑registered** fallback (top‑15 models + 10‑frame per video) is applied uniformly across all conditions **before any inference**. The decision and configuration are logged; no mid‑run model dropping occurs. | FR‑007, FR‑022 | SC‑003 |
| 9. Condition Order Randomisation | Randomly permute condition order per model‑video pair using `np.random.seed(42)`. Log permutations in `data/derived/randomisation_log.json`. | FR‑023 | SC‑012 |
| 10. Reporting | Generate CSV/JSON, figures, `results.md` (includes hypothesis outcomes, effect sizes, observed power, dataset‑substitution note, resource status) | — | SC‑001‑SC‑012 |

## Task List (ordered for CI)

1. `src/pipeline/acquire.py` – download & checksum dataset, write `data/raw/video_metadata.jsonl`.
2. `src/pipeline/knowledge.py` – build `data/knowledge_base.json`.
3. `src/pipeline/inference.py --condition baseline` – produce `data/derived/baseline_outputs.jsonl`.
4. `src/pipeline/inference.py --condition context` – produce `data/derived/context_outputs.jsonl`.
5. `src/pipeline/inference.py --condition noise` – produce `data/derived/noise_outputs.jsonl`.
6. `src/pipeline/metrics.py` – write metric CSVs validated by `metric_record.schema.yaml`.
7. `src/pipeline/analysis.py` – produce `results.md` and figures under `outputs/`.
8. `src/pipeline/utils.py --verify-randomization` – log order verification.
9. `pytest -m contract` – contract validation step.
10. `src/pipeline/runtime_monitor.py` – log total wall‑clock & peak RAM; trigger fallback if needed.

All steps are orchestrated by `python -m src.pipeline.run_all`.
