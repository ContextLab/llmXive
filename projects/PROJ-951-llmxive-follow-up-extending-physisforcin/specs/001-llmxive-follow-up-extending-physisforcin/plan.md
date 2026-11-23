# Implementation Plan: llmXive follow‑up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

**Branch**: `001-llmxive-physs-filter` | **Date**: 2026-10-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-llmxive-physs-filter/spec.md`

> **Spec‑scope flag (kickback)**: FR‑001, FR‑010, FR‑019 and the Wan2.1‑weights assumption in spec.md still mandate local Wan2.1 *generation*. Local Wan2.1 inference requires a multi‑GB GPU and has no faithful CPU form; the plan therefore **acquires real pre‑generated Wan2.1 videos** from a verified open dataset. The spec FRs/assumptions must be amended to describe acquisition of pre‑generated Wan2.1 outputs (identical source and acquisition pipeline for both conditions, differing only in the post‑generation filter) before plan and spec are fully consistent. This plan proceeds under that corrected scope.

## Summary

The experiment tests whether a **post‑generation physics‑consistency filter** (headless PyBullet, scoring trajectory continuity + contact conservation) applied to Wan2.1‑generated robotic‑manipulation videos yields downstream physical consistency **statistically equivalent** (≤ 15 % gap, TOST) **between the filtered and unfiltered models**. The PhysisForcing baseline is reported only for contextual comparison.

**Critical feasibility correction vs. the prior draft**: Wan is a multi‑billion‑parameter video diffusion transformer. Running Wan2.1 inference on the CPU‑only free‑tier runner is **not feasible**, and fabricating a "CPU Wan2.1" would be rejected. Instead, the pipeline **downloads real Wan2.1‑generated robotic‑manipulation videos** from a verified open dataset (Rapidata text‑2‑video human‑preferences Wan2.1 collection) and filters them. This preserves the experimental construct — synthetic videos produced by the Wan2.1 model — while remaining executable.

Pipeline stages:

1. **Acquire** real Wan2.1‑generated videos + prompts from the verified Rapidata dataset, filtering for robotic‑manipulation prompts (e.g., containing “robotic”, “manipulation”, “grasp”). Both conditions draw from the SAME acquisition pipeline; the only difference is the filter. (FR‑001, FR‑010, FR‑019 as scope‑corrected)
2. **Score** every video with a headless PyBullet physics filter (trajectory continuity, contact conservation; 0–100 raw → normalized 0–1). Crashes or corrupted frames receive a failure designation, minimum score, and exclusion. (FR‑002, US‑1 scenarios 2–3, edge cases)
3. **Curate** — discard any video with **normalized physics score < 0.60** (raw < 60, the 60th‑percentile per 2506.09162). Write curated and unfiltered manifests under `data/derived/manifests/`; record retention rate; ensure n ≥ 64 per condition by pulling additional manipulation videos if short. (FR‑003, FR‑010, FR‑019, SC‑001, edge case)
4. **Validate** each `VideoSample` against `video_sample.schema.yaml` via contract tests. (FR‑014, FR‑024)
5. **Train ≈ 50 M‑parameter distilled diffusion model** on curated set (CPU‑only, pinned seed, NaN‑loss guard with ≤ 3 LR retries, monotonic‑loss check, ≤ 4 h); record duration & peak RAM. (FR‑004, FR‑007, SC‑005, FR‑006)
6. **Train the unfiltered‑baseline model** with identical hyperparameters on the unfiltered manifest. (FR‑010, FR‑019)
7. **Generate videos** — each trained model produces ≥ 64 new robotic‑manipulation videos; store in `data/derived/generated/`. (US‑2 scenario 2, FR‑004)
8. **MuJoCo independent validation** — score generated videos from each condition; compute Pearson correlation vs. PyBullet scores (must be ≤ 0.95). (FR‑005, SC‑006)
9. **Go/No‑go sanity gate** — if **< 80 %** of the generated videos achieve a MuJoCo physics‑consistency score ≥ the 60th‑percentile of the original uncurated batch, the pipeline aborts, logs a **null‑result** record, and skips downstream evaluation (T12–T15). This gate ensures that the downstream TOST is not vacuous and gives an honest interpretation of a null result (see research.md). (new)
10. **Benchmark evaluation** — R‑Bench and PAI‑Bench scores for the filtered model, unfiltered baseline, and **PhysisForcing baseline** (descriptive); computes % gap filtered vs. PhysisForcing (descriptive) and filtered vs. unfiltered (primary). (FR‑005, FR‑018, SC‑002, SC‑003)
11. **Statistical equivalence testing** — runs only if the sanity gate passed. Performs Shapiro‑Wilk, Levene, independence diagnostics; primary TOST (filtered vs. unfiltered) with 15 % margin, α = 0.05; fallback Mann‑Whitney U if assumptions violated; reports p‑value and equivalence flag. (FR‑006, FR‑013, FR‑017, SC‑004)
12. **Final report & figures** — aggregate SC‑001–SC‑006 into `data/reports/final_summary.md` + figures, all read from JSON/CSV artifacts. (Principle IV)
13. **End‑to‑end quickstart run** — the full sequence T1→T15 documented in `quickstart.md`. (FR‑022)

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies** (pinned in `code/requirements.txt`):
`torch==2.3.0` (CPU wheel), `pybullet==3.2.6`, `mujoco==3.1.6`, `datasets==2.18.0`, `opencv-python==4.9.0.84`, `pandas==2.2.2`, `scipy==1.13.0`, `jsonschema==4.22.0`, `pytest==8.2.2`, `matplotlib==3.8.4`
**Storage**: files under `data/` (raw downloads with SHA‑256 checksums, derived manifests, model checkpoints, JSON/CSV reports).
**Testing**: pytest; contract tests in `tests/contract/test_contracts.py` validate artifacts against `contracts/*.schema.yaml`.
**Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU cores, ~7 GB RAM, ≤ 6 h/job), pure CPU.
**Compute Strategy**: All steps are CPU‑first; only the optional Kaggle GPU escape hatch could be used for training if the CPU run fails (real `device="cuda"` re‑run).

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Seeds pinned in `src/utils/seeding.py`; videos fetched from the same verified HF URLs each run; SHA‑256 checksums recorded under `data/`. |
| II. Verified Accuracy | Only the verified dataset URLs from the spec’s verified block are cited; the 60th‑percentile raw score = 60 is cited to 2506.09162 (https://arxiv.org/abs/2506.09162). |
| III. Data Hygiene | Raw downloads immutable under `data/raw/` with checksums; every transformation writes new files under `data/derived/`. No PII. |
| IV. Single Source of Truth | Every reported number (SC‑001–SC‑006) is read programmatically from JSON/CSV artifacts; no hand‑typed numbers. |
| V. Versioning Discipline | Artifacts carry content hashes; the project state file’s `updated_at` is updated on each artifact change. |
| VI. Physics‑Consistency Verification | Every training sample passed the headless PyBullet filter; videos with raw score < 60 (normalized < 0.60) discarded. |
| VII. Benchmark Alignment | Evaluation exclusively uses R‑Bench and PAI‑Bench scores; PhysisForcing baseline scores are reported only for context. |

## Project Structure

```text
code/
├── requirements.txt
├── config.yaml                  # conforms to contracts/config.schema.yaml
├── src/
│   ├── utils/
│   │   ├── verify_env.py        # FR‑021, FR‑007, FR‑023
│   │   ├── seeding.py           # Principle I
│   │   └── profile_memory.py    # SC‑005 timing/RAM
│   ├── data/
│   │   ├── download_videos.py   # verified Wan2.1 dataset (FR‑001, FR‑010)
│   │   └── checksum.py          # Principle III
│   ├── filtering/
│   │   ├── pybullet_filter.py   # FR‑002, FR‑003, SC‑001
│   │   └── mujoco_validator.py  # FR‑005, SC‑002, SC‑006
│   ├── training/
│   │   └── train_diffusion.py   # FR‑004, FR‑007, SC‑005, loss monotonicity
│   └── evaluation/
│       ├── generate_videos.py   # generate ≥64 videos per model (US‑2)
│       ├── check_gate.py        # go/no‑go sanity gate (T11)
│       ├── evaluate_benchmarks.py  # FR‑005, SC‑002, SC‑003
│       ├── tost_equivalence.py     # FR‑006, FR‑013, FR‑017, SC‑004
│       └── generate_report.py      # aggregates SC‑001..SC‑006
├── tests/
│   ├── contract/test_contracts.py  # FR‑014, FR‑024
│   └── unit/
data/
├── raw/wan21_videos/            # immutable, checksummed
├── derived/
│   ├── video_samples/           # VideoSample JSON per video
│   ├── physics_scores/          # PhysicsScore JSON per video
│   ├── manifests/               # curated_*.json, unfiltered_*.json
│   └── models/                  # checkpoints
└── reports/                     # benchmark JSONs, TOST results, final summary
```

**Structure Decision**: single flat `src/` package mirroring pipeline stages; no unnecessary scaffolding.

## Task List

| ID | Description | FR/SC addressed | Script |
|----|-------------|-----------------|--------|
| T1 | **Environment audit & config** — assert `torch.cuda.is_available() is False`, load `config.yaml` (validated against `config.schema.yaml`) | FR‑007, FR‑021, FR‑023 | `src/utils/verify_env.py` |
| T2 | **Download real Wan2.1 videos** from the verified Rapidata dataset, stream parquet, filter prompts for robotic‑manipulation keywords, checksum into `data/raw/` | FR‑001, FR‑010, Principle I/III | `src/data/download_videos.py` |
| T3 | Emit a `VideoSample` record per video and validate against `video_sample.schema.yaml` via contract tests | FR‑014, FR‑024 | `tests/contract/test_contracts.py` |
| T4 | **PyBullet physics filter** — headless simulation per video; score trajectory continuity + contact conservation (0–100 raw → normalized 0–1); simulation crashes → failure designation, minimum score, exclusion + logging; corrupted frames → default low score + exclusion | FR‑002, US‑1 scenarios 2–3, edge cases | `src/filtering/pybullet_filter.py` |
| T5 | **Curate** — discard any video with normalized score < 0.60 (raw < 60); write curated and unfiltered manifests under `data/derived/manifests/`; record retention rate; ensure n ≥ 64 per condition by pulling additional manipulation videos if short | FR‑003, FR‑010, FR‑019, SC‑001, edge case | `src/filtering/pybullet_filter.py` |
| T6 | Validate curated/unfiltered manifests against `curated_dataset.schema.yaml` | FR‑014 | `tests/contract/test_contracts.py` |
| T7 | **Train ≈ 50 M‑parameter distilled diffusion model** on curated set (CPU‑only, pinned seed, NaN‑loss guard with ≤ 3 LR retries, monotonic‑loss check, ≤ 4 h); record duration & peak RAM | FR‑004, FR‑007, SC‑005, FR‑006 | `src/training/train_diffusion.py`, `src/utils/profile_memory.py` |
| T8 | Train the **unfiltered‑baseline model** with identical hyperparameters on the unfiltered manifest | FR‑010, FR‑019 | `src/training/train_diffusion.py` |
| T9 | **Generate videos** — each trained model produces ≥ 64 new robotic‑manipulation videos; store in `data/derived/generated/` | US‑2 scenario 2, FR‑004 | `src/evaluation/generate_videos.py` |
| T10 | **MuJoCo independent validation** — score generated videos from each condition; compute Pearson correlation vs. PyBullet scores (must be ≤ 0.95) | FR‑005, SC‑006 | `src/filtering/mujoco_validator.py` |
| T11 | **Go/No‑go sanity gate** — if < 80 % of generated videos achieve a MuJoCo score ≥ the 60th‑percentile of the original uncurated batch, abort pipeline, log a null‑result record, and skip downstream evaluation (T12–T15). Only if the gate passes does the pipeline proceed to T12–T15. | New safety check ensuring meaningful TOST | `src/evaluation/check_gate.py` |
| T12 | **Benchmark evaluation** — R‑Bench and PAI‑Bench scores for the filtered model, unfiltered baseline, and PhysisForcing baseline (descriptive); computes % gap filtered vs. PhysisForcing (descriptive) and filtered vs. unfiltered (primary) | FR‑005, FR‑018, SC‑002, SC‑003 | `src/evaluation/evaluate_benchmarks.py` |
| T13 | **Statistical equivalence testing** — runs only if the sanity gate (T11) passed. Performs Shapiro‑Wilk, Levene, independence diagnostics; primary TOST (filtered vs. unfiltered) with 15 % margin, α = 0.05; fallback Mann‑Whitney U if assumptions violated; report p‑value and equivalence flag | FR‑006, FR‑013, FR‑017, SC‑004 | `src/evaluation/tost_equivalence.py` |
| T14 | **Final report & figures** — aggregate SC‑001–SC‑006 into `data/reports/final_summary.md` + figures, all read from JSON/CSV artifacts | SC‑001–SC‑006, Principle IV | `src/evaluation/generate_report.py` |
| T15 | **End‑to‑end quickstart run** — the full sequence T1→T14 as documented in `quickstart.md` | FR‑022 | CI script |

## Success Criteria Mapping

| SC | Where measured |
|----|----------------|
| SC‑001 | T5 — retention rate in curated manifest |
| SC‑002 | T10 — average MuJoCo‑validated score on generated videos |
| SC‑003 | T12 — % gap filtered vs. PhysisForcing (descriptive) |
| SC‑004 | T13 — TOST (or Mann‑Whitney) p < 0.05 for filtered vs. unfiltered |
| SC‑005 | T7 — recorded training duration ≤ 4 h |
| SC‑006 | T10 — Pearson correlation ≤ 0.95 |

## Complexity Tracking

All FRs are satisfied with **CPU‑first** methods; the optional Kaggle GPU escape hatch is only a fallback for training if the CPU run fails. No speculative GPU‑only steps remain.