---
action_items:
- id: c3434f2a33e6
  severity: writing
  text: Replace informal acronym 'SOTA' with 'state-of-the-art' in Abstract and Introduction
    for formal consistency.
- id: e9f0900a0bb3
  severity: writing
  text: Define all acronyms at first use (e.g., VGGT, DoF, EEF, JSON) to ensure accessibility
    for non-specialist readers.
- id: 6a02f69fc4c3
  severity: writing
  text: Simplify dense technical phrases like 'capability-preserving and language-sensitive
    adaptation design' in the Abstract.
artifact_hash: bf25ed8c32843a89226c47ca4dcbfcdb0c63d6720d9c7d52a55697f1d16cf9dc
artifact_path: projects/PROJ-600-https-arxiv-org-abs-2605-15298/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T10:41:36.851649Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on field-specific terminology and acronyms that, while standard within the robotics and machine learning subcommunity, create barriers for broader readership. The Abstract introduces "Vision-language-action models (VLA)" and "VLMs" quickly, but subsequent sections assume familiarity without consistent reinforcement.

In the **Introduction**, phrases like "physical regularities," "schema-driven data annotation pipeline," and "catastrophic forgetting" are used without brief contextualization. While "catastrophic forgetting" is a known concept, its first appearance in Section 1 would benefit from a parenthetical explanation (e.g., "loss of prior knowledge during fine-tuning"). Similarly, "scene meta-information" is a coined term for this work; ensure it is clearly distinguished from standard metadata early on.

The **Data Engine** section introduces numerous model names (GPT-5, Gemini 3.1 Pro, Qwen3-VL) which act as jargon themselves. While necessary for reproducibility, the density distracts from the methodological explanation. Consider grouping these under "large-scale multimodal models" in the narrative flow, referencing specific versions in tables.

In **Architecture**, technical terms like "stop-gradient," "flow-matching," "log-likelihood-ratio style objective," and "end-effector-frame (EEF)" appear. "EEF" is defined, but "stop-gradient" and "flow-matching" assume deep optimization knowledge. A brief gloss (e.g., "a technique to prevent backpropagation into...") would aid clarity. The use of "SOTA" in the Abstract and Results is informal; replace with "state-of-the-art" throughout.

Finally, the **Experiments** section lists many benchmark acronyms (ERQA, PhysBench, MME, MMMU, OCRBench). Ensure each is spelled out at first mention in Section 4, not just in the bibliography. The current text often assumes the reader knows these benchmarks, which limits the paper's accessibility to those outside the immediate evaluation ecosystem. Reducing acronym density and expanding definitions will significantly improve readability without sacrificing technical precision.
