---
action_items: []
artifact_hash: 796649ea294da2c6877b98c648d9bc4778f52b3dc5447dec0e7cef675c03eb67
artifact_path: projects/PROJ-474-neural-correlates-of-simulated-social-ex/specs/001-neural-correlates-of-simulated-social-ex/spec.md
backend: dartmouth
feedback: "The spec is admirably concrete, but several of its load-bearing claims\
  \ don't hold up on inspection. (1) The dataset premise is likely wrong: ds000030\
  \ is the UCLA Consortium for Neuropsychiatric Phenomics dataset \u2014 a resting-state\
  \ and task battery for schizophrenia/bipolar/ADHD cohorts \u2014 and to my knowledge\
  \ it contains no Cyberball inclusion/exclusion task. The assumption quietly hedges\
  \ this ('or an equivalent Cyberball task dataset'), but the entire ingestion design,\
  \ event parsing, and the \u226510-s"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-19T02:08:47.203076Z'
reviewer_kind: llm
reviewer_name: dan-rockmore-simulated
score: 0.0
verdict: minor_revision
---

The spec is admirably concrete, but several of its load-bearing claims don't hold up on inspection. (1) The dataset premise is likely wrong: ds000030 is the UCLA Consortium for Neuropsychiatric Phenomics dataset — a resting-state and task battery for schizophrenia/bipolar/ADHD cohorts — and to my knowledge it contains no Cyberball inclusion/exclusion task. The assumption quietly hedges this ('or an equivalent Cyberball task dataset'), but the entire ingestion design, event parsing, and the ≥10-subject minimum are built on unverified event markers that may not exist in the named dataset. (2) The spec silently contradicts its own input: the project idea specifies excluding subjects with '> 3 mm mean displacement,' while this spec mandates a 0.2 mm threshold — a 15-fold tightening presented without justification, and one that could plausibly cull most of a clinical-adjacent sample, making SC-001's '≥ 80 % retention' expectation doubly doubtful. (3) The error-code wiring is crossed: US-1's third acceptance scenario says missing Inclusion/Exclusion markers cause an abort with code 101897695 'see FR-011', but FR-011 actually describes per-subject exclusion from paired analysis; the abort-with-101897695 behavior lives in FR-010. A test written against the scenario text and one written against the FR would diverge. (4) The Harvard-Oxford cortical atlas does not contain an 'mPFC' label (its frontal labels are gyral, e.g., 'Frontal Medial Cortex'), so FR-003's ROI list needs an explicit label-mapping convention or the extraction will fail or be silently redefined. (5) The dynamic analysis is under-specified relative to the data: Cyberball exclusion phases are often ~30–60 s, so a 30 s sliding window may yield only a handful of windows per condition — the 'time-resolved connectivity-strength series' risks being two or three points, and no minimum window count is specified. (6) The spec also flips the connectivity metric from the idea's 'averaging the absolute correlation values' to 'preserving sign' — a defensible choice, but a substantive change to the primary outcome made without acknowledgment. None of these are fatal to the science; all of them are the kind of small print that decides whether a pipeline runs at all.

---

> *Note: this contribution was authored by **Dan Rockmore (simulated)** — a simulated AI persona shaped from the public-record writings of Dan Rockmore, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Dan Rockmore.*
