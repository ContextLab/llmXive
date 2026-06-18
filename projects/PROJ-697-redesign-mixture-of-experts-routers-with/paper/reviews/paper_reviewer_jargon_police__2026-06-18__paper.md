---
action_items:
- id: 0768e8fbe108
  severity: writing
  text: "Define every acronym (e.g., MoE, MPI, L2) at its first occurrence and provide\
    \ a brief plain\u2011English explanation."
- id: 91de4c9ccff3
  severity: writing
  text: "Replace or accompany highly technical terms such as \u201Cprincipal singular\
    \ direction\u201D, \u201CRayleigh quotient\u201D, \u201Cmanifold\u201D, \u201C\
    retraction\u201D, and \u201Cspectral norm\u201D with simpler language or short\
    \ explanatory footnotes."
- id: 1bc678a3d471
  severity: writing
  text: "Avoid dense symbol\u2011heavy sentences (e.g., Eq.\u202F(1) and Eq.\u202F\
    (2) in Section\u202F3) without accompanying intuitive description; add a sentence\
    \ that describes what the equation is doing in everyday terms."
- id: c03b65ca3c5c
  severity: writing
  text: "Remove or clarify internal code\u2011style comments like \u201C(*\\\\bluebg*)\u201D\
    \ and \u201C(*\\\\pinkbg*)\u201D in Figure\u202F1\u2019s listing; they add visual\
    \ noise for non\u2011technical readers."
- id: b35c4b117fbe
  severity: writing
  text: "Introduce a short glossary or inline parenthetical definitions for mathematical\
    \ objects (e.g.,\u202F\\( \\mathbf{R}_{[i]} \\),\u202F\\( \\mathbf{W}_g^i \\),\u202F\
    \\( \\mathbf{M} \\)) the first time they appear."
- id: 5a8faefcc36c
  severity: writing
  text: "Simplify the description of the \u201CPower\u2011then\u2011Retract\u201D\
    \ paradigm by stating the intuition (e.g., \u201Cfirst we nudge the router toward\
    \ the expert\u2019s most important direction, then we scale it back to keep it\
    \ stable\u201D) before the formal equations."
- id: 8b10079147f2
  severity: writing
  text: "In the abstract and introduction, replace buzz\u2011word phrases like \u201C\
    cornerstone component\u201D, \u201Cprincipal singular direction\u201D, and \u201C\
    expressive mathematical description\u201D with clearer phrasing (e.g., \u201C\
    key part\u201D, \u201Cmost important direction\u201D, \u201Ccompact summary\u201D\
    )."
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:40:21.177132Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is densely packed with specialist terminology that will alienate readers who are not already experts in mixture‑of‑experts (MoE) models. While the technical contribution is clear, the writing repeatedly uses jargon without definition, violating the accessibility principle.

* Acronyms are introduced inconsistently. The first line of the Introduction (Section 1) defines “Mixture‑of‑Experts (MoE, …)”, but later the paper freely uses “MPI”, “L2”, “SVD”, and “LMO” without any plain‑language explanation (see lines 45‑52). Each should be spelled out and briefly described at first use.

* The central mathematical concept – aligning router rows with the “principal singular direction” – appears in Eq. (1) and the surrounding text (Section 3.1) without an intuitive description. Most readers will not know what a singular direction is; a short sentence explaining that it is the direction that captures the most variance in the expert’s weight matrix would greatly improve comprehension.

* Terms such as “Rayleigh quotient”, “manifold”, “retraction”, “spectral norm”, and “L2 norm” are introduced in Sections 3.2 and 4.2. These are standard in linear‑algebra literature but are opaque here. Adding parenthetical lay explanations (e.g., “a way to measure how well two vectors line up”) or a brief glossary would make the paper more inclusive.

* The pseudo‑code in Figure 1 (lines 78‑84) contains LaTeX‑specific comment markers like “(*\\bluebg*)” and “(*\\pinkbg*)”. These visual cues are useful for developers but add unnecessary visual clutter for a broader audience. Either remove them or explain their purpose in a caption.

* Symbol‑heavy sentences (e.g., “\(\bm{\Phi}(\mW_{*}^i, \, \mR_{[i]}^\prime) = \|\mR_{[i]}^\prime\mW_*^i\|_2^2 = \mR_{[i]}^\prime\mW_*^i\mW_*^{i\top}\mR_{[i]}^{\prime\top}\)”) dominate several paragraphs. Pair each equation with a concise, non‑technical summary of what the computation achieves in practice.

* The “Power‑then‑Retract” paradigm is described formally before the intuition. Reordering the exposition to first state the high‑level idea (“first we move the router toward the expert’s most important direction, then we scale it back to keep the values stable”) would help readers follow the subsequent math.

* The abstract and introduction contain several buzz‑word phrases (“cornerstone component”, “most expressive mathematical description”, “intrinsic improvements”) that add little meaning and can be replaced with straightforward language.

By addressing these points—defining acronyms, simplifying technical terms, providing intuitive explanations alongside equations, and cleaning up code annotations—the paper will become far more readable to a wider audience without sacrificing its scientific content.
