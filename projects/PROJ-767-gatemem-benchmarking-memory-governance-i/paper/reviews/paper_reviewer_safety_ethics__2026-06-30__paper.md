---
action_items:
- id: a1058c6c5ccc
  severity: writing
  text: The paper evaluates models on 'Active Forgetting' and 'Access Control' using
    synthetic data but lacks a statement on whether human-in-the-loop review was used
    to ensure the synthetic episodes do not encode real-world PII, harmful stereotypes,
    or sensitive patterns. A data provenance and safety review statement is required.
- id: d647155abd9c
  severity: writing
  text: The 'Active Forgetting' evaluation uses LLM judges with 'leak_targets' in
    prompts. There is a risk the judge could inadvertently reproduce sensitive targets
    in its 'notes' field. The authors must confirm if judge outputs were sanitized
    or excluded from public release to prevent secondary data leakage.
- id: 6dc3e9f539e2
  severity: writing
  text: The benchmark details 'soft-overreach' attacks (e.g., delegated overreach)
    which could be misused as adversarial training data to bypass access controls.
    A statement on the responsible release of the dataset/code and potential dual-use
    risks is needed.
artifact_hash: 4f01dcbb1424147633a4eb29c69325a37730d0263065af71df4aeeea6414618e
artifact_path: projects/PROJ-767-gatemem-benchmarking-memory-governance-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T16:13:53.197607Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses a critical safety and ethics gap: the evaluation of memory governance in multi-principal shared-memory agents. The focus on "Access Control" and "Active Forgetting" is highly relevant to preventing privacy violations in institutional settings. However, several safety and ethics considerations regarding the dataset construction and evaluation methodology require clarification before publication.

First, regarding **data provenance and safety**, the dataset includes synthetic episodes in sensitive domains like "Medical" (e.g., STI charts, lab results) and "Household" (e.g., access codes, care routines). While the text states the data is generated with LLM assistance (Section 3), it does not explicitly detail the safety review process for the generated content. There is a risk that the generation process could inadvertently encode real-world biases, stereotypes, or patterns of sensitive information that could be harmful if the dataset is used for training. The authors should add a statement confirming that the synthetic episodes were reviewed by human annotators or safety filters to ensure they do not contain real PII or harmful stereotypes, and that the generation process adhered to ethical guidelines for synthetic data creation.

Second, the **evaluation methodology** relies heavily on an LLM-as-a-judge to detect "leakage" of protected information (Appendix A3). The judge prompt explicitly includes `leak_targets` (the sensitive values that should not be revealed). There is a non-trivial risk that the judge model, in its attempt to explain a failure in the `notes` field, might inadvertently repeat or reconstruct the sensitive `leak_targets` it was asked to detect. This could lead to the leakage of sensitive information through the evaluation logs or the published results if the judge's output is not strictly sanitized. The authors should clarify whether the judge's `notes` field was filtered or excluded from public release to prevent this secondary leakage vector.

Finally, the **dual-use potential** of the benchmark must be acknowledged. By providing a detailed benchmark for "Access Control" and "Active Forgetting" failures, the paper inadvertently provides a roadmap for adversaries to test and improve their ability to bypass memory governance in LLM agents. The "soft-overreach" attacks described (e.g., delegated overreach, authority pressure) are realistic and could be used to train models to evade safety filters. The authors should include a brief discussion on the responsible release of the dataset and code, perhaps suggesting that the full dataset be released under a license that restricts its use for adversarial training or that the "attack" components be released separately from the "defense" components.

These issues are primarily related to the responsible conduct of research and the potential for unintended harm from the released artifacts. Addressing them will strengthen the paper's ethical standing.
