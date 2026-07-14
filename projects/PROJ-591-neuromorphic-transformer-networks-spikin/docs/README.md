# Documentation Index

## Overview

This directory contains supplementary documentation for the Neuromorphic Transformer Networks project.

## Documents

- [Energy Metrics Caveat](energy_metrics_caveat.md): Detailed explanation of the CPU-based energy estimation methodology and its implications for result interpretation.

## Related Artifacts

- `code/metrics/energy_logger.py`: Implementation of energy logging with fallback logic.
- `data/processed/baseline_metrics.csv`: Baseline model results with energy estimates.
- `data/processed/spiking_metrics.csv`: Spiking model results with energy estimates.
- `data/results/statistical_analysis_report.md`: Final report including energy comparison analysis.

## Quick Reference

### Key Questions

- **Are the energy values real measurements?**
 No, they are estimates derived from wall-clock time when running on CPU-only systems. See [Energy Metrics Caveat](energy_metrics_caveat.md).

- **Can I trust the comparison between baseline and spiking models?**
 Yes. The same estimation methodology is applied to both models, preserving the validity of relative comparisons and statistical tests.

- **How do I get real power measurements?**
 Run the pipeline on hardware with direct power telemetry (IPMI, RAPL, or GPU with codecarbon support).

### Usage

When citing results from this project, please include the following disclaimer:

> "Energy metrics are estimated using a time-based proxy methodology due to CPU-only execution constraints. While absolute values are approximations, relative comparisons between models remain valid."