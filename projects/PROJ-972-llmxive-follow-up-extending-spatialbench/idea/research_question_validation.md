## Research-question validation

### Phenomenon-vs-method check

**Verdict**: concern

The question asks whether a specific training strategy (adapter on failure modes) yields robust generalization, which is a substantive scientific question about data efficiency and curriculum learning in spatial intelligence. However, it is heavily fixated on the implementation constraint of "parameter-efficient adapter" and the specific mechanism of "contrastive loss on failure modes," which risks narrowing the inquiry to a specific engineering recipe rather than the broader phenomenon of how failure-case curation drives generalization. The core scientific question is valid, but the framing leans too heavily on the specific method (adapter) rather than the principle of targeted curation.

### Circularity check

**Verdict**: pass

The predictor (the model's performance after training on failure modes) and the predicted variable (generalization on unseen tasks from the same benchmark suite) rely on distinct data sources: the training data is a curated subset of the original benchmark's failure cases, while the evaluation data is the held-out "unseen" portion of the test suite. Since the evaluation tasks are explicitly defined as "unseen" and distinct from the training subset, the relationship is not mechanically guaranteed by construction.

### Triviality check

**Verdict**: pass

A positive result (failure-case training achieves parity with full fine-tuning) would be highly informative, suggesting that data quality (targeting errors) can substitute for data quantity in spatial reasoning. Conversely, a null result (failure-case training fails to generalize) would also be publishable, as it would indicate that spatial robustness requires broad exposure to diverse scenarios rather than just correcting specific errors. Neither outcome is predetermined by current domain knowledge.

### Question-narrowing check

**Verdict**: concern

The question names a relationship (failure-case training → generalization) but immediately constrains it with specific implementation details ("parameter-efficient adapter," "contrastive loss," "CPU feasibility") that are not central to the scientific phenomenon. A more robust domain question would ask "Does targeted curation of failure cases improve generalization in spatial foundation models?" without binding the answer to a specific architecture or hardware constraint, which are better suited for the methodology section.

### Overall verdict

**Verdict**: validator_revise

[REVISED]
Does training exclusively on identified failure modes of spatial foundation models yield robust generalization on unseen embodied and egocentric tasks comparable to training on a random subset of equivalent size?
[/REVISED]
The reframing removes the specific architectural constraints (adapter, contrastive loss, CPU) and the "parameter-efficient" label, focusing instead on the core scientific hypothesis: whether the *content* of the training data (failure modes vs. random) drives generalization better than quantity alone, allowing the methodology to remain flexible.
