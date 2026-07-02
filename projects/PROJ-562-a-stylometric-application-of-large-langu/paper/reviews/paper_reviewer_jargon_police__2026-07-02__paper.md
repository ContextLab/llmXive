---
action_items:
- id: 887080076e8a
  severity: writing
  text: The manuscript demonstrates a strong command of computational linguistics
    terminology but occasionally relies on jargon that may alienate readers from the
    digital humanities or general literary studies, who are a key audience for this
    work. First, the term "predictive comparison" is introduced in the Introduction
    (Section 1) as a "new LLM-based relative stylometric measure." While the authors
    explain the *idea* (training a model on one author and testing on another), they
    do not explicitly defin
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:16:52.789457Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript demonstrates a strong command of computational linguistics terminology but occasionally relies on jargon that may alienate readers from the digital humanities or general literary studies, who are a key audience for this work.

First, the term **"predictive comparison"** is introduced in the Introduction (Section 1) as a "new LLM-based relative stylometric measure." While the authors explain the *idea* (training a model on one author and testing on another), they do not explicitly define the *term* itself in plain language. A non-specialist might struggle to distinguish this from standard "perplexity" or "cross-entropy" metrics without a clearer, jargon-free definition of the specific comparative mechanism.

Second, the phrase **"stylometric signatures"** appears frequently (e.g., Section 2.1, 3.1, 3.4). In a biological or forensic context, a "signature" implies a unique, immutable identifier. In this statistical context, the authors are measuring probabilistic patterns. Using "stylistic patterns," "writing fingerprints," or "statistical profiles" would be more accurate and less likely to mislead readers about the nature of the evidence.

Third, the term **"ablation studies"** is used in Section 3.4 to describe the experiments where content words, function words, or parts of speech are removed. While standard in machine learning, this term is not widely known outside the field. A brief parenthetical explanation (e.g., "experiments where specific components are removed to test their contribution") would make the methodology accessible to literary scholars.

Fourth, in the Discussion (Section 4.3), the authors suggest using **"parameter-efficient fine-tuning"** methods. This is a specific technical concept (often referring to techniques like LoRA or adapters) that is not defined. For a general audience, this should be rephrased as "methods that update only a small part of the model" or "lightweight adaptation techniques."

Finally, the word **"confounds"** in Section 2.1 ("eliminating any potential confounds due to translation") is a statistical shorthand. Replacing it with "confounding factors" or "interfering variables" would improve clarity for non-statisticians.

Addressing these terms will ensure the paper's insights are accessible to the interdisciplinary audience it aims to reach, without sacrificing technical precision.
