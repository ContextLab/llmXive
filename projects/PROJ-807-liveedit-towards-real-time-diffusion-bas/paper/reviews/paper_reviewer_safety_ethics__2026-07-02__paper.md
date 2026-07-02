---
action_items:
- id: 43dd6d2c7683
  severity: writing
  text: The manuscript presents a technically advanced framework for real-time video
    editing but lacks sufficient discussion on safety and ethical implications. First,
    regarding human subjects research, Section X_suppl describes a user study involving
    20 volunteers. The text details the metrics and results but fails to mention ethical
    compliance. Standard practice requires explicit confirmation of Institutional
    Review Board (IRB) approval or an exemption determination, along with a statement
    confirming
artifact_hash: ad807d68c3634218d8a37b306582366b9db8e405a9dcf34fb28dd7323fcbdd9e
artifact_path: projects/PROJ-807-liveedit-towards-real-time-diffusion-bas/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:46:16.120957Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a technically advanced framework for real-time video editing but lacks sufficient discussion on safety and ethical implications.

First, regarding human subjects research, Section X_suppl describes a user study involving 20 volunteers. The text details the metrics and results but fails to mention ethical compliance. Standard practice requires explicit confirmation of Institutional Review Board (IRB) approval or an exemption determination, along with a statement confirming that informed consent was obtained from all participants. The manuscript should be updated to include these details to ensure the research adheres to ethical standards for human-subject studies.

Second, the training data provenance is insufficiently addressed. The authors state in Section 4.1 that the dataset comprises "20K high-quality video-video pairs, which are carefully filtered from the large-scale Ditto-1M dataset." There is no discussion regarding the licensing, consent, or privacy status of the source videos within Ditto-1M. Given the potential for training data to contain personally identifiable information (PII) or copyrighted material, the authors must clarify the ethical sourcing and legal compliance of this dataset to prevent potential copyright infringement or privacy violations.

Third, the paper highlights significant dual-use risks. The ability to perform high-fidelity, real-time video editing with strict background preservation (12.66 FPS) could be misused for generating deepfakes, disinformation, or unauthorized surveillance tools. The current manuscript focuses almost exclusively on performance metrics and technical novelty. A dedicated section on "Ethical Considerations" or "Societal Impact" is necessary to acknowledge these risks. The authors should discuss potential misuse scenarios and propose mitigation strategies, such as the integration of invisible watermarks, detection mechanisms, or strict usage policies for the released code and models.

Finally, while the paper mentions a "dedicated benchmark," it does not specify if this benchmark includes safety-critical scenarios or if it was curated to avoid sensitive content (e.g., faces of private individuals). Clarifying the composition of the benchmark would further strengthen the ethical rigor of the evaluation.
