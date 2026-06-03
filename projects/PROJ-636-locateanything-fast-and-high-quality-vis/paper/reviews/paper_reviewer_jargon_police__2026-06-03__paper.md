---
action_items:
- id: fb1ae8e60848
  severity: writing
  text: Expand 'SFT' to 'supervised fine-tuning' at first use in the supplementary
    material (sec/X_0_suppl.tex).
- id: 8a803a9e13b3
  severity: writing
  text: Define 'KV-caching' as 'Key-Value (KV) caching' upon first appearance in sec/3_0_method.tex.
- id: ba2b2d2f99d6
  severity: writing
  text: Replace 'SOTA' with 'state-of-the-art' throughout the manuscript for clarity.
- id: 9116459ae4f6
  severity: writing
  text: Expand 'MLP' to 'multilayer perceptron' when first introduced in sec/3_0_method.tex.
- id: 7a79732955e5
  severity: writing
  text: Define 'GUI' as 'graphical user interface' at first mention in sec/1_intro.tex.
- id: b7c72950d22b
  severity: writing
  text: Expand 'BF16' to 'bfloat16' in sec/X_0_suppl.tex.
artifact_hash: fd5c6b9375343e0bf1127bc6f967de79045e8b07b55446fb41fe382f0df7e34c
artifact_path: projects/PROJ-636-locateanything-fast-and-high-quality-vis/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T13:57:41.185451Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on jargon clarity and accessibility. While the paper introduces novel concepts like Parallel Box Decoding (PBD), several acronyms and technical terms are used without adequate definition for a broader audience, potentially excluding non-specialist readers.

First, **undefined acronyms** appear in critical sections. In `sec/3_0_method.tex` (Section 3.3), the term "KV-caching" is introduced without expansion, though "key-value cache" appears later. Consistency requires the full term "Key-Value (KV) caching" at the first instance. Similarly, "SFT" is used in `sec/X_0_suppl.tex` (Section "LocateAnything Fine-Tuning") without prior definition in the main text or supplement, despite "supervised fine-tuning" being used in the main text without the acronym. This inconsistency creates confusion for readers scanning the supplement.

Second, **common abbreviations** should be spelled out to ensure clarity. "SOTA" is used repeatedly (e.g., `sec/1_intro.tex`, `sec/4_0_experiments.tex`) instead of "state-of-the-art". "MLP" (`sec/3_0_method.tex`) should be "multilayer perceptron". "GUI" (`sec/1_intro.tex`) should be "graphical user interface" at first mention. "BF16" (`sec/X_0_suppl.tex`) should be "bfloat16". These are standard but defining them aids reproducibility and understanding for interdisciplinary audiences.

Third, **system-level jargon** in the supplement (`sec/X_0_suppl.tex`) such as "Stream Packing" and "MagiAttention" may exclude readers not specialized in distributed training systems. A brief plain-language explanation of their function (e.g., "optimizing GPU memory usage" or "handling irregular attention masks") would improve accessibility significantly.

Finally, terms like "Exploration-exploitation dilemma" (`sec/3_0_method.tex`) are standard but dense. A brief clarification would aid non-experts. Addressing these points will make the paper more inclusive without sacrificing technical precision. The authors should audit all acronyms to ensure they are defined at first use throughout the document, including the supplement.
