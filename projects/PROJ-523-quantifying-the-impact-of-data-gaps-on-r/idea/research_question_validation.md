## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about the physical relationship between observational data artifacts (gaps) and the accuracy of physical inference (cosmological parameters). It is independent of any specific gap-filling method's performance, as the methodology compares multiple algorithms to isolate the systematic effect.

### Circularity check

**Verdict**: pass

The predictor (gap characteristics) is an imposed input on simulated data, while the predicted variable (parameter bias) is calculated by comparing recovered parameters against independent ground-truth values from unmasked simulations. There is no mechanical guarantee of the relationship because the bias depends on the interaction between the gap morphology and the filling algorithm, not a shared signal source.

### Triviality check

**Verdict**: pass

While masking effects on power spectra are known, quantifying the specific propagation to cosmological parameters (H₀, Ωₘ) as a function of gap morphology is not predetermined by domain knowledge. Either a significant bias scaling law or a demonstration of robustness against specific gap types would provide actionable constraints for future survey designs.

### Question-narrowing check

**Verdict**: pass

The question explicitly names a domain relationship (data gap characteristics vs. parameter recovery bias) rather than a constraint on implementation resources or specific algorithmic performance. It frames the investigation around the scientific impact of data processing choices on physical conclusions.

### Overall verdict

**Verdict**: validated

All checks pass; the research question addresses a substantive gap in systematic error quantification for CMB experiments without relying on method-evaluation framing or circular logic. The project is ready to advance to initialization.
