# Modeling Limitations and Future Directions

The current analytical pipeline applies standard regression techniques (linear, polynomial,
logarithmic) and residual‑family identification to the knot census dataset. These methods
are primarily **descriptive**, summarizing patterns that already exist in the curated data.
While this provides valuable insight into the structure and relationships within the
available census, it does not constitute **predictive modeling** that can forecast knot
complexity for unseen instances or guide the generation of new knot families.

We acknowledge this limitation explicitly in our documentation and outline future work
to develop more forward‑looking approaches, such as:

* **Supervised learning models** trained on invariant features to predict complexity
  metrics for novel knots.
* **Generative models** (e.g., graph neural networks) that can suggest candidate knots
  with targeted properties.
* **Cross‑validation and external validation** using independent knot datasets to assess
  predictive performance.

These extensions will move the analysis from a purely descriptive framework toward a
predictive one, enhancing the scientific impact of the project.

