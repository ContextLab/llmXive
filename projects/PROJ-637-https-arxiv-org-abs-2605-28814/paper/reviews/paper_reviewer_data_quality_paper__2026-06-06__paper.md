---
action_items:
- id: e374e8c83430
  severity: writing
  text: Explicitly state the license terms for the Knights-and-Knaves and MuSiQue
    datasets used in training and validation.
- id: 4acb3970c8bd
  severity: science
  text: Clarify data split integrity in Appendix A.2 to ensure the 'solvable split'
    for training does not leak validation information.
- id: 78da07a452b4
  severity: writing
  text: Document API dependency risks for the Open Problem Solving benchmark (GPT-5)
    to address reproducibility constraints.
artifact_hash: d74e7ce3cbfe7aea4f0dad766af5b0e41093c35f05a067517ae8e48026ef85b2
artifact_path: projects/PROJ-637-https-arxiv-org-abs-2605-28814/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T15:40:38.606444Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality, provenance, and reproducibility constraints within the manuscript. While the theoretical and experimental sections are detailed, several critical data management details require clarification to meet standard reproducibility guidelines.

First, dataset licensing and provenance are insufficiently documented. The paper utilizes the Knights-and-Knaves (KK) corpus and the MuSiQue dataset (Appendix A.1, A.2). While these are cited, the specific license terms (e.g., CC-BY, MIT, or proprietary restrictions) are not stated. For open science compliance, the authors must explicitly declare the license governing the training and validation splits used. Additionally, the KK corpus is described as "generated with the official sampling pipeline" (Appendix A.1), but no version hash or seed is provided for this generated data. Without a specific version tag or hash, the exact training distribution cannot be recreated if the pipeline changes.

Second, there is a potential data integrity risk in the Multi-Hop Reasoning setup. Appendix A.2 states the training set is the "3-to-4-hop solvable split of the MuSiQue training data" while validation uses the "full official MuSiQue validation set." The text claims this split is "held fixed across methods," but it does not explicitly confirm that the validation set was excluded from the solvability analysis used to create the training split. A brief statement confirming no leakage between the solvability criteria and the validation set is required to rule out optimistic bias.

Third, the Open Problem Solving experiments rely on the OpenAI API (GPT-5) with a specific cost cap ($50) (Appendix A.3). This introduces a dynamic external dependency that limits reproducibility. The manuscript should explicitly acknowledge that results are contingent on API availability and pricing, and ideally, provide the exact API version or model endpoint identifiers used, as "gpt-5" is a high-level abstraction that may change. Finally, the code repository URL in the Abstract (`github.com/Embodied-Minds-Lab/BES`) should be verified for accessibility, and a DOI or archive link (e.g., Zenodo) is recommended to prevent link rot.
