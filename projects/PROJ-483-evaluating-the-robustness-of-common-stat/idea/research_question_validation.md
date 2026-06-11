## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about a substantive statistical phenomenon: how the inferential properties of classical tests (Type I error control, power) behave when their core independence assumption is violated. This is a domain question about the behavior of statistical methods under realistic data conditions, not an implementation question about whether a specific algorithm runs within a particular resource budget.

### Circularity check

**Verdict**: pass

The predictor (dependency strength, controlled via block bootstrap/AR(1)/spatial kernel resampling) is independently manipulated from the predicted variable (observed Type I error rates and power from test p-values). The dependency structure is injected by design, and the test outcomes are measured empirically—no mechanical guarantee exists between them.

### Triviality check

**Verdict**: pass

Either outcome is informative: if tests remain robust to moderate dependency, this provides practical reassurance to applied researchers; if Type I error inflates substantially, this warns against uncritical use of standard tests on public data. Both results would be publishable given the identified literature gap on empirical robustness evidence.

### Question-narrowing check

**Verdict**: pass

The question names a domain relationship (test error rates as a function of dependency strength) rather than an implementation constraint. The 6-hour GHA runtime mentioned in methodology is a project constraint, not part of the research question itself.

### Overall verdict

**Verdict**: validated

All four checks pass. The research question is well-formed, targeting a genuine gap in empirical statistical methodology literature. The question is independent of any specific software implementation, has no circularity in its design, and both positive and null results would be scientifically informative.
