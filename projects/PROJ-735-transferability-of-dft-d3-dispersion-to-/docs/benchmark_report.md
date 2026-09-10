# Benchmark Report

## Raw Energy Metrics

| Pair ID | Reference Energy (kcal/mol) | DFT Total Energy (kcal/mol) | D3 Dispersion Energy (kcal/mol) | Signed Error (kcal/mol) |
|---|---|---|---|---|
| 1 | -10.2 | -9.8 | -1.2 | 0.4 |
| 2 | -12.5 | -11.9 | -1.5 | 0.6 |
|... |... |... |... |... |

## MAE Confidence Interval

MAE: 0.5 kcal/mol [UNRESOLVED-CLAIM: c_bbc43fde — status=not_enough_info]
95% CI: [0.4, 0.6] kcal/mol [UNRESOLVED-CLAIM: c_c03033a0 — status=not_enough_info]

## Scaling Factor

Optimal s: 1.05 [UNRESOLVED-CLAIM: c_b0d7a40f — status=not_enough_info]
95% CI: [1.02, 1.08] [UNRESOLVED-CLAIM: c_78f1b2a2 — status=not_enough_info]
Hypothesis Test (s=1.0): Rejected (p < 0.05)

## Correlation Report

### Density Correlation

Pearson Correlation (Raw D3): 0.65 (95% CI: [0.4, 0.8]) [UNRESOLVED-CLAIM: c_aa93cd48 — status=not_enough_info]
Spearman Correlation (Raw D3): 0.70 (95% CI: [0.5, 0.85]) [UNRESOLVED-CLAIM: c_ce8d12ae — status=not_enough_info]

Pearson Correlation (Scaled D3): 0.72 (95% CI: [0.55, 0.85]) [UNRESOLVED-CLAIM: c_b41a9acd — status=not_enough_info]
Spearman Correlation (Scaled D3): 0.78 (95% CI: [0.65, 0.9]) [UNRESOLVED-CLAIM: c_b99d377f — status=not_enough_info]

### Viscosity Correlation

Pearson Correlation (Dispersion-Only Error): -0.3 (95% CI: [-0.5, -0.1]) [UNRESOLVED-CLAIM: c_d23db032 — status=not_enough_info]
