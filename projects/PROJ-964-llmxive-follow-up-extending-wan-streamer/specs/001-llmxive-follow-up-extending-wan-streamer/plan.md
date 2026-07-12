# Implementation Plan: llmXive follow-up: extending "Wan-Streamer v0.1: End-to-end Real-time Interactive Foundation Models"

**Branch**: `001-llmxive-streamer-optimization` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-streamer-optimization/spec.md`

## Summary

This project implements a research pipeline to investigate "low-information manifolds" in audio-visual generation by extending the Wan-Streamer v0.1 framework. The core hypothesis is that a lightweight CPU-tractable estimator (RNN/Transformer) can predict latent vector deltas based on turn-taking semantics, allowing the system to skip expensive flow-matching steps for "low-priority" frames without exceeding a [deferred] degradation in perceptual quality (FID). The implementation covers data extraction from training logs (or re-generation if logs are missing), estimator training, hybrid inference simulation with **counterfactual ground truth generation**, and rigorous statistical validation (TOST, propensity-score matching, randomized counterfactuals).

**Critical Data Constraint**: The project relies on the existence of Wan-Streamer v0.1 training logs containing latent trajectory data. **If these logs are not available in the local environment or a verified public archive, the project MUST fail gracefully with a "Data Unavailable" error (FR-022).** The plan explicitly removes any "re-generation" fallback for the *primary* latent data, as no verified public URL for the Wan-Streamer model weights/inference code exists in the verified datasets block. The VoxCeleb2 dataset (verified) is used only for *proxy* audio-visual turn-taking analysis if the specific latent logs are present, but cannot substitute for the missing latent trajectory variable required by FR-001.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only, default precision), `scikit-learn`, `pandas`, `pyarrow`, `datasets` (HuggingFace), `numpy`, `scipy` (for TOST), `pyyaml`, `torchvision` (for FID via Inception-v3).  
**Storage**: Local filesystem (`data/`), Parquet/CSV formats.  
**Testing**: `pytest` (unit/contract), custom validation scripts for schema and statistical thresholds.  
**Target Platform**: Linux (GitHub Actions Free Tier: multiple CPUs, sufficient RAM, No GPU).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Training ≤ 6 hours, Peak RAM ≤ 7 GB, Inference latency reduction ≥ 20% with FID degradation ≤ 5%.  
**Constraints**: No GPU/CUDA, no 8-bit quantization requiring CUDA, strict memory limits, reproducibility via pinned seeds.  
**Scale/Scope**: Sampled dataset ≤ 1 GB (targeting 10k+ frames, 500+ events), single model training, simulation of hybrid inference with **counterfactual re-runs** for the randomized subset.

> **Note on Empirical Values**: Specific dataset sizes, exact FID thresholds, and power analysis parameters are deferred to the research phase as per the spec. The plan outlines the *method* to measure these, not the values themselves.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Plan Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | Reproducible on fresh runner; pinned seeds; canonical sources. | `code/` will include `requirements.txt` with pinned versions. All random seeds (numpy, torch, python) will be set at the start of every script. Data fetching will use verified HuggingFace URLs (VoxCeleb2) as per `verified datasets` block. **If Wan-Streamer logs are missing, the system exits with "Data Unavailable" (FR-022) to preserve construct validity.** |
| **II. Verified Accuracy** | Citations verified; title overlap ≥ 0.7. | Research.md will cite only the verified dataset URLs provided in the prompt. No external URLs will be invented. |
| **III. Data Hygiene** | Checksums; no in-place modification; no PII. | Data extraction scripts will write to new files with checksums recorded in `state.yaml`. Raw logs (if used) are read-only. PII scan will be part of the CI pipeline. |
| **IV. Single Source of Truth** | Figures/stats trace to one row in `data/` and one block in `code/`. | All metrics (FID, Latency, MOS) will be computed by scripts in `code/` and logged to `data/` artifacts. The paper generation script will read exclusively from these logs. |
| **V. Versioning Discipline** | Content hashes; `state.yaml` updates. | `code/update_state_yaml.py` will compute hashes of all artifacts and update `state.yaml` upon completion of each phase. |
| **VI. Latency-Quality Trade-off** | Paired statistical test; 5% degradation threshold. | The plan explicitly implements FR-005 (TOST, propensity-score matching) and FR-008 (randomized counterfactuals) to satisfy the paired test requirement. A predefined threshold is hardcoded in the validation logic. |
| **VII. Validation Independence** | Estimator trained on partition A; Evaluated on partition B with separate model. | The dataset will be split into Train/Val/Test. The quality assessment model (for FID/MOS) will be a frozen, pre-trained `inception_v3` model (distinct from the estimator) to ensure validation independence. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-streamer-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Canonical files only)
│   ├── dataset.schema.yaml
│   ├── estimator_output.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/
├── data/
│   ├── raw/               # Downloaded logs / Re-generated latents
│   ├── processed/         # Extracted Parquet/CSV (sampled)
│   └── checksums.txt      # SHA256 hashes
├── code/
│   ├── requirements.txt   # Pinned dependencies
│   ├── __init__.py
│   ├── config.py          # Seed pinning, path config
│   ├── tasks/
│   │   ├── extract_data.py        # FR-001, FR-019, FR-022
│   │   ├── train_estimator.py     # FR-002, FR-006
│   │   ├── simulate_inference.py  # FR-003, FR-008
│   │   ├── execute_fallback.py    # FR-006, FR-009, FR-017 (Handles counterfactual re-runs)
│   │   ├── analyze_latency_bias.py# FR-005, FR-007
│   │   ├── calculate_fid_stability_corr.py # FR-010, FR-011
│   │   ├── validate_proxy_mos.py  # FR-012, FR-013, FR-024
│   │   ├── reduce_sample_size.py  # FR-014, FR-023
│   │   ├── validate_sampling_distribution.py # FR-015
│   │   └── update_state_yaml.py   # FR-020
│   └── utils/
│       ├── metrics.py     # FID (Inception-v3), MOS, TOST logic
│       └── fallback_logic.py # FR-006, FR-017
├── tests/
│   ├── contract/          # Schema validation tests
│   └── unit/              # Logic tests (e.g., fallback precedence)
└── state.yaml             # Versioning and artifact hashes
```

**Structure Decision**: Selected a single-project structure with a `code/tasks/` directory to map directly to the Functional Requirements (FR-007, FR-009, FR-011, etc.). This ensures modularity for the Implementer Agent and aligns with the "Task Module" requirement in the spec. **Note**: Only `dataset.schema.yaml`, `estimator_output.schema.yaml`, and `metrics.schema.yaml` are the canonical contracts; other conflicting files in the `contracts/` directory are deprecated and must be removed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Randomized Counterfactual (FR-008)** | Required to distinguish "easy to skip" from "easy to generate" and establish causal effect. | Observational data alone cannot prove the skip action caused the quality drop; correlation is insufficient for the "low-information manifold" claim. |
| **Counterfactual Re-run (FR-008)** | To measure the *actual* FID degradation of a skipped frame, the system must generate the "Full" version for the *same* frame. | Skipping the re-run would make the comparison between "Skipped (Random)" and "Full (Non-Random)" confounded by selection bias. |
| **Two-Stage Validation (FR-004, VII)** | Estimator and Quality Model must be independent. | Using the same model for training and evaluation would introduce circular validation, invalidating the research claim. |
| **Fallback Precedence Logic (FR-017)** | Randomized intervention must override deterministic fallback. | Simple thresholding would bias the causal inference by excluding the randomized subset from the "skip" condition. |