---
action_items:
- id: c42f9fd0976f
  severity: writing
  text: Define 'KV' (Key-Value) at first use in the Abstract and Section 3.3. The
    term 'KV Cache' is used repeatedly without explanation, which excludes readers
    unfamiliar with transformer inference internals.
- id: 72d34019c5ec
  severity: writing
  text: Replace 'I2V' with 'image-to-video (I2V)' at first occurrence in Section 1
    and Section 3.1. Acronyms should be defined before use to ensure accessibility
    for non-specialists.
- id: 6651e8db0504
  severity: writing
  text: Clarify 'DMD' (Distribution Matching Distillation) in Section 2 and 3.2. While
    the full name appears later, the acronym is used in equations and text before
    the definition is explicitly provided in the flow of the argument.
- id: 75a77871be52
  severity: writing
  text: Replace 'FT' with 'fine-tuning (FT)' in Section 4 (Table 1 caption and text).
    The abbreviation is used in table headers and text without prior definition in
    the main body.
- id: f1b779bc2c6e
  severity: writing
  text: Define 'VAE' (Variational Autoencoder) at first use in Section 2 (Preliminary)
    or Section 3.1. While common in the field, the paper aims for broad applicability
    and should define standard acronyms.
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:01:41.856846Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology and acronyms that are not consistently defined at their first occurrence, creating barriers for non-specialist readers. 

In the **Abstract**, the term "KV Cache" is introduced immediately without defining "KV" (Key-Value). This is a critical omission for readers not deeply versed in transformer architecture internals. Similarly, "I2V" appears in the abstract's description of the training paradigm without expansion.

In **Section 1 (Introduction)**, "I2V" is used again before being defined. The text also introduces "S2V" (Subject-to-Video) without a clear definition, assuming the reader knows this specific sub-field acronym.

**Section 2 (Preliminary)** introduces "DMD" (Distribution Matching Distillation) in the text describing CausVid, but the full expansion is not provided until later in the section or in the method description, creating a momentary confusion. The term "VAE" is used in equations and text without explicit definition, though it is a standard term, its first use should be expanded for clarity.

**Section 3 (Methodology)** is dense with jargon. "KV Cache" is used repeatedly in Section 3.3 without a prior definition in the main text (only in the abstract where it was also undefined). The term "FT" (Fine-Tuning) appears in Section 4 tables and text without being spelled out first. 

The paper frequently uses "ODE" (Ordinary Differential Equation) in the context of diffusion models (e.g., Section 3.2) without defining it, which may alienate readers from adjacent fields. 

To improve accessibility, the authors should:
1. Define all acronyms (KV, I2V, S2V, DMD, VAE, FT, ODE) at their very first appearance in the text.
2. Consider replacing "KV Cache" with "Key-Value cache" on first use, or providing a brief parenthetical explanation of its function in the context of autoregressive generation.
3. Ensure that terms like "Teacher Forcing" and "Self-Forcing" are briefly contextualized if the paper aims for a broader audience beyond those who have read the specific papers cited (e.g., Self-Forcing, CausVid).

These changes are essential to meet the goal of making the research accessible to a wider audience, including those in e-commerce and content creation who may not be experts in generative model internals.
