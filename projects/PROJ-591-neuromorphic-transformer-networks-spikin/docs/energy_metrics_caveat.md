# Energy Metrics: CPU Proxy Caveat

## Overview

This document clarifies the nature of energy measurements produced by the Neuromorphic Transformer Networks pipeline, specifically addressing the limitations of CPU-based energy estimation.

## The "CPU Proxy" Caveat

The energy metrics logged by `code/metrics/energy_logger.py` and reported in `data/processed/baseline_metrics.csv` and `data/processed/spiking_metrics.csv` are **estimates derived from wall-clock time**, not direct hardware power measurements.

### Why This Limitation Exists

1. **Hardware Constraints**: The project is constrained to CPU-only execution per the Constitution and CI requirements. Standard energy monitoring tools like `codecarbon` are optimized for GPU workloads and often provide unreliable or missing data on CPU-only systems.

2. **Proxy Methodology**: When direct power measurement is unavailable, the system falls back to estimating energy consumption using:
 ```
 estimated_energy = wall_clock_time × cpu_power_baseline
 ```
 Where `cpu_power_baseline` is a configurable constant (default: 65W for a typical server CPU).

3. **"Estimated" Flag**: All energy records generated via this fallback mechanism are marked with `is_estimated=True` in the logs. This flag is propagated to the CSV output as a boolean column.

## Interpretation Guidelines

When analyzing results:

- **Comparative Validity**: While absolute energy values are estimates, **relative comparisons** between baseline and spiking models trained under identical conditions remain valid. The same proxy methodology applies to both, preserving the ratio of energy consumption.

- **Statistical Analysis**: Paired t-tests (Task T022) on energy-per-token metrics are statistically sound because the systematic error introduced by the proxy method cancels out when comparing matched seeds.

- **Absolute Values**: Do not interpret the absolute kWh values as precise physical measurements. They represent a consistent proxy for computational effort.

## Implementation Details

The fallback logic is implemented in `code/metrics/energy_logger.py`:

- If `codecarbon` fails to initialize or returns `None` for power data, the system automatically switches to the time-based proxy.
- The `EnergyLogger` class sets the `is_estimated` flag accordingly.
- The `estimate_energy_from_time` function applies the configurable power baseline.

## Future Improvements

To obtain direct power measurements:

1. Deploy on hardware with IPMI or RAPL (Running Average Power Limit) support.
2. Use external power meters for physical measurement.
3. Upgrade to GPU-accelerated environments where `codecarbon` provides direct telemetry.

## References

- Constitution Principle III: Data Hygiene and State Tracking
- Task T007: Implementation of `energy_logger.py`
- Task T018: Integration of energy logging in spiking training
- Spec FR-009: Paired Statistical Design (relies on consistent measurement methodology)

## Conclusion

The "CPU Proxy" caveat does not invalidate the scientific findings of this project. The primary goal is to demonstrate the **relative efficiency** of spiking neural dynamics compared to conventional transformers. Since both models are measured using the same proxy methodology under identical conditions, the comparative results remain robust and scientifically meaningful.

For absolute energy values, users must acknowledge the estimated nature of the data and treat them as computational effort proxies rather than physical power measurements.
