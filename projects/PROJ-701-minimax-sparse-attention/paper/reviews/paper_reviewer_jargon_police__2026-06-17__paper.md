---
action_items:
- id: 716eca0bf4dc
  severity: writing
  text: Define all acronyms on first use (e.g., GQA, KL, KV, MoE, ROI, LSE, H800)
    to aid readers unfamiliar with the domain.
- id: effa93f79840
  severity: writing
  text: Replace overly technical jargon such as "exp-free", "KV-outer iteration",
    "persistent grid", and "reverse sparse index" with plain-language explanations
    or brief parenthetical definitions.
- id: 735dab4f3fdf
  severity: writing
  text: Avoid dense abbreviation clusters in sentences (e.g., "per-token attention
    FLOPs", "block-granular access", "two-phase combine") by breaking them into simpler
    clauses.
- id: 8300fa7fc83b
  severity: writing
  text: Introduce a short glossary or inline footnotes for domain-specific terms like
    "attention sink", "block-max-pool", "top-k", and "stop-gradient".
- id: f74c7b2cf5c0
  severity: writing
  text: Rephrase sentences that assume specialist knowledge, such as "the indexer-warmup
    stage rapidly reduces the KL loss", by explaining what KL loss is and why its
    reduction matters.
- id: 978feff5382f
  severity: writing
  text: Simplify the description of the training schedule; replace "two-stage training
    schedule" with "initial full-attention phase followed by sparse training".
- id: 28838082370a
  severity: writing
  text: In the abstract and introduction, replace buzz-word heavy phrases like "agentic
    workflows", "ultra-long-context capability", and "frontier LLMs" with concrete
    descriptions of the tasks and context lengths.
- id: f4ad11a15c27
  severity: writing
  text: Clarify the meaning of symbols that appear without explanation, e.g., the
    symbol G in Eq. (1) and the notation sg in Eq. (9).
- id: 86d78a3b360e
  severity: writing
  text: Limit the use of capitalised technical terms (e.g., "Main Branch", "Index
    Branch") without contextual grounding; add a brief reminder of their role when
    they re-appear later in the text.
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T16:28:21.070759Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript presents a solid technical contribution, but its heavy reliance on domain-specific jargon and undefined acronyms makes it difficult for readers outside the immediate sparse‑attention community to follow.

**Acronym and notation definitions** – Acronyms such as GQA (Grouped‑Query Attention), KL (Kullback‑Leibler), KV (key‑value), MoE (Mixture‑of‑Experts), ROI, LSE, and hardware references like H800 appear without first‑time explanations. Introducing each term where it is first used will greatly improve accessibility.

**Overly technical phrasing** – Phrases like “exp‑free selection”, “KV‑outer iteration”, “persistent grid”, and “reverse sparse index” are used in the kernel description (§4) without plain‑language equivalents. Adding brief parenthetical definitions or a short glossary would help non‑specialist readers understand the implementation details.

**Abbreviation clusters** – Sentences contain dense clusters of abbreviations (e.g., “per‑token attention FLOPs”, “block‑granular access”, “two‑phase combine”). Breaking these into simpler clauses or providing short expansions improves readability.

**Glossary for specialized concepts** – Terms such as “attention sink”, “block‑max‑pool”, “top‑k”, and “stop‑gradient” are critical to the method but are not explained for a broader audience. Inline footnotes or a concise glossary would bridge this gap.

**Context for loss functions** – The manuscript frequently mentions “the indexer‑warmup stage rapidly reduces the KL loss” without explaining what KL loss measures (the divergence between the indexer’s selection distribution and the full‑attention distribution) and why its reduction is important. A brief explanatory sentence would clarify its role.

**Training schedule description** – The “two‑stage training schedule” could be restated as “initial full‑attention phase followed by sparse training”, which is clearer for readers unfamiliar with the terminology.

**Abstract and introduction buzz‑words** – Expressions such as “agentic workflows”, “ultra‑long‑context capability”, and “frontier LLMs” are vague. Replacing them with concrete statements (e.g., “handling sequences up to one million tokens for code generation and document summarisation”) makes the motivation more tangible.

**Symbol clarification** – Symbols like \(G\) in Equation (1) and the stop‑gradient operator \(\sg\) in Equation (9) appear without textual description. Adding a brief note about their meaning will help readers connect the notation to the intuition.

**Consistent terminology** – Capitalised terms “Main Branch” and “Index Branch” are used throughout; when they re‑appear, a short reminder of their function would aid comprehension.

Addressing these writing‑level concerns will broaden the paper’s accessibility without altering its scientific contributions.
