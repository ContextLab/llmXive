---
action_items:
- id: b9cda0ce7e05
  severity: writing
  text: The paper includes medical datasets (CheXpert, CBIS-DDSM, Glaucoma) but lacks
    a specific discussion on the ethical risks of deploying models trained on these
    benchmarks in clinical settings, particularly regarding false negatives in diagnosis.
- id: ecebd3aaabc1
  severity: writing
  text: The 'Celeb Attractiveness' dataset relies on crowd-annotated attractiveness
    labels. The manuscript should explicitly address the ethical implications of using
    such subjective, potentially biased human annotations for training automated systems.
- id: a3f636df5c07
  severity: writing
  text: While the authors state they use de-identified data, the 'Celeb Attractiveness'
    and 'PetFinder' datasets contain images of identifiable individuals or animals.
    A brief statement confirming compliance with the original data licenses regarding
    public release and potential re-identification risks is needed.
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:47:55.445067Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses safety and ethics primarily through the use of publicly available, de-identified datasets and the inclusion of a standard NeurIPS ethics checklist. The authors correctly note in the checklist (Item 9) that no human subjects were involved in the study itself and that the data is public. However, given the inclusion of high-stakes domains such as healthcare (CheXpert, CBIS-DDSM, Glaucoma) and social bias (Celeb Attractiveness), the manuscript would benefit from a more explicit discussion of the downstream ethical implications of the proposed benchmark.

Specifically, in Section 1 (Introduction) and Section 7 (Discussion), the authors should briefly address the potential for harm if models trained on MulTaBench are deployed in clinical settings without rigorous validation, particularly regarding the risk of false negatives in medical diagnosis. Additionally, the use of the 'Celeb Attractiveness' dataset, which relies on crowd-sourced subjective ratings, warrants a brief acknowledgment of the ethical concerns regarding bias and the potential for reinforcing harmful stereotypes if such models are used in real-world applications.

While the authors state that the data is de-identified, the inclusion of images of people (CelebA) and animals (PetFinder) requires a confirmation that the release of the benchmark complies with the original data licenses and that reasonable steps have been taken to mitigate re-identification risks, even if the data is public. The current checklist response (Item 11) is somewhat generic; a more specific statement regarding the handling of these specific image datasets would strengthen the ethical review. The paper does not appear to contain dual-use risks that would prevent publication, but these clarifications are necessary for responsible research dissemination.
