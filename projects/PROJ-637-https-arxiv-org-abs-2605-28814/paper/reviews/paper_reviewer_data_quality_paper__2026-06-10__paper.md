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
reviewed_at: '2026-06-10T00:53:24.038456Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This re-review assesses the data quality provisions in the current manuscript revision against the three prior action items. Unfortunately, none of the items have been adequately addressed in the provided LaTeX source.

**1. Dataset Licenses (Item e374e8c83430):**
In `sections/appendix.tex`, under `\subsection{Logical Reasoning}`, the authors state, "We generate the K\&K corpus with the official sampling pipeline." This does not explicitly state the license terms for the Knights-and-Knaves dataset. Similarly, in `\subsection{Multi-Hop Reasoning}`, the text notes, "We use the answerable subset of MuSiQue," without specifying the MuSiQue license. For data quality and legal compliance, explicit license terms (e.g., CC-BY, MIT) must be declared for all training and validation datasets.

**2. Data Split Integrity (Item 4acb3970c8bd):**
In `sections/appendix.tex`, `\subsection{Multi-Hop Reasoning}`, the manuscript describes the training set as "the 3-to-4-hop solvable split of the MuSiQue training data" and the validation set as "the full official MuSiQue validation set." While this defines the splits, it does not explicitly clarify data split integrity. To address the prior `science` severity concern, the text must explicitly confirm that the solvable training split does not leak validation information (e.g., by verifying no overlap exists between the solvable subset and the official validation set).

**3. API Dependency Risks (Item 78da07a452b4):**
In `sections/appendix.tex`, `\subsection{Open Problem Solving}`, the text notes, "LLM access is through the OpenAI API. We use \texttt{gpt-5}..." However, it fails to document API dependency risks. There is no discussion regarding reproducibility constraints should the API change, become unavailable, or if the specific model version (GPT-5) is not publicly accessible. This omission significantly impacts the verifiability of the inference experiments.

All three prior action items remain unresolved. No new data quality issues were identified.
