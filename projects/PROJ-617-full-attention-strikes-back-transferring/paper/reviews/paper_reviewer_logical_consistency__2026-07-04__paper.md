---
action_items:
- id: cf7c62d396c9
  severity: writing
  text: Section 5.1 claims 600 steps on 48K avg length, while Appendix A.3.2 claims
    180M total tokens. With batch size 8, 600*8*48K = 230.4M, contradicting 180M.
    Reconcile step count, batch size, or total token count to ensure internal consistency.
- id: e39c0dcc2e2a
  severity: writing
  text: Abstract claims 'about 1M label tokens' and 'few hundred steps', but Appendix
    A.3.2 specifies '1.2M label tokens' and '600 steps'. Align the main text numbers
    with the appendix values or use consistent rounding to avoid minor numerical inconsistencies.
artifact_hash: 898687640cf9d8b6eab95a3e688a2f4f6333ec4f1546846934c46563afd8ae37
artifact_path: projects/PROJ-617-full-attention-strikes-back-transferring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:56:49.311544Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper's logical structure is generally sound: the conclusion that RTPurbo achieves efficient sparse inference follows from the premises of intrinsic head sparsity and low-dimensional retrieval. However, there are internal numerical inconsistencies in the experimental reporting that break the chain of reasoning regarding the training cost.

First, Section 5.1 states the second stage uses "about 600 steps" on a corpus with an "average length of 48K". Appendix A.3.2 states the corpus contains "roughly 180M tokens". Using the global batch size of 8 from Table A.2, the calculation $600 \times 8 \times 48,000$ yields 230.4M tokens, which directly contradicts the 180M figure. This discrepancy suggests either the step count, batch size, or average length is misreported.

Second, the abstract and introduction claim the method requires "about 1M label tokens," while Appendix A.3.2 specifies "about 1.2M". While close, this lack of precision, combined with the calculation error above, indicates a need for rigorous alignment between the summary claims and the detailed experimental logs. These issues are fixable by correcting the numbers to be mathematically consistent.
