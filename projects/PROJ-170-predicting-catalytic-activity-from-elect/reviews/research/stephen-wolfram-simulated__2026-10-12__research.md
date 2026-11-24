---
action_items: []
artifact_hash: dcb7e2d52561a22cc7a63148a5bb397116fd88e5502fcd4051c57219c8ccba67
artifact_path: projects/PROJ-170-predicting-catalytic-activity-from-elect/specs/001-predicting-catalytic-activity-from-elect/spec.md
backend: dartmouth
feedback: "The load-bearing risk in this spec is the data alignment, and the spec\
  \ treats it as a solved preprocessing step when it is actually the experiment. OC20\
  \ is a purely computational dataset of DFT reaction energetics; it contains no experimental\
  \ TOFs. The experimental TOFs come from a single '2025 CO\u2082 hydrogenation study'\
  \ (never identified by title, DOI, or URL), and FR-002 requires exact string matching\
  \ on composition, surface_facet, and synthesis_condition across three heterogeneous\
  \ sources. Real"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-12T20:06:26.544269Z'
reviewer_kind: llm
reviewer_name: stephen-wolfram-simulated
score: 0.0
verdict: minor_revision
---

The load-bearing risk in this spec is the data alignment, and the spec treats it as a solved preprocessing step when it is actually the experiment. OC20 is a purely computational dataset of DFT reaction energetics; it contains no experimental TOFs. The experimental TOFs come from a single '2025 CO₂ hydrogenation study' (never identified by title, DOI, or URL), and FR-002 requires exact string matching on composition, surface_facet, and synthesis_condition across three heterogeneous sources. Realistically this yields tens of matched entries, not the hundreds-to-thousands the spec hedges toward — and the hedge is itself internally inconsistent: the acceptance scenario defers 'n≥500, target≥3000' while the assumption says the analysis proceeds at ≥500, but no evidence is offered that even 500 experimental CO₂-hydrogenation TOF entries with matching DFT descriptors exist anywhere in the literature. A power analysis on a sample size that the data cannot supply is not a power analysis. Second, the spec's success criteria quietly retreat from the idea's claims: SC-003 asks only that a top-5-descriptor model reach half the full model's R² and explicitly relabels this as 'measuring feature redundancy rather than physical validation,' which no longer answers the research question of which descriptors capture the physical determinants. Third, the Materials Project does not distribute a public 'mp_bulk_descriptors.csv' via wget, and its data requires an API key — FR-001's download mechanism is unverified. The right fix is cheap and immediate: run the alignment on the actual sources before committing to modeling stories, and report the true matched count as the first experimental result rather than an assumption.

---

> *Note: this contribution was authored by **Stephen Wolfram (simulated)** — a simulated AI persona shaped from the public-record writings of Stephen Wolfram, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Stephen Wolfram.*
