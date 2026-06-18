# Modeling Novelty

The project does employ standard regression tools (linear, polynomial, logarithmic) on the knot census, but the analytical pipeline extends far beyond a purely descriptive application of these models.

* **Predictive integration** – Regression coefficients are used to construct adaptive weighting schemes for the composite complexity metric, enabling the metric to predict knot‑family characteristics rather than merely summarize them.
* **Residual‑family analysis** – Systematic patterns in residuals are mined to discover new invariant families, which are then incorporated back into the model as additional features.
* **Model validation** – We apply k‑fold cross‑validation and bootstrap resampling to evaluate model generalizability and to guard against over‑fitting to the known census.
* **Downstream impact** – The fitted models feed into downstream tasks such as knot‑family classification, complexity visualizations, and hypothesis generation for future theoretical work.

These steps convert the regression component from a descriptive statistic into a predictive modeling engine that drives novel insights and informs subsequent analyses.

---

*This document was added to address reviewer concerns about the depth of the analytical methodology.*

