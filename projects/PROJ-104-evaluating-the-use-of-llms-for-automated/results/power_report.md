# Power Analysis Report (T002)

Monte‑Carlo power analysis for the Friedman test comparing
fidelity scores across the three LLM architectures (FR‑005,
SC‑004). This operationalises the specification's assumption
about statistical validity: if power is low, downstream results
are framed as exploratory associations rather than definitive
claims.

## Design

- Test: Friedman test (three paired models), alpha = 0.05
- Target effect: medium, Cohen's f = 0.25
- Within‑subject correlation: 0.5
- Paired samples: n = 500
- Monte‑Carlo replicates: 1000
- Pinned seed: 42 (Constitution I, ``code.seeds``)

## Result

- estimated_power_n500: 1.0000
- exploratory: false

## Interpretation

Estimated power (1.0000) meets or exceeds the 0.8 convention, so the planned sample size is adequate to detect a medium effect; results need not be framed as exploratory on power grounds.
