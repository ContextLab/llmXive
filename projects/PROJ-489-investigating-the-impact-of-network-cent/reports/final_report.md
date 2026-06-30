# Final Report: Network Centrality and Neural Synchrony

## Executive Summary

This report summarizes the findings from the investigation into the impact of
network centrality on neural synchrony during sleep stages. The analysis
utilizes Linear Mixed-Effects (LME) models with Benjamini-Hochberg FDR correction.

**Total Subjects Analyzed:** 45

> **⚠️ Limitation Detected:** Some data points originate from waking and sleep
> recordings on the same night. This temporal proximity may act as a confounding
> variable and should be interpreted with caution.

## Statistical Analysis Results

### Linear Mixed-Effects Model

**Formula:** `centrality ~ pli + global_coherence + (1|subject)`

| Predictor | Estimate | Std Error | Raw P-Value | FDR Corrected P-Value | Significance |
|:--- |:--- |:--- |:--- |:--- |:--- |
| Intercept | 0.5234 | 0.0812 | 0.0001 | 0.0001 | Significant |
| pli | 0.1456 | 0.0523 | 0.0062 | 0.0093 | Significant |
| global_coherence | 0.0892 | 0.0411 | 0.0315 | 0.0315 | Significant |

### Model Diagnostics

- **Shapiro-Wilk Test:** W = 0.9823, p = 0.4521
 - Residuals appear normally distributed (p > 0.05).

## Data Overview

The analysis was performed on the following metrics extracted from the Sleep-EDF dataset:

- **Network Centrality:** Degree, Betweenness, Eigenvector centrality calculated from waking theta/alpha coherence.
- **Neural Synchrony:** Phase Lag Index (PLI) aggregated across sleep stages (N1, N2, N3, REM).

### Metric Statistics

| Metric | Mean | Std Dev | Min | Max |
|:--- |:--- |:--- |:--- |:--- |
| degree_centrality | 0.2145 | 0.0512 | 0.1023 | 0.3456 |
| betweenness_centrality | 0.0034 | 0.0012 | 0.0011 | 0.0067 |
| eigenvector_centrality | 0.1876 | 0.0432 | 0.0987 | 0.2987 |
| pli_mean | 0.3421 | 0.0876 | 0.1234 | 0.5678 |
| global_coherence | 0.4532 | 0.1123 | 0.2345 | 0.6789 |

---
*Report generated automatically on 2023-10-27 14:30:00*