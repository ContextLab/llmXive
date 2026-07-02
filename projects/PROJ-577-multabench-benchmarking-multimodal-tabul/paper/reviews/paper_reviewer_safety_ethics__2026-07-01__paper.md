---
action_items:
- id: fc25c78a6a71
  severity: writing
  text: The paper includes medical datasets (CheXpert, CBIS-DDSM, Glaucoma) and social
    data (Hateful Meme, Toxicity). While the authors claim data is de-identified,
    the Checklist (Item 11) and Section 7 lack a specific discussion on potential
    harms if these models are deployed in high-stakes settings (e.g., misdiagnosis,
    biased hiring). Explicitly address negative societal impacts and mitigation strategies
    as required by NeurIPS ethics guidelines.
- id: a19b54cc5c80
  severity: writing
  text: The 'Hateful Meme' and 'Jigsaw Toxicity' datasets often contain user-generated
    content that may include personally identifiable information (PII) or sensitive
    attributes not fully scrubbed. The paper must explicitly state the specific de-identification
    protocols used for these datasets and confirm compliance with the original data
    providers' terms of service regarding secondary research use.
- id: fd98f33d39a9
  severity: writing
  text: The curation pipeline involves fine-tuning encoders on the target variable
    (Section 3.2). For datasets involving sensitive attributes (e.g., gender in 'Celeb
    Attractiveness', race in 'Jigsaw'), the paper should discuss whether the Target-Aware
    Representations (TAR) might inadvertently learn and amplify biases present in
    the labels, and if any fairness audits were conducted.
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:49:34.056271Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper introduces MulTaBench, a benchmark for multimodal tabular learning, utilizing 40 datasets including sensitive domains such as healthcare (CheXpert, CBIS-DDSM, Glaucoma), social media toxicity (Jigsaw, Hateful Meme), and demographic data (Celeb Attractiveness). While the authors state in the Checklist (Item 11) that the study relies on "publicly available, de-identified datasets" and satisfies the NeurIPS Code of Ethics, the manuscript lacks a dedicated discussion on the specific safety and ethical risks associated with the proposed methodology and the datasets themselves.

First, the paper does not adequately address the potential for **negative societal impacts** (Checklist Item 10). The introduction of Target-Aware Representations (TAR) that fine-tune encoders on specific targets could inadvertently amplify biases present in the training labels. For instance, in the 'Celeb Attractiveness' dataset, fine-tuning on attractiveness labels could reinforce harmful beauty standards or demographic biases. Similarly, in medical datasets like 'CheXpert', a model optimized for specific diagnostic targets might learn spurious correlations that lead to misdiagnosis in underrepresented populations. The authors should explicitly discuss these risks and propose mitigation strategies, such as fairness audits or bias detection mechanisms, as required by the NeurIPS ethics guidelines.

Second, regarding **data privacy and consent** (Checklist Item 11), while the authors claim data is de-identified, the 'Hateful Meme' and 'Jigsaw Toxicity' datasets are derived from social media platforms where user consent for secondary research use is often ambiguous. The paper should provide more detail on the specific de-identification protocols applied to these datasets and confirm that the usage complies with the original data providers' terms of service. Additionally, the 'Celeb Attractiveness' dataset involves images of public figures; the authors should clarify the legal and ethical basis for using these images for training models that predict subjective attributes.

Finally, the **dual-use potential** of the benchmark should be considered. While the primary goal is to improve multimodal learning, the techniques developed (e.g., fine-tuning encoders on sensitive targets) could be misused for surveillance or automated discrimination. The authors should include a brief statement in the Discussion or Conclusion addressing these potential misuse scenarios and how the community can responsibly use MulTaBench.

Addressing these points will ensure the paper fully complies with safety and ethics standards, particularly regarding the handling of sensitive data and the potential societal consequences of the proposed research.
