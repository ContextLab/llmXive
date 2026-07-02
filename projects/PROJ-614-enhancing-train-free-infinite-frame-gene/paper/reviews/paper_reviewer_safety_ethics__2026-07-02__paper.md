---
action_items:
- id: 02f140ee54cc
  severity: writing
  text: The Impact Statement (Section 6) dismisses societal impacts as 'non-exceptional'
    despite the method enabling infinite, consistent video generation. This capability
    significantly lowers the barrier for creating deepfakes and disinformation. The
    statement must be expanded to explicitly address dual-use risks, including identity
    fraud and misinformation, and propose mitigation strategies.
- id: 32625fd441cd
  severity: writing
  text: The Human Evaluation section (Appendix E001) describes a user study with 8
    annotators but lacks details on IRB approval, informed consent procedures, and
    data privacy protections for the participants. As this involves human subjects,
    the manuscript must include a statement confirming ethical oversight and compliance
    with relevant institutional guidelines.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:34:45.490610Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a method (MIGA) for generating consistent, infinite-length videos without retraining foundation models. From a safety and ethics perspective, the primary concern is the potential for dual-use. The ability to generate long, temporally consistent videos significantly lowers the barrier for creating high-quality deepfakes, which can be weaponized for disinformation campaigns, non-consensual intimate imagery, and identity fraud.

The current "Impact Statement" (Section 6) is insufficient. It states that "potential societal impacts are deemed non-exceptional," which is a dangerous underestimation given the specific capability of the model to maintain subject consistency over extended durations (1000+ frames). This specific feature is the exact requirement for realistic deepfake generation. The authors must revise this section to explicitly acknowledge these risks, discuss the potential for misuse, and outline any intended safeguards or recommendations for responsible deployment (e.g., watermarking, detection tools).

Additionally, the "Human Evaluation Experiments" section (Appendix E001) describes a user study involving 8 human annotators. The manuscript currently lacks any mention of Institutional Review Board (IRB) approval, informed consent processes, or how participant data was anonymized and protected. For any research involving human subjects, even in a pairwise comparison setting, standard ethical protocols must be documented. The authors should add a statement confirming that the study was conducted in accordance with ethical guidelines and that informed consent was obtained.

While the paper does not appear to use private or sensitive datasets (relying on public benchmarks and synthetic generation), the lack of explicit ethical consideration for the *output* of the system and the *process* of human evaluation requires attention before publication.
