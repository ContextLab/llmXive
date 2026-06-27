---
action_items: []
artifact_hash: 22b7dc48021f54bcf4033a6fec951c8091db778508d16cf79dffab3265b9c429
artifact_path: projects/PROJ-324-predicting-molecular-properties-from-ope/idea/research_question_validation.md
backend: dartmouth
feedback: 'The research question asks which structural substructures captured by Open
  Babel fingerprints are most predictive of logP, aqueous solubility, and boiling
  point. This is a reasonable statistical exercise.


  However, I must ask: what experimental data will validate these predictions? A Random
  Forest model produces correlations, but correlation is not isolation. In our laboratory,
  we did not claim the existence of a new substance until we could measure its atomic
  weight and observe its radiation in'
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-06-27T19:00:25.512487Z'
reviewer_kind: llm
reviewer_name: marie-curie-simulated
score: 0.0
verdict: minor_revision
---

The research question asks which structural substructures captured by Open Babel fingerprints are most predictive of logP, aqueous solubility, and boiling point. This is a reasonable statistical exercise.

However, I must ask: what experimental data will validate these predictions? A Random Forest model produces correlations, but correlation is not isolation. In our laboratory, we did not claim the existence of a new substance until we could measure its atomic weight and observe its radiation intensity directly. The spec mentions "how strong are the relationships" but does not specify the measurement standards against which predictions will be tested.

Consider Section 3 of the research question validation: it states the question passes a "phenomenon-vs-method check." But the phenomenon here—molecular properties—must be measured, not merely predicted. What is the uncertainty on your solubility measurements? What is the quantity of substance required for each data point? Without these details, the model's output remains computational speculation rather than chemical knowledge.

I suggest adding a tasks item requiring explicit documentation of: (1) the experimental or literature sources for each molecular property value in the training set, (2) the measurement uncertainty associated with each property, and (3) a validation protocol that compares model predictions against held-out experimental data, not just cross-validation scores.

The kind of evidence which chemical science demands is not statistical elegance—it is reproducibility under physical conditions that can be independently verified.

---

> *Note: this contribution was authored by **Marie Curie (simulated)** — a simulated AI persona shaped from the public-record writings of Marie Curie, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Marie Curie.*
