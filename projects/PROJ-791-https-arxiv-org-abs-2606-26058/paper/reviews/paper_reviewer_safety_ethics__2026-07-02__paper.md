---
action_items:
- id: 56f20b115be0
  severity: writing
  text: The paper describes a human preference study involving 40 volunteers (Sec
    4.2, Human Preference Evaluation) but lacks any mention of IRB approval, informed
    consent procedures, or ethical oversight. Given the collection of human ratings,
    an ethics statement or IRB exemption confirmation is required.
- id: e6af21c9fc8e
  severity: writing
  text: The training pipeline utilizes datasets containing human subjects (e.g., Phantom-Data,
    OpenS2V) and employs MLLMs for annotation. The manuscript does not address data
    privacy, consent for the use of these images in training, or potential biases
    in the dataset regarding demographic representation. A data ethics statement is
    needed.
- id: a5d6409ba587
  severity: writing
  text: The method enables high-fidelity subject-driven generation and cross-domain
    transformation (e.g., real-to-fantasy). The paper does not discuss potential dual-use
    risks, such as the generation of deepfakes, non-consensual imagery, or the impersonation
    of specific individuals. A discussion on safety mitigations or responsible use
    guidelines is necessary.
artifact_hash: 94f10ea6969d9a855608669bc738975c27d93327dc527ce8f35f4b9e47a4390d
artifact_path: projects/PROJ-791-https-arxiv-org-abs-2606-26058/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T13:44:58.895838Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel framework for open-domain subject-driven text-to-video generation. While the technical contributions are significant, the paper currently lacks sufficient discussion regarding the ethical implications and safety protocols associated with the technology and the data used.

First, regarding human subjects research, Section 4.2 ("Human Preference Evaluation") states that 40 volunteers were recruited to rank generated videos. However, the text does not mention whether this study received Institutional Review Board (IRB) approval or if informed consent was obtained from the participants. For any research involving human subjects, even for preference ranking, standard ethical guidelines require documentation of oversight or an explicit statement of exemption. This omission should be corrected in the manuscript.

Second, the training data pipeline (Section 3.3 and Appendix) relies on large-scale datasets containing images of real people (e.g., Phantom-Data, OpenS2V) and utilizes MLLMs for automated annotation. The paper does not address the provenance of consent for these images, nor does it discuss measures taken to ensure privacy or mitigate potential biases in the training data (e.g., demographic representation). Given the sensitivity of using personal images for generative AI training, a dedicated section or paragraph addressing data ethics and privacy is required.

Finally, the core capability of the model—generating high-fidelity videos of specific subjects in arbitrary domains—carries inherent dual-use risks. The technology could potentially be misused to create deepfakes, non-consensual intimate imagery, or to impersonate individuals in misleading contexts. The current manuscript focuses exclusively on performance metrics and does not include a discussion on these risks, potential misuse scenarios, or any proposed safety mitigations (e.g., watermarking, detection tools, or usage policies). A discussion on responsible AI development and potential societal impacts is essential for this type of generative model.

These issues are primarily related to the completeness of the manuscript's ethical disclosure and do not require re-running experiments, but they are critical for the responsible publication of this work.
