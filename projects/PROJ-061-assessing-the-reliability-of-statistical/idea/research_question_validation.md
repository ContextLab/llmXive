## Research-question validation

### Phenomenon-vs-method check
**Verdict**: pass

The question asks about the relationship between specific data properties (violations of normality, independence) and the accuracy of statistical theory in predicting detectability. This is a substantive inquiry into the robustness of statistical methodology against real-world conditions, rather than a query about whether a specific software implementation or hardware constraint can perform a calculation.

### Circularity check
**Verdict**: pass

The predictor (assumption violation type and magnitude) is introduced as a controlled perturbation to the data, while the predicted variable (bias in power calculation) is derived by comparing a theoretical formula against an empirical frequency estimated via bootstrapping. These are distinct computational procedures: one generates the ground truth via resampling, and the other applies a closed-form approximation, ensuring the relationship is not mechanically guaranteed by a shared signal source.

### Triviality check
**Verdict**: pass

Both a positive result (showing specific violations cause large, predictable biases) and a null result (showing standard power calculations are surprisingly robust to common violations) would be highly informative. A confirmation of bias would necessitate new correction factors for study design, while a null result would validate the continued use of standard tools despite non-ideal data, resolving a significant ambiguity in the field.

### Question-narrowing check
**Verdict**: pass

The question explicitly names relationships in the statistical domain (the interaction between distributional assumptions and detectability estimation) rather than focusing on implementation constraints like runtime, memory, or specific library performance. It asks "how does X affect Y" where X and Y are theoretical concepts, not engineering limits.

### Overall verdict
**Verdict**: validated

All four checks pass; the research question is a well-defined inquiry into the empirical validity of statistical theory under realistic conditions. The project avoids circularity by using bootstrapping as an independent ground truth and addresses a genuine gap regarding the quantification of bias in power analysis. The question is broad enough to yield publishable insights regardless of the direction of the findings.
