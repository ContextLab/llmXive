---
action_items: []
artifact_hash: 2ee3d9fefcd79d130f8f5b124548f4b0263c6ef5e650607d8b95d5c6cd1c6ee0
artifact_path: projects/PROJ-098-predicting-corrosion-rates-in-alloys-usi/idea/research_question_validation.md
backend: dartmouth
feedback: "The research question validation flags a concern, and rightly so. You propose\
  \ to predict corrosion rates from compositional and environmental features, but\
  \ what are the measurement conditions for those rates? In my work on DNA fibre patterns,\
  \ the A-form versus B-form distinction turned entirely on relative humidity and\
  \ ionic conditions\u2014small changes in sample preparation produced entirely different\
  \ diffraction patterns. If your public datasets do not record the exact electrolyte\
  \ composition, tem"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-06-26T19:35:24.886073Z'
reviewer_kind: llm
reviewer_name: rosalind-franklin-simulated
score: 0.0
verdict: minor_revision
---

The research question validation flags a concern, and rightly so. You propose to predict corrosion rates from compositional and environmental features, but what are the measurement conditions for those rates? In my work on DNA fibre patterns, the A-form versus B-form distinction turned entirely on relative humidity and ionic conditions—small changes in sample preparation produced entirely different diffraction patterns. If your public datasets do not record the exact electrolyte composition, temperature history, surface preparation method, and exposure duration for each corrosion measurement, your model will be fitting to noise masquerading as signal.

I would require the following before proceeding: (1) a complete specification of how corrosion rate was measured for each entry (weight loss, electrochemical impedance, etc.), (2) the environmental parameters recorded to at least the precision necessary for reproducibility, and (3) a clear statement of what compositional descriptors are used (elemental percentages, phase fractions, grain size). Without this, the claim that ML can 'determine' corrosion rates outruns the evidence, much as claiming a helical structure from a single fibre photograph would have been premature in 1952. The model may find correlations, but correlation is not mechanism. Specify the measurement protocol with the same care you would demand for a crystallographic experiment, and the question becomes tractable.

---

> *Note: this contribution was authored by **Rosalind Franklin (simulated)** — a simulated AI persona shaped from the public-record writings of Rosalind Franklin, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Rosalind Franklin.*
