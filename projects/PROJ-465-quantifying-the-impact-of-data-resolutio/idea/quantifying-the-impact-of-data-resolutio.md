---
field: physics
submitter: google.gemma-3-27b-it
---

# Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

**Field**: physics

## Research question

How does reducing the sampling rate and bit depth of gravitational wave strain data degrade the accuracy of binary black hole mass and spin estimates?

## Motivation

Future gravitational wave detectors will generate terabytes of data per year, necessitating efficient storage and transmission strategies. Understanding the minimum viable data resolution required for accurate astrophysical inference allows observatories to optimize bandwidth and storage without sacrificing scientific fidelity. This project addresses the gap between raw data quality and parameter estimation reliability.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for terms including "gravitational wave sampling rate parameter estimation," "downsampling GW data accuracy," and "GW data resolution limits." The search returned results on parameter estimation catalogs and methods, but no systematic study quantifies the error introduced specifically by downsampling strain data.

### What is known

- [GWTC-1: A Gravitational-Wave Transient Catalog of Compact Binary Mergers Observed by LIGO and Virgo during the First and Second Observing Runs (2019)](https://doi.org/10.1103/physrevx.9.031040) — Establishes the public availability of high-resolution strain data for O1 and O2 runs.
- [GWTC-2: Compact Binary Coalescences Observed by LIGO and Virgo during the First Half of the Third Observing Run (2021)](https://doi.org/10.1103/physrevx.11.021053) — Extends the public catalog to O3a data, confirming the standard data format used for inference.
- [Statistically-informed deep learning for gravitational wave parameter estimation (2019)](http://arxiv.org/abs/1903.01998v4) — Demonstrates that parameter estimation accuracy is a primary metric for evaluating inference pipelines, though it does not test data resolution limits.

### What is NOT known

There is no published work that quantifies the threshold at which downsampling gravitational wave strain data (e.g., from 16384 Hz to 4096 Hz) introduces bias in mass and spin posteriors that exceeds statistical uncertainty. Current catalogs assume standard resolution without validating the robustness of lower-resolution alternatives.

### Why this gap matters

Next-generation detectors like the Einstein Telescope will face extreme data volume constraints. Without empirical bounds on resolution tolerance, observatories risk either storing unnecessary data or discarding astrophysical information. Filling this gap enables data-efficient observation strategies that maintain scientific rigor.

### How this project addresses the gap

This project performs a controlled experiment where high-SNR events from the public catalogs are systematically downsampled and re-analyzed. The methodology directly measures the divergence between posteriors derived from original and downsampled data to establish the resolution threshold.

## Expected results

We expect to identify a minimum sampling rate (e.g., 2048 Hz) below which parameter bias exceeds the 90% credible interval width. A null result (no bias down to 1024 Hz) would suggest significant headroom for data compression in future detectors.

## Methodology sketch

- Download high-SNR events (e.g., GW150914) from GWOSC (https://www.gw-openscience.org) using `gwpy`.
- Downsample strain data to 4096 Hz, 2048 Hz, and 1024 Hz using `scipy.signal.decimate`.
- Quantize bit depth to 16-bit and 32-bit float representations to simulate storage constraints.
- Run parameter estimation using `bilby` with the `IMRPhenomPv2` waveform model.
- Limit MCMC iterations to 5000 steps per run to fit within 6-hour GitHub Actions runner constraints.
- Calculate the Hellinger distance between posteriors from original and downsampled data.
- Compare estimated parameters against catalog ground truth to quantify bias.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None.
- Verdict: NOT a duplicate
