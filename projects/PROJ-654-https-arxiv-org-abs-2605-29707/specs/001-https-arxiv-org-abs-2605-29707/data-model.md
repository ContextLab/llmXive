# Data Model: Reproduce & Validate Domino Speculative Decoding Framework

## Overview

Defines the structured data exchanged between the benchmark script, aggregation utilities, and validation logic.

## Entity Definitions

### 1. Benchmark Run Configuration
```yaml
run_id: "<timestamp+hash>"
timestamp: "<ISO‑8601>"
hardware:
  cpu_cores: 2
  ram_gb: 7.0
  device: "cpu"
model_config:
  target_model_name: "<selected model, e.g., Qwen2-1.8B>"
  draft_model_name: "Qwen2-0.5B"
status: "success" | "failed"
```

### 2. Per‑Run Metrics (raw JSON from `run_hf_benchmark.sh`)

| Field | Type | Description |
|-------|------|-------------|
| `model_name` | string | Target model identifier. |
| `draft_model_name` | string | Draft model identifier. |
| `total_latency` | number (seconds) | End‑to‑end latency for the run. |
| `tokens_generated` | integer | Total tokens produced. |
| `tokens_per_second` | number | Throughput. |
| `baseline_latency` | number (optional) | Latency of the baseline autoregressive run. |
| `domino_latency` | number (optional) | Latency of the Domino run. |
| `speedup_ratio` | number | `baseline_latency / domino_latency`. |
| `hardware_context` | string | Human‑readable hardware description. |
| `library_versions` | object | `{ "torch": "...", "transformers": "...", "accelerate": "..." }` – **non‑empty strings required**. |
| `timestamp` | string (ISO‑8601) | Run start time. |
| `status` | string (`success`/`failed`) | Execution outcome. |
| `error_message` | string (optional) | Populated on failure. |

### 3. Aggregated Metrics (output of `aggregate_metrics.py`)

```json
{
  "model_name": "Qwen2-1.8B",
  "draft_model_name": "Qwen2-0.5B",
  "baseline_latency_ms": { "mean": ..., "std": ..., "min": ..., "max": ... },
  "domino_latency_ms":   { "mean": ..., "std": ..., "min": ..., "max": ... },
  "tokens_per_second_baseline": { "mean": ..., "std": ... },
  "tokens_per_second_domino":   { "mean": ..., "std": ... },
  "speedup_ratio": { "mean": ..., "std": ..., "min": ..., "max": ... },
  "acceptance_rate": { "mean": ..., "std": ..., "min": ..., "max": ... },
  "total_tokens": 12345,
  "prompt_count": 30,
  "run_count": 20,
  "peak_ram_gb": 5.8,
  "library_versions": {
    "torch": "2.2.2+cpu",
    "transformers": "4.41.0",
    "accelerate": "0.31.0"
  },
  "timestamp": "2025-07-01T12:34:56Z",
  "status": "success"
}
```

### 4. Validation Report (output of `report_generator.py`)

| Field | Type | Description |
|-------|------|-------------|
| `feature_id` | string | Fixed to `001-reproduce-domino-speculative-decoding`. |
| `hardware_context` | string | e.g., `"2 vCPU, 7 GB RAM"`. |
| `model_substitution` | string | Explanation of any fallback (e.g., `Qwen3 → Qwen2‑1.8B/0.5B`). |
| `speedup_mean` | number | Mean speedup (baseline_latency / domino_latency). |
| `speedup_std` | number | Standard deviation of speedup. |
| `confidence_interval_95` | object (`lower`, `upper`) | 95 % CI for speedup. |
| `p_value` | number | Result of paired t‑test (Baseline vs. Domino). |
| `statistical_pass` | boolean | `true` if `p_value < 0.05`. |
| `speedup_positive` | boolean | `true` if `speedup_mean > 1.0`. |
| `tolerance_pass` | boolean | `true` if `speedup_mean` lies within ±20 % of the paper claim (4.392 – 6.588). |
| `pass_status` | enum (`PASS`, `FAIL`) | `PASS` **only** if `statistical_pass && speedup_positive`; otherwise `FAIL`. |
| `notes` | string | Free‑form commentary, including hardware mismatch disclaimer. |
| `timestamp` | string (ISO‑8601) | Report generation time. |

## Constraints

- **Latency values** must be > 0.  
- **Speedup** must be > 0.  
- **Model names** must correspond to a valid HuggingFace identifier.  
- **RAM usage** (`peak_ram_gb`) must be ≤ 6.5 GB (explicit limit matching SC‑002).  
- **Library version strings** must be non‑empty (enforced by `minLength: 1` in the schema).  

## Model Fallback Policy (Addressing Edge Cases)

Allowed fallback models (CPU‑friendly, ≤ 7 GB RAM):

1. `Qwen/Qwen2-1.8B` (≈ 4 GB) – primary.  
2. `Qwen/Qwen2-0.5B` (≈ 1.2 GB) – secondary fallback.

Models such as `Llama-2-7B` are **excluded** because they cannot be loaded in FP32 within the RAM budget without disallowed quantization.

## Data Flow Summary

1. **Setup** → hardware detection → model selection.  
2. **Benchmark** → per‑run JSON files → `resource_monitor.py` records RAM.  
3. **Aggregation** → `aggregate_metrics.py` produces `benchmark_metrics_aggregated.json`.  
4. **Validation** → `report_generator.py` consumes aggregated metrics → `validation_report.md`.
