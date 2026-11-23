# Scientific Principles

## Principle V: Versioning
All artifacts are versioned via `state.yaml`. This ensures reproducibility and traceability of all data and model outputs.

## Principle VI: Distinct Stimulus Set Validation
Primes and targets are stored in separate directories and validated to ensure they are never merged prematurely. This prevents data leakage and maintains the integrity of the experimental design.

## Principle VII: Human-Rated Ambiguity
Ambiguity scores for social stimuli are strictly human-rated. Synthetic derivation is prohibited to ensure the validity of the analysis.

## Principle VIII: Associational Analysis
All findings are framed as associational. The system explicitly avoids causal claims to reflect the observational nature of the data.

## Principle IX: Data Integrity
The system halts if data quality thresholds are not met (e.g., >10% missing images, <90% linkage). This ensures that only high-quality data is used for analysis.
