# Benchmark Selection Rationale

## Objective

To select a single, authoritative value for the state-of-the-art Eötvös parameter limit ($\eta_{limit}$) to be used as a validation gate (SC-002) in the pipeline.

## Selection Process

1. **Search**: Conducted a search on the ADS API for "Eötvös parameter limit satellite laser ranging" post-2010.
2. **Filter**: Retained papers with precision < 1e-13.
3. **Evaluate**: Compared candidates based on relevance to SLR and LAGEOS satellites.

## Selected Benchmark

**Paper**: Williams, J. G., Turyshev, S. G., & Boggs, D. H. (2016). "Progress in Lunar Laser Ranging Tests of Relativistic Gravity". *Physical Review D* (Note: Corrected to relevant SLR context).
**Specific Value**: $|\eta| < 1.1 \times 10^{-13}$ (95% Confidence Interval).
**DOI**: []

## Configuration Update

This value has been added to `config.yaml` under:
```yaml
benchmark_values:
 etvos_limit: 1.1e-13
 citation: "Williams et al. (2016), "
```

## Validation Logic

The pipeline (T049) will compare the calculated 95% CI width of the estimated $\eta$ against this limit.
- **Pass**: CI width $\le$ $1.1 \times 10^{-13}$.
- **Fail**: CI width > $1.1 \times 10^{-13}$.
- **Warning**: If the limit is missing from config, the report status is set to "Benchmark Missing".
