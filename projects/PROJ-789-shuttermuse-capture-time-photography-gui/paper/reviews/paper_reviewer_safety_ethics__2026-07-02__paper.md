---
action_items:
- id: 9dfd0205f01f
  severity: science
  text: The dataset construction pipeline (Sec 4.1) relies on 'Nano-Banana-Pro' to
    remove subjects from portrait images to create 'person-free scenes.' This raises
    significant privacy and consent concerns regarding the source of the original
    portrait images. The paper must explicitly state the provenance of these images
    (e.g., public datasets, user-uploaded content) and confirm that appropriate consent
    was obtained for the original subjects before their likenesses were processed
    and used for training.
- id: 83e6c0720a8b
  severity: writing
  text: The subject-side guidance task involves generating pose recommendations for
    humans in specific scenes. There is a risk of generating poses that could be unsafe,
    physically impossible, or culturally inappropriate for the specific context. The
    paper should include a discussion on safety filters or constraints implemented
    to prevent the model from suggesting harmful or dangerous poses, and clarify if
    any safety guidelines were provided to the human annotators during the verification
    process.
- id: 3442383ef313
  severity: writing
  text: The evaluation of subject-side guidance uses an MLLM judge to score 'physical
    plausibility' and 'scene interaction' (Sec 4.2, App B). While this avoids direct
    human testing, the training data generation involved human annotators reviewing
    poses. The paper should clarify if the annotators were provided with safety guidelines
    to reject poses that might lead to injury or if the dataset includes any exclusion
    criteria for hazardous scenarios.
artifact_hash: c05d947baccac31badb983e4672bc18e6d1ae08f6b2511780ab5cbcde805c567
artifact_path: projects/PROJ-789-shuttermuse-capture-time-photography-gui/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:16:15.377094Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a novel benchmark and model for capture-time photography guidance, which inherently involves interacting with human subjects and their environments. From a safety and ethics perspective, the primary concerns revolve around data privacy, consent, and the potential for generating harmful recommendations.

**Data Privacy and Consent:**
The construction of the subject-side dataset (Section 4.1, "Subject-side guidance") involves a critical step where portrait images are processed using "Nano-Banana-Pro" to remove the subject, creating a "person-free scene" (lines 235-238). The paper states that these images are collected from "multiple online platforms" (line 226) but does not specify the nature of these platforms or the consent status of the individuals depicted. Using images of people, even if the person is later removed, for training a model that generates pose recommendations raises significant privacy and ethical questions. The authors must explicitly disclose the source of these images (e.g., are they from public datasets with known licenses, or scraped from social media?) and confirm that appropriate consent was obtained for the use of these images in this research context. If the images were scraped, the ethical implications of using personal likenesses without explicit consent for training a generative model need to be addressed.

**Safety of Generated Content:**
The model is designed to recommend human poses (Section 1, "Introduction"; Section 4.2, "Subject-side guidance"). There is a non-trivial risk that the model could recommend poses that are physically dangerous (e.g., balancing on unstable objects, extreme contortions) or culturally insensitive/inappropriate for the specific scene. While the paper mentions that "professional annotators subsequently review and revise these rationales" (line 248) and that "Five experienced photographers further verify both the generated rationales and the pose annotations" (line 253), it does not detail the specific safety criteria or guidelines provided to these annotators. The review should include a statement on whether safety constraints were applied during data generation or model training to prevent the suggestion of hazardous poses. Additionally, the "Failure Case Analysis" (Appendix D) notes issues with "floating" poses but does not mention any instances of unsafe pose recommendations, which might suggest a lack of rigorous safety testing or reporting.

**Evaluation Ethics:**
The evaluation relies heavily on MLLM judges (Section 4.2, "Subject-side evaluation metrics"). While this reduces the need for human subjects in the evaluation phase, the training data generation involved human annotators. The paper should clarify if the annotators were trained to identify and reject any poses that could be interpreted as unsafe or harmful. Furthermore, the "User Study" (Section 6) recruited six participants for blind evaluation. The paper should briefly mention the ethical approval process for this study (e.g., IRB approval or informed consent procedures), although this is often standard practice, it is good to explicitly state it in the context of human-subject research.

In summary, while the technical contributions are significant, the paper requires clarification on the ethical sourcing of the training data, particularly regarding the use of images containing human subjects, and a discussion on the safety measures implemented to prevent the generation of harmful pose recommendations.
