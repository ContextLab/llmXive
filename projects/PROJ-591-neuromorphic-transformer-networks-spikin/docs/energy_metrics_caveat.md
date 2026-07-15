# Energy Metrics: CPU Proxy Caveat

## Overview

This document clarifies the methodology and limitations of energy consumption measurements
in the Neuromorphic Transformer Networks project (PROJ-591).

## The "CPU Proxy" Methodology

Due to hardware constraints (CPU-only execution environment), this project does not
measure actual physical power consumption via hardware sensors (e.g., RAPL, IPMI, or
specialized power meters). Instead, it employs a **CPU Proxy** estimation strategy
implemented in `code/metrics/energy_logger.py`.

### How It Works

1. **Wall-Clock Time Measurement**: The system measures the precise execution time
 of training and inference steps using `time.perf_counter()`.
2. **Baseline Power Assumption**: A fixed power coefficient (Watts) is applied to
 the elapsed time. This coefficient represents a standard TDP (Thermal Design Power)
 for the target CPU class (e.g., 65W for a typical server CPU).
3. **Calculation**:
 ```
 Energy (kWh) = (Elapsed_Time_seconds * Assumed_Power_Watts) / 3,600,000
 ```
4. **Fallback Logic**: If the `codecarbon` library fails to initialize or detect
 supported hardware, the system automatically falls back to this wall-clock
 estimation and sets the `is_estimated` flag to `True`.

## Critical Limitations

### 1. Not Physical Measurement
The values recorded in `data/processed/baseline_metrics.csv` and
`data/processed/spiking_metrics.csv` are **estimates**, not direct physical
measurements. They do not account for:
- Dynamic voltage and frequency scaling (DVFS)
- Actual CPU utilization percentages (idle vs.满载)
- Memory bus energy consumption
- Cooling overhead (PUE)

### 2. Relative Comparison Validity
While absolute energy values are approximate, the **relative comparison** between
the Baseline Transformer and the Spiking Transformer is valid for this study.
Since both models run on the same hardware, under the same workload conditions,
and with the same measurement methodology, the *difference* in energy consumption
reflects the architectural efficiency gains of the spiking approach.

### 3. Spiking Efficiency Context
The primary hypothesis is that spiking neural networks (SNNs) reduce energy by
utilizing sparse activation (fewer spikes). Even with a CPU proxy, the reduction
in floating-point operations (FLOPs) and memory access patterns in the spiking
model should correlate with lower estimated energy usage.

## Reporting Standards

All generated reports (e.g., `data/results/statistical_analysis_report.md`) must
explicitly state:
> "Energy metrics are derived via a CPU proxy estimation (wall-clock time × fixed
> power coefficient) due to the lack of direct hardware power sensing in the
> execution environment. Values are marked as 'estimated' in the data files."

## Implementation Reference

- **Source Code**: `code/metrics/energy_logger.py`
- **Key Function**: `estimate_energy_from_time()`
- **Data Flag**: `is_estimated` (boolean) in `EnergyRecord` dataclass
- **Fallback Trigger**: `codecarbon` initialization failure or unsupported hardware

## Future Improvements

To transition from "Proxy" to "Physical" measurement:
1. Deploy on hardware with RAPL (Running Average Power Limit) support.
2. Integrate `codecarbon` with actual power meter APIs.
3. Update `requirements.txt` to include `rapl` or `pyrapl` dependencies.
4. Modify `EnergyLogger` to read from `/sys/class/powercap/intel-rapl/` on Linux.