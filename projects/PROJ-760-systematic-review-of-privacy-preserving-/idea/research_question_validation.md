## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about the interaction between data heterogeneity (non-IID skew) and the utility costs of two distinct privacy mechanisms (differential privacy vs. secure aggregation). It seeks to understand a phenomenon in distributed learning systems: how data distribution characteristics amplify specific types of privacy overhead. The question is independent of any specific model architecture or implementation method, focusing instead on the systemic behavior of the protocol under varying data conditions.

### Circularity check

**Verdict**: pass

The predictor variable (degree of data skew, controlled via Dirichlet $\alpha$) is an input parameter defining the data distribution. The predicted variables (utility costs, measured as accuracy degradation and convergence speed) are outputs derived from the training process under those conditions. These are independent sources: the skew is a property of the dataset partitioning, while the utility cost is a result of the optimization process under privacy constraints, ensuring no mechanical guarantee of the relationship.

### Triviality check

**Verdict**: pass

While it is generally known that non-IID data hurts FL convergence, the specific interaction with differential privacy (which adds noise) versus secure aggregation (which adds communication overhead) is not trivially predetermined. A result showing that DP's noise amplification is disproportionately worse under high skew than SecAgg's communication cost would be a novel, actionable insight for protocol selection. Conversely, a null result (that both scale similarly) would challenge the assumption that DP is uniquely sensitive to heterogeneity, making both outcomes scientifically informative.

### Question-narrowing check

**Verdict**: pass

The question names a specific domain relationship: the interaction between data skew and privacy mechanism efficacy. It does not frame the inquiry around whether a specific method can run within a specific budget, but rather asks *how* the system behaves under the interaction of these variables. The mention of "critical skew threshold" indicates a search for a domain-specific boundary condition rather than an implementation constraint.

### Overall verdict

**Verdict**: validated

The research question is well-posed, focusing on a substantive interaction between data distribution and privacy protocols without falling into implementation-narrowing or circularity traps. Both positive and null results would yield significant insights into the practical deployment of federated learning systems, making the project valuable for guiding protocol selection in heterogeneous environments.
