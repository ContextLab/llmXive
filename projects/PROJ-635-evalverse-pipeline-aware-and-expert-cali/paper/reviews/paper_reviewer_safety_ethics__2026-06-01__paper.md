---
action_items:
- id: b4dac2917a50
  severity: writing
  text: Add IRB approval statement and details on informed consent/compensation for
    human annotators in Section 6.1.
- id: 1a4b1ab48313
  severity: writing
  text: Clarify copyright licensing and usage rights for the professional film database
    used in Dataset Curation (Section 5).
- id: 36d66d64597e
  severity: writing
  text: Include a Broader Impact or Safety section discussing dual-use risks (e.g.,
    deepfakes) and mitigation strategies.
artifact_hash: 6faa9771208714f9c9a3cc2fd9c236bea013078b3bccae3296b28b65b67f8880
artifact_path: projects/PROJ-635-evalverse-pipeline-aware-and-expert-cali/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T04:40:43.681960Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a robust framework for evaluating cinematic video generation but lacks sufficient disclosure regarding ethical compliance and potential societal impact. Specifically, the **Human Evaluation Protocol** (Section 6.1) details the use of human annotators (filmmakers, scientists) without stating whether Institutional Review Board (IRB) approval was obtained, or if informed consent and compensation were provided. Standard ethical guidelines for research involving human subjects require explicit confirmation of these protections to ensure participant welfare and data privacy. Without this, the reproducibility of the human study is ethically questionable.

Furthermore, the **Dataset Curation** section (Section 5) describes sourcing a "database of professional films and animations" for test pair construction. The copyright status and usage rights for these materials are not clarified. Utilizing copyrighted content for benchmarking without explicit licensing or fair use justification poses legal and ethical risks, particularly regarding the intellectual property of the original creators. The use of facial recognition tools like InsightFace (Section 7.1.1) on these videos further introduces biometric privacy concerns that require mitigation strategies.

Finally, the paper does not include a **Broader Impact** or **Safety** discussion. As EvalVerse aims to optimize Reinforcement Learning (RL) for video generation, it could inadvertently facilitate the creation of high-fidelity deepfakes, disinformation, or non-consensual imagery. The current manuscript treats evaluation purely as a technical metric without addressing the dual-use risks inherent in advancing professional-grade synthesis capabilities. To meet conference safety standards, the authors must address these omissions to ensure the work does not contribute to harm.
