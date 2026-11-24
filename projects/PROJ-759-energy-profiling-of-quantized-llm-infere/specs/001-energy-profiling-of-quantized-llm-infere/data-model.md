# Data Model: Energy Profiling of Quantized LLM Inference on Edge CPUs

## Overview

Three core entity types — **Configuration**, **InferenceRun**, **AggregatedMetric** — defined by JSON Schemas in `contracts/` and validated by `tests/` . This revision aligns the schemas with the intended implementation (Task T8) and clarifies exclusion rules.

## Entities

- **Configuration**: a unique model‑size × quantization pair (Several primary configs + LLaMA‑7B attempt configs). Includes `quantization_status` (`ok` / `failed`) so a failed quantization is explicit, never a disguised FP16 checkpoint.
- **InferenceRun**: one seeded execution of a Configuration; stores net energy, latency, token count, perplexity, measurement method, CPU frequency, timestamp. Energy may be `null` when measurement_method is `"unavailable"`; such runs are **excluded** from aggregation (see aggregation step).
- **AggregatedMetric**: mean/std summary over the multiple InferenceRuns per Configuration, plus dequantization‑overhead and variance‑stability flags.

## Data Flow

1. Configurations generated once (T2) → `data/configs/*.json`, validated against `config.schema.yaml`.
2. InferenceRuns emitted per repetition (T6) → `data/results/runs/<config_id>_<run_index>.json`, validated against `inference_run.schema.yaml`.
3. AggregatedMetrics computed (T8) → `data/results/aggregated.csv` (one row per config), validated against `aggregated.schema.yaml`.
4. `summary.json` (T9/T11) derives exclusively from `aggregated.csv` and run JSONs (Principle IV).

Raw WikiText‑2 parquet is preserved unchanged under `data/raw/` with a recorded SHA‑256; all derivations write new files with provenance (Principle III).

## Exclusion Rule (new)

Runs where `measurement_method` is `"unavailable"` are **excluded** from all energy‑per‑token aggregations; the corresponding `energy_joules` field may be `null`. Consequently, `mean_energy_per_token` and `std_energy_per_token` may be `null` when no energy measurements exist for a configuration.
