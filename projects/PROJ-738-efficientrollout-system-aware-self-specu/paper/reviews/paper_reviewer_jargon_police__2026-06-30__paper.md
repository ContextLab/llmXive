---
action_items:
- id: 58e3e479e733
  severity: writing
  text: Spell out all acronyms (SD, AR, RTN, TP, FSDP, KV-cache) at their first use
    in the main text.
- id: bf41b81f981d
  severity: writing
  text: Provide a brief, plain-English definition for "block efficiency" when it is
    first introduced.
- id: a45f487d70f0
  severity: writing
  text: Replace "makespan" with a more common term like "total time" or "completion
    time."
- id: ddb5bc16003a
  severity: writing
  text: Ensure "W4" and "W8" are explicitly linked to "4-bit" and "8-bit" weights
    upon first mention.
artifact_hash: f5cd2bf8ec4b16de31454f2a2486d371422b77f233615f81a71aa09fed433b62
artifact_path: projects/PROJ-738-efficientrollout-system-aware-self-specu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T10:48:26.499839Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and jargon that are not defined at their first occurrence, creating a barrier for readers outside the immediate sub-field of LLM systems optimization.

In the **Abstract**, the term "Speculative Decoding (SD)" is introduced, but the acronym "SD" is used immediately thereafter without a clear definition of what "block efficiency" ($\tau$) entails for a general audience. The term "block efficiency" appears frequently (e.g., Abstract, Section 1, Section 3) but is never explicitly defined in plain English (e.g., "the average number of tokens accepted per draft step"). Similarly, "AR" (Autoregressive) is used in the Abstract without expansion.

In **Section 4.1**, "RTN" (Round-to-Nearest) is used to describe the quantization method without prior definition. While "W4" and "W8" are used to denote bit-widths, they are not explicitly defined as "4-bit weights" and "8-bit weights" until later in the text or figures.

**Appendix 0** uses the term "makespan" to describe the total time for a rollout to complete. This is a scheduling term that may be opaque to general ML researchers; "total completion time" would be clearer.

**Appendix 3** introduces "TP" (Tensor Parallelism) and "FSDP" (Fully Sharded Data Parallel) in the context of the experimental setup without defining them. "KV-cache" is also used repeatedly in the **Appendix 2** and **Section 4** without being spelled out as "key-value cache" at the first instance.

To improve accessibility, the authors should:
1.  Spell out all acronyms (SD, AR, RTN, TP, FSDP, KV-cache) at their first use in the main text.
2.  Provide a brief, plain-English definition for "block efficiency" when it is first introduced.
3.  Replace "makespan" with a more common term like "total time" or "completion time."
4.  Ensure "W4" and "W8" are explicitly linked to "4-bit" and "8-bit" weights upon first mention.
