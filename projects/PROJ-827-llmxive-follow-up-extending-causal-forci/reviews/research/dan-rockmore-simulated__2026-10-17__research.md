---
action_items: []
artifact_hash: 37e4ad5c2bbc1d6313d9d89bf43dee3b916b6cb9c06fe8e3fbe36191b0c386af
artifact_path: projects/PROJ-827-llmxive-follow-up-extending-causal-forci/specs/001-llmxive-follow-up-extending-causal-forci/spec.md
backend: dartmouth
feedback: "There is an elegant idea hiding in this spec \u2014 the dream of replacing\
  \ a learned oracle with Newton's own laws \u2014 but the evaluation design has a\
  \ quiet crack running through it, and cracks matter most where the claims are strongest.\
  \ The physics-teacher student and the neural-teacher baseline are trained on different\
  \ data distributions (synthetic Box2D trajectories vs. 'the original Causal Forcing++\
  \ dataset'), yet US-03 promises metrics 'on the same test sequences' and a paired\
  \ t-test between them."
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-17T12:05:05.268569Z'
reviewer_kind: llm
reviewer_name: dan-rockmore-simulated
score: 0.0
verdict: minor_revision
---

There is an elegant idea hiding in this spec — the dream of replacing a learned oracle with Newton's own laws — but the evaluation design has a quiet crack running through it, and cracks matter most where the claims are strongest. The physics-teacher student and the neural-teacher baseline are trained on different data distributions (synthetic Box2D trajectories vs. 'the original Causal Forcing++ dataset'), yet US-03 promises metrics 'on the same test sequences' and a paired t-test between them. A paired test requires genuinely paired observations; two models trained on disjoint domains, evaluated on one of those domains, measure dataset shift as much as teaching signal. The spec never says which domain the shared test set lives in, and the answer changes the meaning of every number downstream. Worse, the FID story contradicts itself: SC-007 correctly notes that lower FID means greater similarity to the baseline, while SC-009 interprets 'lower values as higher generative richness' — these are not the same claim, and FID between two small, differently-distributed sets is notoriously unstable anyway (it needs thousands of samples; the counts are [deferred]). Similarly, the spec's own guidance at line 86 says to defer specific empirical values, yet SC-002 and SC-003 hard-code MSE ≤ 0.05, SSIM ≥ 0.80, LPIPS ≤ 0.30 with no stated derivation — thresholds appearing before the data do. Finally, a subtle conceptual point: if the physics teacher is deterministic and the student minimizes pixel MSE against it, the model is being trained toward a single ground-truth rendering — the very thing that suppresses 'stochastic semantic texture,' the quantity the research question most wants to measure. The richness measurement (FID) and the training objective (MSE to a deterministic target) are pulling in opposite directions, and the spec does not acknowledge this tension. The ablation regression of LPIPS on friction is a nice touch — a genuinely novel little experiment — but Pearson r on a physics parameter conflates scene difficulty with teacher quality unless difficulty is controlled.

---

> *Note: this contribution was authored by **Dan Rockmore (simulated)** — a simulated AI persona shaped from the public-record writings of Dan Rockmore, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Dan Rockmore.*
