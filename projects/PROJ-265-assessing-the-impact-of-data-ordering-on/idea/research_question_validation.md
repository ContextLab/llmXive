## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about a statistical phenomenon: how temporal autocorrelation (a data property) affects bootstrap coverage probability (an inferential property). This is independent of any specific implementation method or computational constraint.

### Circularity check

**Verdict**: pass

The predictor (temporal autocorrelation strength, measured from the data generation process) and predicted variable (coverage probability, measured from the resampling procedure) are derived from independent sources. The autocorrelation characterizes the data, while coverage is measured from the bootstrap resampling—no mechanical guarantee exists between them.

### Triviality check

**Verdict**: concern

The general principle that autocorrelation violates bootstrap exchangeability assumptions is theoretically established in statistics literature. However, the specific quantitative mapping between autocorrelation strength and coverage degradation may represent an empirical gap. A null result would contradict established theory, but the quantitative characterization could still be informative for practitioners.

### Question-narrowing check

**Verdict**: pass

Names a domain relationship (temporal autocorrelation → coverage bias) rather than an implementation constraint. The question is about statistical behavior, not whether a specific method works within budget or runtime limits.

### Overall verdict

**Verdict**: validated

All four checks pass or show only minor concerns that don't undermine the core question. The project addresses a genuine empirical gap in quantifying how much standard bootstrap coverage degrades at different autocorrelation levels, which could inform practitioner decision-making about when to use block bootstrap versus standard resampling.
