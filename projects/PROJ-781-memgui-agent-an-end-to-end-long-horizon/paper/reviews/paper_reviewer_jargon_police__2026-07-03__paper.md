---
action_items:
- id: 5913ae184ec2
  severity: writing
  text: The manuscript relies heavily on domain-specific acronyms and jargon that
    are not defined upon first use, creating barriers for non-specialist readers.
    In the Introduction (Section 1), the term ReAct is used immediately without expansion.
    While standard in the sub-field, it should be spelled out as "Reasoning and Acting"
    on first mention. Similarly, SFT (Supervised Fine-Tuning) appears in Section 1
    and Section 3 without definition. The phrase "prompt explosion" is used metaphorically;
    replacing
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T19:24:23.898810Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and jargon that are not defined upon first use, creating barriers for non-specialist readers. 

In the **Introduction (Section 1)**, the term **ReAct** is used immediately without expansion. While standard in the sub-field, it should be spelled out as "Reasoning and Acting" on first mention. Similarly, **SFT** (Supervised Fine-Tuning) appears in Section 1 and Section 3 without definition. The phrase "prompt explosion" is used metaphorically; replacing this with "excessive prompt length" or "context bloat" would be more precise and accessible.

In **Section 3 (Dataset)**, the term **backbone** is used to refer to the base model. While common in deep learning, "base model" or "foundation model" is clearer for a broader audience. The term **rollouts** is used to describe teacher-generated trajectories; "simulated runs" or "generated trajectories" is less jargon-heavy.

In **Section 4 (Experiments)** and the **Appendix**, several critical metrics are introduced without definition. **IRR** (Information Retention Rate) and **MTPR** (Memory-Task Proficiency Ratio) appear in tables (Table 1, Table 3) but are not defined in the main text. **Pass@k** is used extensively but lacks a formal definition in the body. **LoRA** is mentioned in the appendix without expansion.

Finally, the term **zero-shot** is used frequently (e.g., Section 1, Section 3) without a brief parenthetical explanation (e.g., "without task-specific fine-tuning"), which would aid readers unfamiliar with LLM evaluation protocols.

These omissions do not invalidate the science but significantly reduce the paper's accessibility to the broader computer science community and practitioners outside the specific niche of LLM agents.
