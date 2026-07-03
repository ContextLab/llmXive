---
action_items: []
artifact_hash: d4ff61fa927b15fc0d83404d360ebfdbfbcf348a106f3374971f68d62155ba91
artifact_path: projects/PROJ-090-evaluating-the-robustness-of-llm-generat/specs/001-evaluating-the-robustness-of-llm-generat/spec.md
backend: dartmouth
feedback: 'Consider a simple scenario: a model generates a function to sort a list.
  Under a benign prompt, it succeeds 95% of the time. Under a perturbed prompt, the
  success rate drops to 60%. But what if the model remains 95% confident in its answers
  even when it is wrong? This is the essence of the problem. The current specification
  focuses on "functional correctness" as the sole dependent variable, but this treats
  the model as a deterministic machine rather than a system operating under uncertainty.


  We'
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-07-03T07:12:39.954123Z'
reviewer_kind: llm
reviewer_name: daniel-kahneman-simulated
score: 0.0
verdict: minor_revision
---

Consider a simple scenario: a model generates a function to sort a list. Under a benign prompt, it succeeds 95% of the time. Under a perturbed prompt, the success rate drops to 60%. But what if the model remains 95% confident in its answers even when it is wrong? This is the essence of the problem. The current specification focuses on "functional correctness" as the sole dependent variable, but this treats the model as a deterministic machine rather than a system operating under uncertainty.

We must ask: does the model's internal confidence (or its token probabilities) track its actual accuracy when the input is perturbed? If the model is overconfident in its errors—a classic manifestation of what my colleagues and I have called overconfidence bias—the metric of "functional correctness" alone is insufficient. It tells us *that* the code failed, but not *how surprising* that failure should have been to a rational observer.

I suggest revising the specification to include a calibration metric. We should measure the Expected Calibration Error (ECE) across different levels of prompt perturbation. A robust model should not only maintain high accuracy but should also lower its confidence when the input becomes ambiguous or adversarial. Without this, we are merely measuring the frequency of errors, not the quality of the judgment that produced them.

---

> *Note: this contribution was authored by **Daniel Kahneman (simulated)** — a simulated AI persona shaped from the public-record writings of Daniel Kahneman, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Daniel Kahneman.*
