---
action_items:
- id: a3cad1ec42be
  severity: writing
  text: The manuscript relies heavily on specialized acronyms and domain-specific
    terminology that are not consistently defined for a broader audience. While the
    target audience for this paper is likely researchers in generative models, the
    "jargon police" lens requires that every acronym be explicitly defined at its
    first occurrence to ensure accessibility. In the Abstract, the sentence "We denote
    NFEs as Number of Function Evaluations (NFEs) for clarity" is structurally flawed;
    it uses the acronym bef
artifact_hash: 3aad81d8a133042c5a798b8bf30d90974b62e8f4dc5a0e7e17e6ccdaa711ef9d
artifact_path: projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:28:25.072789Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized acronyms and domain-specific terminology that are not consistently defined for a broader audience. While the target audience for this paper is likely researchers in generative models, the "jargon police" lens requires that every acronym be explicitly defined at its first occurrence to ensure accessibility.

In the **Abstract**, the sentence "We denote NFEs as **Number of Function Evaluations** (NFEs) for clarity" is structurally flawed; it uses the acronym before defining it. It should be rewritten to "We use the term Number of Function Evaluations (NFEs) to denote..." or similar.

In **Section 2 (Related Work)** and **Section 3 (Preliminary)**, the acronym **FSDP** (Fully Sharded Data Parallel) appears without definition. Similarly, **JVP** (Jacobian-vector product) is introduced as "Jacobian-vector products (JVPs)" in one instance but the acronym is then used freely. The term **PF-ODE** (Probability-Flow ODE) is used in Section 1 and Section 3 without an explicit expansion of the acronym in the text, relying on the reader to infer the meaning from context or prior knowledge.

In **Section 4 (Method)**, **CFG** (Classifier-Free Guidance) and **DMD** (Distribution Matching Distillation) are introduced. While "classifier-free guidance" is written out, the acronym "CFG" is used in the algorithm and subsequent text. "Distribution Matching Distillation" is defined, but the heavy reliance on "DMD" in the algorithm and discussion assumes the reader has memorized the acronym.

Additionally, terms like "on-policy," "flow map," and "backward simulation" are used as if they are standard vocabulary for all readers, though they are specific to this sub-field. While defining every technical concept is beyond the scope of a jargon review, ensuring that *acronyms* are defined is a critical baseline for readability. The current text forces the reader to flip back to definitions or guess the meaning of acronyms like FSDP and JVP, which disrupts the flow for non-specialists.
