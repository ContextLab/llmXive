---
action_items:
- id: dfcd42cc2d1e
  severity: writing
  text: "Define every acronym at its first appearance (e.g., MoE, GQA, QK\u2011Norm,\
    \ SiLU, MLP, RMSNorm, RoPE, KV, MTP, RLVR, GRPO, IcePop, DAPO, KL)."
- id: 908a86645780
  severity: writing
  text: "Replace overly technical phrases such as \u201Cdecoder\u2011only Transformer\u201D\
    , \u201Clatency\u2011focused modifications\u201D, \u201Cper\u2011token compute\u201D\
    , and \u201Cthroughput mode\u201D with plain\u2011language equivalents (e.g.,\
    \ \u201Ca model that only generates text\u201D, \u201Cspeed\u2011optimised changes\u201D\
    , \u201Ccomputation needed for each token\u201D, \u201Csteady\u2011state processing\
    \ speed\u201D)."
- id: af3c983afe34
  severity: writing
  text: "Add brief, non\u2011technical explanations for specialist terms (e.g., explain\
    \ what \u201CGrouped\u2011Query Attention\u201D does, what a \u201CMulti\u2011\
    Token Prediction head\u201D is, and what \u201Cspeculative decoding\u201D means)\
    \ instead of assuming reader familiarity."
- id: 0f327526b4d9
  severity: writing
  text: "Avoid stacking multiple acronyms in a single sentence without context (e.g.,\
    \ the sentence in \xA72 that lists GQA, QK\u2011Norm, SiLU\u2011gated MLPs, RMSNorm,\
    \ RoPE). Break it into separate, clearly explained clauses."
- id: c9c527b0bb57
  severity: writing
  text: "Reduce numeric overload in prose; move detailed percentages and hyper\u2011\
    parameter values to tables or appendices, and refer to them in the text with simple\
    \ statements (e.g., \u201Cthe model achieves competitive scores on coding benchmarks\u201D\
    )."
- id: 1fc60c584b25
  severity: writing
  text: "Clarify jargon\u2011heavy sections such as the RL description (\xA74.3) by\
    \ summarising the high\u2011level idea before diving into algorithmic specifics\
    \ (e.g., first say \u201CWe fine\u2011tune the model using reinforcement learning\
    \ with rewards that can be automatically checked\u201D, then detail GRPO, asymmetric\
    \ clipping, etc.)."
- id: 309d78ea57ba
  severity: writing
  text: "Standardise terminology: consistently use either \u201Cexpert\u201D or \u201C\
    expert layer\u201D rather than alternating between \u201Cexpert\u201D, \u201C\
    expert configuration\u201D, and \u201CMoE load\u2011balancing loss\u201D."
- id: b5873a93e82d
  severity: writing
  text: Provide a glossary of all abbreviations and specialised terms at the end of
    the paper for quick reference.
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:37:21.815485Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is rich in technical detail but frequently relies on dense jargon and undefined acronyms, which creates a steep barrier for readers outside the immediate research community. In the Introduction (Section 1) the term **MoE** appears without an initial definition, and later sections continue to introduce new abbreviations (e.g., **GQA**, **QK‑Norm**, **SiLU**, **MLP**, **RMSNorm**, **RoPE**, **KV**, **MTP**, **RLVR**, **GRPO**, **IcePop**, **DAPO**, **KL**) without any explanatory context. Each should be spelled out at first use and accompanied by a short, lay‑person description.

Sentences such as “decoder‑only Transformer with MoE feed‑forward layers, GQA, QK‑Norm, SiLU‑gated MLPs, RMSNorm, and RoPE” (Section 2) cram multiple specialized terms into a single clause, making the passage unreadable for non‑experts. Breaking this into separate sentences, each with a brief definition, would greatly improve clarity.

The paper also employs a number of buzz‑heavy phrases—“latency‑focused modifications”, “per‑token compute”, “throughput mode”, “speculative decoding”, “concision penalty”, “trigger words”, “asymmetric PPO clipping”, “leave‑one‑out advantage”—without clarifying their practical meaning. Replacing these with plain language (e.g., “speed‑optimised changes”, “the amount of computation needed for each token”, “steady‑state processing speed”) and adding concise explanations would make the content accessible.

Numeric detail is often embedded directly in the narrative (e.g., “peak LR 3×10⁻⁵, 500 decay iterations, and 117 B tokens”), which distracts from the key take‑away. Such numbers belong in tables or appendices; the main text should summarise the result (“the model was trained with a carefully tuned learning‑rate schedule”).

The reinforcement‑learning section (§4.3) dives into algorithmic specifics before stating the high‑level goal. A brief overview of the purpose of RLVR and the intuition behind the reward shaping would help orient readers.

Finally, the manuscript would benefit from a glossary of all abbreviations and a consistent naming convention for “expert” versus “expert layer”. Addressing these writing issues will significantly broaden the paper’s audience without altering its scientific content.
