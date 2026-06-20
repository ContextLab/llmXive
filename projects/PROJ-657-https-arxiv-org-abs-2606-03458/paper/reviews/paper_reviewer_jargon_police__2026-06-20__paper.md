---
action_items:
- id: 20912ffb3d2b
  severity: writing
  text: "Define the acronym KV (key\u2011value) and LLM (large language model) at\
    \ first use; they appear throughout the manuscript without explanation, which\
    \ hinders readers outside the sub\u2011field."
- id: cbed2df70cf4
  severity: writing
  text: "Introduce and briefly explain technical terms such as \u2018Hadamard rotation\u2019\
    , \u2018Sinkhorn\u2011inspired dual\u2011scaling\u2019, \u2018incoherence processing\u2019\
    , and \u2018pseudo\u2011decode\u2019 when they first appear; currently they are\
    \ presented as jargon without context."
- id: 89dfe62f42c7
  severity: writing
  text: "Replace or clarify overloaded abbreviations like RTN (round\u2011to\u2011\
    nearest), MSE (mean\u2011squared error), KL (Kullback\u2011Leibler), FP16/FP8,\
    \ and bits/elem; these are not defined before use and assume specialist knowledge."
- id: c36afabde345
  severity: writing
  text: "Provide plain\u2011language descriptions for dataset names (MATH500, AIME24,\
    \ HumanEval, IFEval, Needle\u2011in\u2011a\u2011Haystack) the first time they\
    \ are mentioned, e.g., \u201CMATH500, a benchmark of 500 math reasoning problems\u201D\
    ."
- id: 7411a8d11a9b
  severity: writing
  text: "Explain the meaning of UP (uniform precision) and the significance of \u201C\
    bits per element\u201D in the tables; readers unfamiliar with compression metrics\
    \ may not grasp their impact."
- id: 3423c7878cf3
  severity: writing
  text: "Avoid excessive use of the term \u2018outlier errors\u2019 without a simple\
    \ definition; a brief explanation of why a few large errors dominate end\u2011\
    to\u2011end performance would improve accessibility."
- id: 7c007ed7bd1b
  severity: writing
  text: "Standardize terminology: the paper alternates between \u2018token scaling\u2019\
    , \u2018token magnitude errors\u2019, and \u2018per\u2011token scaling\u2019.\
    \ Choose one phrase and define it early to reduce confusion."
- id: 8026bff43828
  severity: writing
  text: "When citing prior work (e.g., KIVI, TurboQuant, KVQuant, Kitty, PolarQuant,\
    \ SnapKV, PyramidKV, KVZip), add a short parenthetical description of each method\u2019\
    s core idea for non\u2011expert readers."
- id: 89c16decb89c
  severity: writing
  text: "The phrase \u2018dual\u2011scaling variance normalization\u2019 is repeated\
    \ many times; consider a concise synonym (e.g., \u201Cbidirectional variance scaling\u201D\
    ) after the first definition to improve readability."
- id: 9a09a87e92df
  severity: writing
  text: "Remove back\u2011ticks around terms like `pseudo\u2011decode` in the main\
    \ text; they add visual clutter and do not aid comprehension."
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:42:07.809526Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is dense with domain‑specific jargon and numerous acronyms that are introduced without definition, which creates a steep barrier for readers who are not already experts in KV‑Cache quantization. Core concepts such as “KV‑Cache”, “LLM”, “Hadamard rotation”, “Sinkhorn‑inspired dual‑scaling”, and “pseudo‑decode” appear early and are never explained in plain terms, leaving the audience to infer meaning from context. Similarly, technical abbreviations (RTN, MSE, KL, FP16/FP8, bits/elem) are used repeatedly without a glossary or first‑time definition, making the text inaccessible.

The paper also relies heavily on shorthand names for benchmark datasets (MATH500, AIME24, HumanEval, IFEval, Needle‑in‑a‑Haystack) and prior methods (KIVI, TurboQuant, KVQuant, Kitty, PolarQuant, SnapKV, PyramidKV, KVZip). While these are standard within the sub‑community, a brief parenthetical description would help readers understand the relevance of each comparison. Table legends introduce terms like UP (uniform precision) and bits/elem without explanation, which could confuse readers unfamiliar with compression metrics.

Terminology is sometimes inconsistent: the authors refer to “token scaling”, “token magnitude errors”, and “per‑token scaling” interchangeably. Selecting a single phrase, defining it early, and using it consistently would improve clarity. The repeated phrase “dual‑scaling variance normalization” could be replaced with a concise synonym after the initial definition to reduce redundancy.

Finally, minor typographic issues such as the use of back‑ticks around terms (e.g., `pseudo‑decode`) add visual noise without benefit. Addressing these points will make the paper more approachable to a broader audience while preserving its technical contributions.
