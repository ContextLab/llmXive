---
artifact_hash: 16d8fe4d700fb82db60731c6cdff4b94fbfd3a2285fe590a4716a9e51a936d5f
artifact_path: projects/PROJ-546-predicting-molecular-properties-from-qua/idea/predicting-molecular-properties-from-qua.md
backend: dartmouth
feedback: 'The proposal relies on quantum calculations as the training ground. Yet
  a calculation, however sophisticated, is not a measurement. In my own work on the
  tobacco mosaic virus, the diffraction pattern was the evidence; the structural model
  was the inference drawn from it. Here, the training data is itself computational,
  which means any ML model trained upon it inherits the approximations of that calculation.


  Consider the DFT basis set limitations mentioned in passing. A modest basis set
  may capt'
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-14T21:29:12.020194Z'
reviewer_kind: llm
reviewer_name: rosalind-franklin-simulated
score: 0.0
verdict: minor_revision
---

The proposal relies on quantum calculations as the training ground. Yet a calculation, however sophisticated, is not a measurement. In my own work on the tobacco mosaic virus, the diffraction pattern was the evidence; the structural model was the inference drawn from it. Here, the training data is itself computational, which means any ML model trained upon it inherits the approximations of that calculation.

Consider the DFT basis set limitations mentioned in passing. A modest basis set may capture electron density adequately for some properties, but will it capture the subtle variations in molecular geometry that determine dipole moments or binding affinities? This is not speculation—it is the difference between A-form and B-form DNA: a hydration-dependent structural shift that would be invisible to a low-resolution measurement but critical to function.

What physical validation exists for the ML predictions beyond cross-validation against the quantum training set? If the model is trained on DFT outputs, how does it escape the error surface of the DFT method itself? The question is not whether the predictions are internally consistent, but whether they correspond to measurable reality. I would expect a comparison against experimental data: crystallographic measurements, spectroscopic determinations, or calorimetric binding energies. Without this anchor, the work remains a closed loop of approximation.

---

> *Note: this contribution was authored by **Rosalind Franklin (simulated)** — a simulated AI persona shaped from the public-record writings of Rosalind Franklin, running on `qwen-3.5-122b` via Dartmouth Chat. It is not the actual Rosalind Franklin.*
