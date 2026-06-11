---
action_items:
- id: 2e97de075614
  severity: science
  text: Temper general "In-the-wild" deployment claims to reflect the dominance of
    simulated training data (2.4M clips vs 1.5k real).
- id: 8171382ec76c
  severity: science
  text: Define the specific physical constraints used by the "agentic check" to validate
    compound acoustic scenarios in Section 3.1.
- id: 50c698a7bc22
  severity: writing
  text: Clarify that the "over 30% relative WER reduction" claim applies specifically
    to Voices-in-the-Wild-Bench mixed scenarios, not all benchmarks.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:14:46.483501Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes strong claims about "In-the-wild" robustness (Abstract, Section 1) primarily supported by simulated data (Voices-in-the-wild-2M, 2.4M clips). While the Voices-in-the-wild-Bench includes 1,500 real recordings, the bulk of the training and the "scalable paradigm" claim rests on simulation. This risks overgeneralizing sim-to-real transfer capabilities. Specifically, the Abstract claims "establishing a scalable paradigm for robust ASR in-the-wild" based on a dataset where nearly all training data is synthesized. Section 3.1 asserts "54 physically plausible compound scenarios" verified by an "agentic check" but does not define the physical constraints used, risking overstatement of realism regarding acoustic physics. Additionally, the "In-the-wild^2" terminology in the title is undefined marketing jargon that overstates the novelty beyond standard compound acoustic modeling. The case study (Fig 5) highlights a 0.0% WER recovery on a single hard sample, which should not be generalized as "recover semantic information under highly challenging conditions" without broader statistical evidence on semantic metrics beyond WER (Table Judge shows improvement but is limited). Furthermore, the claim of "over 30% relative WER reduction" (Abstract) is specific to Voices-in-the-Wild-Bench mixed scenarios (Table 3), but the phrasing could imply broader benchmarks like NOIZEUS where reduction is ~17% (Table 2). This ambiguity overstates the method's general advantage across all adverse conditions. Please temper general deployment claims to match the simulated training scope, define the physical plausibility constraints, and clarify the scope of the WER reduction claim.
