## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about the statistical properties (Type I error control and power) of standard parametric tests when data are contaminated, and whether robust estimators improve these properties. It is a substantive scientific inquiry about the behavior of inference procedures, independent of any particular implementation detail.

### Circularity check

**Verdict**: pass

The predictor (level/type of data contamination) and the predicted variables (empirical Type I error rates and power) are derived from separate aspects of the simulation study. Contamination is an external manipulation, while error rates and power are outcome metrics; they are not mechanically linked.

### Triviality check

**Verdict**: pass

Both possible outcomes are informative: if standard tests remain reliable, that supports their continued use; if they fail and robust alternatives succeed, that provides actionable guidance for practitioners. Neither outcome is predetermined by existing domain knowledge.

### Question-narrowing check

**Verdict**: pass

The question frames a domain-level relationship (“how do tests behave under contamination?”) rather than a constraint on a specific algorithm’s implementation or computational budget.

### Overall verdict

**Verdict**: validated
