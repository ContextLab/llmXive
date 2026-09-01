# Technical Design Document

## Window Length Justification
The default short-duration window is statistically invalid for the Schaefer 200 atlas due to rank deficiency and insufficient time points for stable correlation estimation. A 60s window is mandated by FR-003 to ensure robust metric stability.

## Null Model Selection
AR-surrogates were rejected in favor of phase-shuffling as mandated by FR-008. Phase-shuffling preserves the power spectrum while destroying temporal structure, providing a more appropriate null model for dynamic connectivity analysis.

## Artifact Schema Override
The Plan's definition of `final_results.csv` containing `Variability_Component_1...N` is incorrect. The Spec's single `Variability_Metric` (mean edge SD) schema is the authoritative source.
