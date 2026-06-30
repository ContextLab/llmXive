---
action_items:
- id: fb1a13ee6d42
  severity: science
  text: The SGGP pipeline removes persons from portraits to create training data.
    Authors must clarify the consent status of individuals in these source images
    and confirm compliance with privacy regulations for this derivative use.
- id: b2d9db5b0448
  severity: writing
  text: The MLLM judge (Gemini-3.0-Pro) scores pose aesthetics. Authors must discuss
    potential biases in this closed-source model regarding body types or cultural
    norms that could lead to exclusionary guidance.
- id: 6515cd3a8e96
  severity: writing
  text: The 'reject' criteria for poor composition may inadvertently flag images of
    people with disabilities. Authors should address how the dataset and model mitigate
    such aesthetic biases.
artifact_hash: c05d947baccac31badb983e4672bc18e6d1ae08f6b2511780ab5cbcde805c567
artifact_path: projects/PROJ-789-shuttermuse-capture-time-photography-gui/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T22:06:51.515711Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a system for capture-time photography guidance, including pose recommendations for human subjects. From a safety and ethics perspective, the primary concerns revolve around data privacy, consent, and potential algorithmic bias in human-centric tasks.

**Data Privacy and Consent:**
In Section 3.1 ("Subject-side guidance"), the authors describe the Subject-side Guidance Generation Pipeline (SGGP). This pipeline takes portrait images, removes the person using an image-editing model (Nano-Banana-Pro) to create a "person-free scene," and pairs this with the extracted pose keypoints. The paper states that images are collected from "multiple online platforms" (Section 3.1, paragraph 1) but does not specify the licensing terms, the nature of these platforms, or whether the individuals depicted in the original portraits provided consent for their likeness to be used in this specific manner (i.e., for training a model to recommend poses). Generating synthetic training data by removing subjects from real-world photos raises significant privacy questions, particularly if the source images were not explicitly licensed for derivative AI training. The authors must explicitly state the provenance of the 30K subject-side samples and confirm that the data usage complies with privacy laws (e.g., GDPR, CCPA) and ethical guidelines regarding the use of human likenesses.

**Algorithmic Bias and Fairness:**
The system provides "pose recommendations" based on "aesthetics" and "scene interaction." The evaluation relies on an MLLM (Gemini-3.0-Pro) to score these poses. There is a risk that the underlying MLLM judge, or the training data itself, may encode biases regarding body types, gender, or cultural norms of posing. For instance, if the "aesthetics" score penalizes certain body shapes or poses common in specific cultures, the system could provide harmful or exclusionary guidance. The paper mentions "five common human pose types" but does not detail the diversity of the subjects in the dataset. A discussion on how the authors ensured diversity in the training data and how they evaluated the model's fairness across different demographics is necessary.

**Evaluation Bias:**
The reliance on a proprietary MLLM (Gemini-3.0-Pro) as the sole judge for "physical plausibility" and "pose aesthetics" (Section 4.2) introduces a "black box" ethical risk. If the judge model has inherent biases, the benchmark results and the model's optimization (via RL) will reinforce those biases. The authors should discuss the limitations of using closed-source models for ethical evaluation and consider including human evaluation across diverse demographic groups to validate the fairness of the recommendations.

**Potential for Harm:**
While the application seems benign (photography guidance), the ability to generate "pose recommendations" could be misused or lead to user harm if the recommendations are physically unsafe (e.g., suggesting poses that cause strain) or if the system is used to generate non-consensual deepfake-like pose overlays. The paper briefly mentions "physical plausibility" but does not explicitly address safety constraints regarding physical injury or the potential for misuse in generating deceptive content. A brief statement on safety constraints and potential misuse scenarios would strengthen the ethical standing of the work.
