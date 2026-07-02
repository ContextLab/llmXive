---
action_items:
- id: f88d7a32ddad
  severity: writing
  text: The paper describes training on real-world videos (SpatialVID, RealEstate10K,
    Sekai, DL3DV) with recovered camera poses but lacks explicit statements regarding
    data privacy, consent, or compliance with the original dataset licenses. A dedicated
    'Data Ethics' or 'Privacy' subsection is required to confirm that all real-world
    data usage adheres to the source terms and that no personally identifiable information
    (PII) was retained or exposed.
- id: a1c38a211280
  severity: writing
  text: The 'Event Instruction Tuning' and 'Composable Events' capabilities allow
    users to generate specific interactions (e.g., collisions, handoffs) and modify
    world states. The paper does not address potential dual-use risks where these
    features could be exploited to generate realistic disinformation, deepfakes of
    specific individuals, or harmful scenarios. A discussion on safety guardrails,
    content filtering, or responsible release policies is necessary.
- id: b6e419abe14d
  severity: writing
  text: The evaluation section relies on a VLM (Gemini-3.1-Pro) for artifact detection
    and human preference studies. The paper does not disclose the demographic composition
    of the human assessors or the specific safety guidelines provided to them to prevent
    bias or the generation of harmful content during the study. Clarification on the
    ethical oversight of the human evaluation process is needed.
artifact_hash: dd358f57d42e68a3445f4b34d5b2202a60d20e2d68878dcf007801dde467660f
artifact_path: projects/PROJ-717-dreamx-world-1-0-a-general-purpose-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T17:33:51.647607Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a sophisticated interactive world model with significant capabilities in camera control, long-horizon generation, and event manipulation. From a safety and ethics perspective, the primary concerns revolve around data provenance, potential dual-use applications, and the transparency of evaluation protocols.

First, regarding **data privacy and consent**, Section 3.1.2 ("Real-world and Game Data") lists the ingestion of real-world video datasets (SpatialVID, RealEstate10K, Sekai, DL3DV) for training. While the paper details the technical pipeline for camera pose recovery and filtering, it omits any discussion of the ethical acquisition of this data. Specifically, there is no mention of whether the original datasets contained personally identifiable information (PII), how such data was handled (e.g., blurring faces, removing license plates), or confirmation that the usage complies with the specific licenses and terms of service of the source datasets. Given the increasing scrutiny on training data for generative models, a dedicated statement or subsection addressing data privacy, consent, and license compliance is required to ensure the research adheres to ethical standards.

Second, the paper highlights **dual-use risks** associated with the model's advanced control features. The "Event Instruction Tuning" (Section 4.3) and "Composable Events" capabilities allow users to specify complex interactions, such as object collisions, handoffs, and multi-entity dynamics. While framed as a feature for realistic simulation, these capabilities could be misused to generate highly convincing disinformation, deepfakes of specific individuals in compromising situations, or realistic depictions of harmful events. The manuscript currently lacks a discussion on the potential for misuse, the implementation of safety guardrails (e.g., content filters, refusal mechanisms for harmful prompts), or the authors' strategy for responsible release. A discussion on these risks and the measures taken to mitigate them is essential for a complete safety assessment.

Finally, the **evaluation methodology** raises minor ethical questions. The "Artifact Detection Metric" (Section 6.1) utilizes a proprietary VLM (Gemini-3.1-Pro) to judge generated content, and the "Human Preference Study" (Section 6.4) involves human assessors. The paper does not specify the ethical guidelines provided to human assessors, their demographic diversity, or how potential biases were mitigated. Furthermore, there is no mention of whether the human study was approved by an Institutional Review Board (IRB) or if informed consent was obtained from participants. While the study appears to be a standard preference test, explicit confirmation of ethical oversight and the protocols used to protect participants would strengthen the paper's ethical standing.

In summary, while the technical contributions are significant, the paper requires revisions to explicitly address data privacy, dual-use risks, and the ethical oversight of its evaluation procedures.
