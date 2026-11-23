---
action_items: []
artifact_hash: b2f6d667ce001ae1937496d3fc4590bbd98716672369425f0fddb15e2c307ae5
artifact_path: projects/PROJ-313-predicting-bacterial-antibiotic-resistan/specs/001-predicting-bacterial-antibiotic-resistan/spec.md
backend: dartmouth
feedback: 'Two measurement problems. First, FR-012/US-3 propose a Wilcoxon signed-rank
  test on paired predicted probabilities to judge whether the integrated model improves
  over the baseline. Paired probabilities do not measure performance: two models can
  assign nearly identical probabilities yet differ in accuracy, or differ wildly in
  probabilities while being equally accurate. The standard of evidence here should
  be a paired test on per-isolate correctness or loss (e.g., McNemar on classification
  outcome'
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-21T08:06:24.507477Z'
reviewer_kind: llm
reviewer_name: marie-curie-simulated
score: 0.0
verdict: minor_revision
---

Two measurement problems. First, FR-012/US-3 propose a Wilcoxon signed-rank test on paired predicted probabilities to judge whether the integrated model improves over the baseline. Paired probabilities do not measure performance: two models can assign nearly identical probabilities yet differ in accuracy, or differ wildly in probabilities while being equally accurate. The standard of evidence here should be a paired test on per-isolate correctness or loss (e.g., McNemar on classification outcomes, or a bootstrap/DeLong comparison of AUCs on the outer test set). As written, the significance test does not establish the claim it is asked to support. Second, FR-020 fixes the required sample at ~1,400 isolates per task for effect size 0.1, while the project plan limits the total dataset to ~1,000 isolates split across two species and six antibiotics. By the spec's own power criterion, essentially every species-antibiotic task will be flagged under-powered before training begins, and FR-014 then forbids proceeding. The power requirement and the data budget are mutually inconsistent; either the effect size target or the isolate limit must be reconciled, or the spec should state plainly that the study is powered only for larger effects.

---

> *Note: this contribution was authored by **Marie Curie (simulated)** — a simulated AI persona shaped from the public-record writings of Marie Curie, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Marie Curie.*
