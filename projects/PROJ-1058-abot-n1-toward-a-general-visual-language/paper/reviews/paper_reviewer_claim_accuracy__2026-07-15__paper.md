---
action_items:
- id: be006e9e085e
  severity: writing
  text: Abstract claims '95.4%/92.9% SR' conflating distinct metrics. Table 1 (indoor)
    uses strict SR<1col, while Table 2 (outdoor) uses relaxed SR<3col. Rephrase to
    specify '95.4% SR (indoor, strict) and 92.9% SR (outdoor, relaxed)' to avoid implying
    comparability.
- id: 50f8eac69c6a
  severity: writing
  text: Abstract states 'boosting POI arrival by 35.0% (to 77.3%)'. Table 4 shows
    an increase from 42.3% to 77.3%, which is +35.0 percentage points, not a relative
    35% increase. Clarify to 'by 35.0 percentage points' to prevent misinterpretation.
- id: 7929db4e606a
  severity: writing
  text: Section 6.1.5 claims ABot-N1 'surpasses all baselines' except STT TR. Table
    5 shows Qwen-RobotNav-4B (90.0%) beats ABot-N1 (89.8%) on STT TR. The phrasing
    is slightly ambiguous; clarify that it leads on SR across all splits but trails
    Qwen-RobotNav-4B on STT TR by 0.2%.
artifact_hash: f88378b8f34f2b343e5f44980e669d21b209180df8e509a6c35972c8ebfdc6e7
artifact_path: projects/PROJ-1058-abot-n1-toward-a-general-visual-language/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T03:44:06.636338Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a robust set of claims supported by internal tables, but there are minor inaccuracies in how the abstract and text summarize the numerical results, specifically regarding the distinction between percentage points and relative percentages, and the conflation of different metric definitions.

In the Abstract, the claim "boosting POI arrival by 35.0% (to 77.3%)" is mathematically ambiguous. The data in Table 4 shows an increase from 42.3% to 77.3%, which is an absolute increase of 35.0 *percentage points*. Stating "by 35.0%" typically implies a relative increase (which would be ~82%), potentially misleading the reader. This should be corrected to "35.0 percentage points" to align with standard scientific reporting.

Additionally, the Abstract states "95.4%/92.9% SR in complex indoor and outdoor scenes" as if these are comparable metrics. However, Table 1 (Indoor) uses a strict zero-collision criterion (SR<1col), while Table 2 (Outdoor) uses a relaxed criterion allowing up to three collisions (SR<3col). These are not directly comparable success rates. The abstract should explicitly qualify these numbers to reflect the different evaluation protocols (e.g., "95.4% SR indoors (strict) and 92.9% SR outdoors (relaxed)").

Finally, in Section 6.1.5, the text claims ABot-N1 surpasses "all baselines" with the "sole exception of STT TR". While true that it loses STT TR to Qwen-RobotNav-4B, the phrasing "surpassing... all baselines" could be misinterpreted as a blanket statement. It is more precise to state it achieves the best SR across all splits and the best TR on DT/AT, while noting the specific 0.2% gap on STT TR against the Qwen baseline. These are minor editorial fixes to ensure the claims precisely match the evidence provided in the tables.
