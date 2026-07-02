---
action_items:
- id: f2fa3437bd47
  severity: writing
  text: The abstract claims an "average training acceleration of 3x," but Section
    4.2 only reports "up to 3x" on specific tasks. Clarify if this is a global average
    or a maximum, and specify the conditions to avoid over-claiming general efficiency.
- id: 9e80c5710f3b
  severity: writing
  text: The claim that a 10% checkpoint recovers "approximately 80% of final performance"
    (Section 1, 3.3) lacks specific context. Explicitly state the exact percentage
    and the specific model/dataset used in the main text to support this precise quantitative
    assertion.
- id: 1c690a5228f7
  severity: writing
  text: Describing EffOPD as requiring "no complex hyperparameter tuning" (Abstract)
    overstates the case. The method requires sampling a validation set and performing
    a sequential search. Qualify this claim to acknowledge these procedural requirements
    and overhead.
artifact_hash: 86f3dbb1aa547b2619e2d0068122fd6e86cb21c5f6980bdd3810b1ffe64d94e9
artifact_path: projects/PROJ-597-https-arxiv-org-abs-2605-11739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:57:55.831286Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the efficiency and mechanisms of On-Policy Distillation (OPD) and the proposed EffOPD method. While the analysis is thorough, there are instances where the language overstates the generality or precision of the findings based on the presented data.

First, the Abstract and Introduction claim an "average training acceleration of 3x" (Abstract) and "up to 3x" (Introduction). However, the results in Section 4.2 and Figure 5 show varying speeds across different tasks and models. For instance, the text notes "more than a 3x speedup" on mathematical reasoning but does not explicitly calculate or state a global average across all seven benchmarks and four model scales. Presenting a specific "average" in the abstract without a clear definition or table summarizing this average risks over-claiming the generalizability of the speedup. The claim should be qualified (e.g., "up to 3x on specific tasks" or "an average of X% across benchmarks") to match the evidence.

Second, the claim that a 10% checkpoint recovers "approximately 80% of the final reasoning performance" (Section 1, Section 3.3) is a precise quantitative assertion. While Figure 4(c) is cited, the text does not explicitly state the exact percentage or the specific model/dataset configuration that yielded this 80% figure. Without this explicit detail in the main text, the claim relies on the reader's interpretation of a figure they cannot fully inspect. To avoid over-interpretation, the authors should explicitly state the exact recovery percentage and the specific experimental conditions (e.g., "On the Qwen3-8B model trained on MATH500, a 10% checkpoint recovered 81% of the final performance") in the body of the paper.

Finally, the description of EffOPD as requiring "no complex hyperparameter tuning" (Abstract, Section 4.1) is slightly overstated. The method involves sampling a validation set of 50 examples and performing a sequential search over 5 candidate step sizes. While this avoids training new modules, it introduces specific procedural hyperparameters (validation set size, search range, checkpoint frequency) and computational overhead (validation inference) that are not trivial. The claim should be nuanced to acknowledge these requirements, perhaps by stating it requires "minimal additional hyperparameter tuning" or "no additional trainable modules," rather than implying a complete absence of tuning or overhead.

These issues are primarily matters of precision and qualification in the text rather than fundamental flaws in the science. Addressing them will ensure the claims are strictly supported by the data presented.
