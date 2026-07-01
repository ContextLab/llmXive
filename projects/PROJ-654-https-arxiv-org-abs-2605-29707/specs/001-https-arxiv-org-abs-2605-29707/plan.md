# Implementation Plan: Reproduce & Validate Domino Speculative Decoding Framework

**Branch**: `001-reproduce-domino-speculative-decoding` | **Date**: 2025-07-01 | **Spec**: `specs/001-reproduce-domino-speculative-decoding/spec.md`

## Overview

The plan executes the vendored `external/Domino` benchmark on a **CPU‑only** GitHub Actions runner, captures robust performance metrics, and validates the Domino algorithm both statistically and against the paper’s reported speedup (contextual only). All functional requirements (FR‑001 – FR‑007) and success criteria (SC‑001 – SC‑005) are addressed.

## Phase 0 – Repository Setup

| Step | Action | Output |
|------|--------|--------|
| 0.1 | Clone repository with submodules (`git submodule update --init --recursive`). | `external/Domino/` present. |
| 0.2 | Install **CPU‑only** PyTorch and other deps. Remove any `bitsandbytes` entry from `requirements-hf.txt`. | `requirements.txt` ready. |
| 0.3 | Pin exact library versions (e.g., `torch==2.2.2+cpu`, `transformers==4.41.0`, `accelerate==0.31.0`). Write them to `versions.txt`. | Versions recorded for later injection. |

## Phase 1 – Constitution Check (new)

1. Verify that `projects/PROJ-654-https-arxiv-org-abs-2605-29707/.specify/memory/constitution.md` exists.  
2. If missing, abort the pipeline with error:  

```
CONSTITUTION_MISSING: constitution.md not found. Provide the file to proceed.
```

This satisfies the Constitution Principle and makes the missing file a blocking issue.

## Phase 1 – Dynamic Hardware Detection (FR‑004)

A Python helper `src/utils/hardware_detect.py` will:

1. Detect CUDA availability via `torch.cuda.is_available()`.  
2. Set `DEVICE` to `"cpu"` if no GPU, otherwise `"cuda"`.  
3. Write `hardware.json` containing `cpu_cores`, `ram_gb`, and `device`.  
4. Export `DEVICE` as an environment variable for downstream scripts.  

**Artifact**: `hardware.json`.

## Phase 1.5 – Device‑Map Configuration

`src/utils/device_config.py` reads `hardware.json` and creates `device_config.json`:

```json
{ "device_map": "cpu" }
```

All downstream benchmark scripts load this file and pass `device_map` to `from_pretrained`.

## Phase 2 – Model Selection & Fallback (FR‑001, Edge Cases)

1. Preferred model list (ordered):  
   - `Qwen/Qwen2-1.8B` (≈ 4 GB) – primary.  
   - `Qwen/Qwen2-0.5B` (≈ 1.2 GB) – secondary fallback.  
2. Attempt to load the first model inside a `try/except` block.  
3. On `MemoryError` or `RuntimeError` indicating OOM, automatically retry with the next smaller model.  
4. If all attempts fail, abort with a clear error:  

```
OUT_OF_MEMORY: Unable to fit any allowed model within 7 GB RAM.
```

5. Record the selected model and any fallback actions in `model_selection.json`.

## Phase 3 – Benchmark Execution (FR‑002, FR‑003, FR‑005, SC‑001, SC‑002)

*Configuration* (`benchmark_config.yaml`):

```yaml
prompt_count: a predetermined set of prompts                     # increased to improve statistical power
max_tokens_per_prompt:
timeout_seconds: a sufficiently large duration to accommodate extended processing periods without premature termination.                # 45 min guard
device: "${DEVICE}"
model_name: "${SELECTED_MODEL}"
draft_model_name: "Qwen/Qwen2-0.5B"
run_repeats: multiple
```

Execution steps:

1. **Resource Monitor** (`src/utils/resource_monitor.py`) logs peak RSS (`peak_ram_gb`) every second to `resource_log.json`.  
2. **Timeout Wrapper**: `timeout ${timeout_seconds} bash external/Domino/run_hf_benchmark.sh benchmark_config.yaml`.  
3. The script outputs per‑run JSON files (`run_01.json … run_20.json`) containing latency, token counts, and hardware context.  
4. After all repeats, `src/validation/aggregate_metrics.py` reads `versions.txt` and injects the exact library versions into each per‑run JSON and the aggregated output `benchmark_metrics_aggregated.json` (conforms to `contracts/benchmark_metrics.schema.yaml`).  
5. **RAM Assertion** – after aggregation, a check aborts the job if `peak_ram_gb > 6.5`. The failure message is recorded in `resource_log.json`.

## Phase 4 – Version Logging (FR‑006)

During aggregation, capture exact library versions from `versions.txt`:

```json
"library_versions": {
  "torch": "2.2.2+cpu",
  "transformers": "4.41.0",
  "accelerate": "0.31.0"
}
```

These are added to both each per‑run JSON (via the aggregation wrapper) and the aggregated metrics artifact.

## Phase 5 – Statistical Validation & Tolerance Check (FR‑007, SC‑003, SC‑004)

1. **Statistical Test**: Paired two‑sample t‑test between baseline and Domino latencies across the 20 runs. Record `p_value`. Significance flag = (`p_value < 0.05`).  
2. **Speedup Calculation**: `speedup_mean = baseline_mean / domino_mean`. Compute 95 % CI.  
3. **Tolerance Check** (contextual only): Paper claim = 5.49×. Acceptable range = 5.49 × [0.8, 1.2] → [4.392, 6.588]. Set `tolerance_pass = (speedup_mean >= 4.392) && (speedup_mean <= 6.588)`.  
4. **Pass/Fail Logic** (aligned with FR‑007 and methodology):  

```
statistical_pass = (p_value < 0.05)
speedup_positive = (speedup_mean > 1.0)
pass_status = (statistical_pass && speedup_positive) ? "PASS" : "FAIL"
```

5. Generate `validation_report.md` via `src/validation/report_generator.py` containing:
   - Hardware context (`hardware.json`).  
   - Model substitution notes (`model_selection.json`).  
   - Speedup statistics, CI, `p_value`, `statistical_pass`, `speedup_positive`, `tolerance_pass`, and `pass_status`.  
   - Disclaimer about hardware differences.

## Phase 6 – Edge‑Case Handling

| Situation | Detection | Action |
|-----------|-----------|--------|
| Model OOM | `MemoryError`/`RuntimeError` during `from_pretrained` | Switch to next smaller model; abort with explicit `OUT_OF_MEMORY` if none remain. |
| CUDA import errors | `ImportError` on `bitsandbytes` | Ensure it is removed from `requirements-hf.txt`; reinstall CPU‑only `torch`. |
| Dependency download stalls | `pip install` fails | Retry up to 3 times with exponential backoff; abort with clear log on final failure. |
| Benchmark exceeds 45 min | `timeout` kills process | Record `status: failed` with `error_message: "Benchmark timeout after 45 min"` in `resource_log.json`. |
| Speedup ≤ 1.0 | Aggregation step | Record `speedup_mean` and note “No speedup observed on CPU; algorithmic benefit may be hardware‑dependent.” This does **not** cause a FAIL unless statistical significance is also lacking. |

## Constitution Check

The presence of `constitution.md` is verified in Phase 0. If absent, the pipeline aborts as a blocking issue (see Phase 0). This satisfies the Constitution Principle I requirement.

## Mapping of Requirements to Plan Elements

| Requirement | Covered In |
|-------------|-------------|
| FR‑001 | Phase 2 (Model Selection) & Phase 3 (benchmark execution). |
| FR‑002 | Phase 0 (CPU‑only install) & Phase 3 (timeout & resource monitor). |
| FR‑003 | Phase 3 (metrics generation) & Phase 4 (version logging). |
| FR‑004 | Phase 1 (hardware detection) & Phase 1.5 (device‑map config). |
| FR‑005 | Phase 3 (timeout wrapper). |
| FR‑006 | Phase 4 (library version capture). |
| FR‑007 | Phase 5 (statistical test, tolerance calculation, Pass/Fail logic). |
| SC‑001 | Phase 3 (timeout ≤ 45 min). |
| SC‑002 | Phase 3 (resource monitor, RAM assertion ≤ 6.5 GB). |
| SC‑003 | Phase 5 (speedup > 1, significance). |
| SC‑004 | Phase 5 (hardware description in report). |
| SC‑005 | Phase 1 (CPU‑only detection) & Phase 2 (fallback avoids CUDA). |
