---
action_items: []
artifact_hash: eeb38d30b090b9b481f936f7a18b29e67c5fcdb606372133c43443658f731a6e
artifact_path: projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/specs/001-single-cell-trajectories-of-t-cell-exhau/spec.md
backend: dartmouth
feedback: "I read this as a specification of measurements, and I ask of each number:\
  \ what is the instrument, what is the quantity, and is the reference actually established?\
  \ Several are not. (1) The validation signature is cited as \"PMID 32012345\" \u2014\
  \ a placeholder-looking identifier used as the sole independent reference for SC-002,\
  \ SC-006, FR-006 and FR-008. The kind of evidence chemical science demands begins\
  \ with a verifiable source; here the entire biological validation rests on an unverified\
  \ citation. "
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-18T10:05:53.675088Z'
reviewer_kind: llm
reviewer_name: marie-curie-simulated
score: 0.0
verdict: minor_revision
---

I read this as a specification of measurements, and I ask of each number: what is the instrument, what is the quantity, and is the reference actually established? Several are not. (1) The validation signature is cited as "PMID 32012345" — a placeholder-looking identifier used as the sole independent reference for SC-002, SC-006, FR-006 and FR-008. The kind of evidence chemical science demands begins with a verifiable source; here the entire biological validation rests on an unverified citation. (2) The enrichment statistic is internally inconsistent: FR-006 mandates a two-sided t-test over bootstrap iterations while FR-008 mandates Fisher's exact test on the same comparison — two different instruments for the same quantity, both with p < 0.01. (3) The scVelo input is underspecified: FR-001 and the assumptions speak only of "raw count matrices", but RNA velocity requires spliced/unspliced (loom) matrices; the acceptance scenario in US-1 assumes these exist without stating where they come from. (4) FR-010 requires "therapy‑response labels" in each dataset, but the assumed minimum of 80% marker presence says nothing about whether response labels exist at all in chronic-infection datasets; the assumption asserts this for "the relevant GEO dataset" (singular, unnamed) while FR-012 forbids substitution. (5) The cross-dataset consistency claim rests on Spearman correlation over only the "top 3 fork-point genes" — a rank correlation of three items is nearly uninformative as evidence of consistency. (6) The 45-minute CPU-only runtime for scVelo on >10,000 cells is asserted as an acceptance threshold rather than measured; the assumption that 2 cores and ~7 GB RAM suffice is stated, not demonstrated.

---

> *Note: this contribution was authored by **Marie Curie (simulated)** — a simulated AI persona shaped from the public-record writings of Marie Curie, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Marie Curie.*
