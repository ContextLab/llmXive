---
action_items:
- id: d8de98aedb42
  severity: writing
  text: The 'Ethics and Broader Impacts' section (Appendix) claims no human subjects
    were involved, yet Section 3.2 states audio timestamps were verified by 'human
    inspection.' Clarify the nature of this human involvement (e.g., crowdsourcing,
    internal staff) and confirm if IRB approval or informed consent was obtained,
    as this contradicts the 'no human subjects' claim.
- id: d7f375e49b1b
  severity: writing
  text: The paper releases a dataset of intervention-based video clips (Shift, Mute,
    Swap) derived from the 'Oops' dataset. Explicitly state the licensing terms of
    the derived dataset and confirm that the source videos do not contain personally
    identifiable information (PII) or faces that could be re-identified, given the
    potential for misuse in adversarial attacks.
artifact_hash: e83058c54d1a49095166f0ef2ff7177a4db8d52f3626563ad7ae59fa949315e9
artifact_path: projects/PROJ-610-https-arxiv-org-abs-2605-16403/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:16:18.630381Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses a critical safety issue: the "Clever Hans" effect in multimodal models, where models hallucinate audio based on visual priors rather than actual audio input. This has direct implications for safety-critical applications (e.g., autonomous driving, surveillance) where false audio grounding could lead to catastrophic misinterpretations. The proposed diagnostic framework (Thud) is a valuable contribution to model safety and robustness.

However, there are specific ethical and procedural gaps in the manuscript that require clarification before acceptance:

1.  **Human Subject Ambiguity:** In Section 3.2 ("Annotation and Preference Pair Construction"), the authors state that audio timestamps were verified by "human inspection." Conversely, the "Ethics and Broader Impacts" section (Appendix) explicitly claims, "The study does not involve human-subject experiments, crowdsourcing, or the collection of personally identifiable information." This is a direct contradiction. If humans were involved in labeling or verification, the authors must clarify the protocol: Was this internal staff or external crowdworkers? If external, was IRB approval obtained? If internal, was informed consent documented? The current text risks violating standard research ethics guidelines regarding human data labeling.

2.  **Data Privacy and Derived Assets:** The authors release a new dataset of intervened videos (Appendix: New Assets). While the source is the "Oops" dataset, the intervention process (shifting, muting, swapping) creates a new derivative work. The authors must explicitly confirm that the source videos were screened for PII (e.g., faces, license plates, private locations) to prevent the release of a dataset that could be used to re-identify individuals or harass subjects, especially given the "failure cases" nature of the data which might highlight sensitive events.

3.  **Dual-Use Risks:** The paper acknowledges the risk of "adversarial examples" in the Broader Impacts section. However, it does not detail the specific safeguards taken to prevent the release of the "Shift/Mute/Swap" generation scripts from being used to *create* adversarial attacks against other models. While the intent is diagnostic, the methodology is dual-use. A brief statement on the responsible release of the code (e.g., rate limiting, usage agreements, or specific warnings in the README) would strengthen the ethical stance.

The science is sound, but the ethical reporting regarding human involvement and data privacy needs to be precise to align with the stated claims.
