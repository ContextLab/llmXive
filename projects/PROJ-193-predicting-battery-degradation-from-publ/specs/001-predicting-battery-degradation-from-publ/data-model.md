# Data Model: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

## Overview

Canonical representations for the pipeline. All artifacts under `data/` carry versioned filenames and provenance metadata; raw data is immutable (checksummed). Schemas in `contracts/` are validated by pytest (FR‑013). **No synthetic or placeholder data enters `data/`** (FR‑012); test fixtures live under `tests/fixtures/` and never produce reported metrics.

## Entities

| Entity | Description | Fields |
|--------|-------------|--------|
| **BatteryCell** | Raw per‑cell record parsed from source CSVs. | `cell_id: string`, `protocol_type: string`, `cycle_numbers: list[int]`, `voltage_trace`, `current_trace`, `temperature_trace` (per‑cycle time‑series), `per_cycle_capacity: list[float]` |
| **SequenceWindow** | Processed model input. | `cell_id: string`, `input_sequence: floating-point ndarray (50, 100, 3)`, `target_fade: float` where fade = (Q_initial − Q_final)/Q_initial **computed at cycle 100** (cells with fewer than 100 cycles are filtered out). |
| **AggregatedFeatureImportance** | Summarized importance scores derived from raw time‑step/channel attributions. | `cell_id: string`, `per_cycle_importance: list[float]` (length 50, each the sum over 100 timesteps × 3 channels), `per_channel_importance: dict[string, float]` (`voltage`, `current`, `temperature`), `derived_signatures: dict[string, float]` (e.g., early‑cycle voltage variance, current slope, temperature fluctuation; these correspond to literature‑cited degradation signatures such as ΔQ(V) variance, early‑cycle capacity‑fade slope, incremental‑capacity peak shifts). |
| **ModelPrediction** | Model output per test cell. | `cell_id: string`, `predicted_fade: float`, `ci_lower: float`, `ci_upper: float`, `feature_importance_scores: AggregatedFeatureImportance` |
| **BaselineFeatureSet** | Hand‑crafted incremental‑capacity features **restricted to cycles 1‑50** (aligns with FR‑010). | `cell_id: string`, `features: dict[string, float]` (e.g., `dq_variance_1_50`, `fade_slope_early`, `ic_peak_shift_1_50`), `target_fade: float` |

## Splits

- Train/validation: 80/20 by cell, stratified by `protocol_type`, fixed seed.
- Test: entire held‑out protocol family (≥ 10 cells, FR‑011), guaranteed disjoint from training protocols.

## Provenance

Every processed file records: source URLs, checksums of raw inputs, pipeline version, seed, and generation timestamp.

Derived files never overwrite raw files (Constitution III).

## Contracts

Validated by `tests/contract/test_processed_schema.py` and `tests/contract/test_model_output_schema.py` against `contracts/processed_dataset.schema.yaml` and `contracts/model_output.schema.yaml` (see `contracts/` files). Contract tests run on fixture‑derived artifacts; schema conformance of real‑data artifacts is asserted in‑pipeline at write time.

## Mapping to Literature Signatures (new)

`src/interpret/literature_mapping.py` defines explicit rules that map aggregated signatures (e.g., average voltage variance over cycles 1‑10) to the literature‑cited features required by SC‑010. This mapping enables a deterministic check that at least three of the top aggregated features correspond to known early‑cycle degradation signatures.
