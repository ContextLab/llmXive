---
action_items: []
artifact_hash: f098ae707662ea7ce696ff8b8606006fdddb80c25be82361ec114d13c9a397ed
artifact_path: projects/PROJ-1037-why-can-t-i-open-my-drawer-mitigating-ob/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:12:11.499747Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.5
verdict: accept
---

This paper presents a methodological contribution to computer vision (Zero-Shot Compositional Action Recognition) focused on mitigating "object-driven shortcuts" in model training. The work involves training models on existing public video datasets (Something-Something V2, EPIC-KITCHENS-100) and introducing a new benchmark split (EK100-com) derived from these public sources.

From a safety and ethics perspective, the research is low-risk:
1.  **Data Provenance:** The datasets used (Sth-com, EK100) are derived from public benchmarks with established licenses. The paper does not scrape new data from social media or private sources, nor does it release any raw video data containing Personally Identifiable Information (PII). The "EK100-com" is a re-splitting of existing public data, not a new collection of human subjects.
2.  **Dual-Use:** The proposed method (RCORE) aims to improve the temporal reasoning of action recognition models. While improved action recognition could theoretically be used in surveillance, the paper does not introduce capabilities that meaningfully lower the barrier to harmful surveillance or deception compared to existing state-of-the-art models. The method is a regularization technique for training, not a tool for generating deceptive content or exploiting vulnerabilities.
3.  **Human Subjects:** The research does not involve direct interaction with human subjects, surveys, or the collection of private behavioral data. The use of public video datasets for algorithmic training does not require IRB approval in this context, and no such statement is missing.
4.  **Bias/Fairness:** The paper explicitly addresses a form of bias (co-occurrence priors leading to shortcut learning) and proposes a method to mitigate it. It does not introduce new biases against identifiable demographic groups.

There are no missing disclosures, unmitigated risks, or ethical violations specific to this work. The paper is a standard algorithmic improvement study with no foreseeable non-trivial safety risks that require mitigation or disclosure beyond what is standard for the field.
