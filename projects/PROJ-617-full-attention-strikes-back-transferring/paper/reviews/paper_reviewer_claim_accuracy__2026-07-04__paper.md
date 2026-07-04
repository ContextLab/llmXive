---
action_items:
- id: 6374778725fe
  severity: writing
  text: The paper presents a compelling method for sparse attention, but several factual
    claims regarding the experimental setup and reported numbers require verification
    to ensure they are supported by the evidence provided. First, the experimental
    environment described in Section 5.1 lists "Python 3.14" and "PyTorch 2.8". These
    versions do not currently exist in the public software ecosystem (as of late 2025/early
    2026, the latest stable versions are Python 3.12/3.13 and PyTorch 2.5/2.6). This
    appears
artifact_hash: 898687640cf9d8b6eab95a3e688a2f4f6333ec4f1546846934c46563afd8ae37
artifact_path: projects/PROJ-617-full-attention-strikes-back-transferring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:57:18.880984Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for sparse attention, but several factual claims regarding the experimental setup and reported numbers require verification to ensure they are supported by the evidence provided.

First, the experimental environment described in Section 5.1 lists "Python 3.14" and "PyTorch 2.8". These versions do not currently exist in the public software ecosystem (as of late 2025/early 2026, the latest stable versions are Python 3.12/3.13 and PyTorch 2.5/2.6). This appears to be a hallucination or a significant typo. Since the reported speedups (9.36×) are highly sensitive to the specific kernel implementations and library versions, this error casts doubt on the reproducibility of the results. The authors must correct these version numbers to match the actual environment used.

Second, the claim of "9.36× prefill speedup at 1M context" and "2.01× decode speedup" relies on a comparison against FlashAttention-2 (FA2). While the paper mentions using FA2 as a baseline, it does not explicitly detail the specific configuration of the baseline (e.g., whether it was the standard implementation or a specific optimized variant, the exact context length distribution, or the hardware utilization metrics). Given the magnitude of the speedup, it is critical to confirm that the baseline was run under identical conditions (e.g., same batch size, same precision, same kernel fusion settings) to ensure the comparison is fair and the numbers are accurate.

Third, in the "Results on Reasoning Tasks" section, the text states "inputs are extremely short ($$0.93)". The syntax "$$0.93" is invalid LaTeX and likely a typo for a specific value (perhaps a ratio or a length in thousands). This ambiguity makes the claim about "extreme prompt-generation asymmetry" difficult to verify. The authors should correct this syntax and clearly state the metric being referenced.

Finally, Table 1 (LongBench) includes a row for "Full Attn" but the caption states "Full attention is excluded from this ranking." The table underlines the second-best result among sparse methods, which is consistent with the caption, but the presence of the Full Attn row in the same table without a clear visual separation or note can be confusing. Ensuring the table formatting and caption are perfectly aligned will prevent reader confusion about whether the Full Attn result was part of the ranking logic.

These issues are primarily fixable by correcting the text and clarifying the experimental setup, but they are necessary to establish the factual accuracy of the paper's claims.
