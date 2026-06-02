---
action_items:
- id: c959054b2f39
  severity: writing
  text: Expand the 'Broader impacts' section to explicitly discuss potential negative
    societal impacts, such as algorithmic bias in healthcare or financial decision-making,
    rather than only citing positive use cases.
- id: f48828bc226c
  severity: writing
  text: Clarify data provenance and consent status for datasets containing human faces
    (e.g., CelebA, Instagram-based datasets) to ensure compliance with privacy regulations
    and original licenses.
- id: 0bd80b23ee55
  severity: writing
  text: Revise the 'Safeguards' checklist answer from 'NA' to discuss potential misuse
    risks of the benchmark, such as enabling discriminatory automated decision-making
    systems.
artifact_hash: 6787a87df841d43fd2785f288cbdae2d1c09b5ec14bf84bfd0cf81559d785c80
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T11:13:32.147708Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses safety and ethics primarily through the NeurIPS Paper Checklist (Section: "NeurIPS Paper Checklist"). While the authors claim compliance with the Code of Ethics and assert that datasets are publicly available and de-identified, the discussion lacks depth regarding specific ethical risks inherent in the selected datasets and the benchmark's potential applications.

**Data Privacy and Consent:**
The benchmark includes datasets involving human subjects, such as "Celeb Attractiveness" (derived from CelebA) and Instagram-based datasets (e.g., "Justin Instagram"). The paper states in the checklist that it relies on "publicly available, de-identified datasets; no human subjects" (Checklist Item: Code of ethics). However, datasets like CelebA have faced scrutiny regarding consent and privacy, as subjects may not have consented to specific downstream uses. Additionally, medical datasets (CBIS-DDSM, CheXpert, Glaucoma) are public but sensitive; while likely HIPAA-compliant, the paper should explicitly confirm that no re-identification risks exist when combining modalities (e.g., linking medical images with tabular metadata).

**Broader Impacts and Misuse:**
The "Broader impacts" section (Checklist Item) is minimal, citing only a "use case in healthcare industry." The benchmark enables high-stakes predictive modeling in domains like healthcare (diagnosis), finance (loan approval via Amazon packages), and hiring (resume text + photo). The current text does not discuss the risk of amplifying biases present in the training data (e.g., racial or gender bias in medical images or attractiveness ratings). The checklist answer for "Safeguards" is "NA" with the justification "Benchmark poses no misuse risks," which is insufficient for a tool that improves multimodal prediction capabilities in sensitive domains.

**Recommendations:**
1.  **Expand Broader Impacts:** Explicitly address potential negative societal impacts, including fairness, bias, and discrimination risks, particularly in the healthcare and e-commerce contexts mentioned.
2.  **Verify Consent:** Provide more detail on the licensing and consent status of datasets involving human identities (CelebA, social media) to ensure they meet ethical standards for research.
3.  **Safeguards Discussion:** Acknowledge that while the datasets are public, the *methods* enabled by the benchmark could be used for harmful purposes (e.g., automated discrimination), and discuss responsible release guidelines.
