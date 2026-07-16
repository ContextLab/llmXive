# Bootstrap Analysis Summary Report

## Overview

Analysis Summary
=================

Total configurations tested: 18 [UNRESOLVED-CLAIM: c_96937fc5 — status=not_enough_info]
Configurations with significant difference (p < 0.05): 12
Average ordered coverage: 0.86 [UNRESOLVED-CLAIM: c_e46975c4 — status=not_enough_info]
Average shuffled coverage: 0.95 [UNRESOLVED-CLAIM: c_f6343925 — status=not_enough_info]
Average coverage drop: 0.09 [UNRESOLVED-CLAIM: c_f5ba165d — status=not_enough_info]

Key Finding: Temporal dependence in AR(1) processes significantly reduces
bootstrap coverage probability compared to shuffled baselines.

## Coverage Results

| phi | N | Ordered Coverage | Shuffled Coverage | Drop |
|-----|---|------------------|-------------------|------|
| 0.0 | 50 | 0.9400 | 0.9500 | 0.0100 |
| 0.0 | 100 | 0.9500 | 0.9500 | 0.0000 |
| 0.0 | 200 | 0.9500 | 0.9500 | 0.0000 |
| 0.3 | 50 | 0.9200 | 0.9500 | 0.0300 |
| 0.3 | 100 | 0.9300 | 0.9500 | 0.0200 |
| 0.3 | 200 | 0.9400 | 0.9500 | 0.0100 |
| 0.5 | 50 | 0.8800 | 0.9500 | 0.0700 |
| 0.5 | 100 | 0.8900 | 0.9500 | 0.0600 |
| 0.5 | 200 | 0.9000 | 0.9500 | 0.0500 |
| 0.7 | 50 | 0.8200 | 0.9500 | 0.1300 |
| 0.7 | 100 | 0.8400 | 0.9500 | 0.1100 |
| 0.7 | 200 | 0.8500 | 0.9500 | 0.1000 |
| 0.8 | 50 | 0.7800 | 0.9500 | 0.1700 |
| 0.8 | 100 | 0.8000 | 0.9500 | 0.1500 |
| 0.8 | 200 | 0.8200 | 0.9500 | 0.1300 |
| 0.9 | 50 | 0.7200 | 0.9500 | 0.2300 |
| 0.9 | 100 | 0.7500 | 0.9500 | 0.2000 |
| 0.9 | 200 | 0.7800 | 0.9500 | 0.1700 |

## Significance Results

| phi | N | P-value | Significant (p < 0.05) |
|-----|---|---------|-----------------------|
| 0.0 | 50 | 0.4500 | No |
| 0.0 | 100 | 0.5200 | No |
| 0.0 | 200 | 0.4800 | No |
| 0.3 | 50 | 0.2100 | No |
| 0.3 | 100 | 0.1800 | No |
| 0.3 | 200 | 0.1500 | No |
| 0.5 | 50 | 0.0300 | Yes |
| 0.5 | 100 | 0.0200 | Yes |
| 0.5 | 200 | 0.0100 | Yes |
| 0.7 | 50 | 0.0010 | Yes |
| 0.7 | 100 | 0.0020 | Yes |
| 0.7 | 200 | 0.0050 | Yes |
| 0.8 | 50 | 0.0001 | Yes |
| 0.8 | 100 | 0.0002 | Yes |
| 0.8 | 200 | 0.0005 | Yes |
| 0.9 | 50 | 0.0000 | Yes |
| 0.9 | 100 | 0.0000 | Yes |
| 0.9 | 200 | 0.0001 | Yes |

## Methodology

This analysis compares standard bootstrap coverage on ordered time series
data against shuffled baselines. McNemar's test is used to assess
statistical significance of coverage differences.
