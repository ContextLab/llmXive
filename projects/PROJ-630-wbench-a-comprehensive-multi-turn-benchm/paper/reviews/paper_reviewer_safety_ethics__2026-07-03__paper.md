---
action_items:
- id: 173d026fb662
  severity: writing
  text: 'The manuscript presents a comprehensive benchmark for interactive video world
    models. From a safety and ethics perspective, the paper is generally sound in
    its intent to evaluate model capabilities rather than generate harmful media.
    However, three specific areas require clarification to ensure full compliance
    with ethical research standards. First, regarding Dual-Use and Content Safety:
    The dataset includes interaction types such as "combat" and "subject action" (Section
    5, Appendix e002). Whil'
artifact_hash: 583182a56bc8cd93d801cd098b02d980b9a48cb375dac6cc8130da68f508615f
artifact_path: projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T14:03:58.605779Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive benchmark for interactive video world models. From a safety and ethics perspective, the paper is generally sound in its intent to evaluate model capabilities rather than generate harmful media. However, three specific areas require clarification to ensure full compliance with ethical research standards.

First, regarding **Dual-Use and Content Safety**: The dataset includes interaction types such as "combat" and "subject action" (Section 5, Appendix e002). While the paper states in the Broader Impact section (Appendix e002) that it mitigates risks by releasing only evaluation tools, it does not explicitly address whether the 289 test cases or the prompt templates include scenarios that could be interpreted as generating violence, self-harm, or other harmful content. Given the rapid advancement of generative video, there is a risk that the benchmark itself could be repurposed to stress-test models for generating harmful imagery. The authors should explicitly state whether a content safety filter was applied during the curation of the 289 cases and whether any prompts were excluded due to safety concerns.

Second, regarding **Human Subject Research**: The evaluation of the benchmark's alignment with human preference involved 400 annotators performing 13,515 pairwise comparisons (Appendix e002, Section "Human-Preference Annotation Platform"). The manuscript does not mention Institutional Review Board (IRB) approval or ethical oversight for this crowdsourcing activity. Standard ethical guidelines require that such studies be reviewed to ensure informed consent, fair compensation, and protection of annotator well-being (e.g., exposure to potentially disturbing content). The authors must confirm if IRB approval was obtained and provide details on the consent process and compensation rates.

Third, regarding **Data Privacy and Training Data**: The "Visual Plausibility" metric relies on a model fine-tuned on 6,000 videos with human annotations (Appendix e002, Section "Visual Plausibility"). The provenance of these 6,000 videos is not detailed. If these videos contain real-world footage of individuals, the authors must confirm that appropriate consent was obtained for their use in training a public model and that no personally identifiable information (PII) was retained. If the data is synthetic, this should be explicitly stated to avoid ambiguity.

Addressing these points will strengthen the paper's ethical standing and ensure transparency regarding the safety of the dataset and the welfare of the human participants involved in the evaluation.
