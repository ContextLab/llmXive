---
action_items:
- id: cc8713297e18
  severity: writing
  text: "Define or replace the term \u201Charness\u201D early on; most readers will\
    \ understand \u201Ctoolset\u201D or \u201Cenvironment configuration\u201D more\
    \ readily."
- id: 6805a22255dc
  severity: writing
  text: "Introduce the acronym \u201CLLM\u201D (large language model) at first use;\
    \ it appears without definition in the abstract and later sections."
- id: 3ac5c47b5c7a
  severity: writing
  text: "Explain the symbols\u202Fk,\u202FG,\u202FN,\u202F\u03B8,\u202F\u03B1,\u202F\
    S_j, etc., when they first appear; many are used in equations before any textual\
    \ description."
- id: 34159609e68f
  severity: writing
  text: "Replace \u201Cself\u2011preference\u201D with a clearer phrase such as \u201C\
    agent\u2019s own ranking of its outputs\u201D and provide a brief intuitive explanation."
- id: 5f5026c01dd2
  severity: writing
  text: "The phrase \u201Cbest\u2011of\u2011N\u201D is jargon; consider rephrasing\
    \ to \u201Cselect the best among N candidates\u201D."
- id: 3dad8ac93899
  severity: writing
  text: "Clarify \u201CDPP\u201D (determinantal point process) on first mention; a\
    \ short parenthetical definition will aid non\u2011specialists."
- id: 104c459ab799
  severity: writing
  text: "The term \u201Cdiagnosis\u201D is used for a specific analysis step; a brief\
    \ description of what this entails would improve readability."
- id: 3469b5052110
  severity: writing
  text: "Avoid overloading the word \u201Crank\u201D \u2013 it appears as a function\
    \ name, a scoring metric, and a verb. Use distinct terms like \u201Cscore\u201D\
    , \u201Ccompare\u201D, or \u201Cevaluate\u201D."
- id: 4d5fdce594db
  severity: writing
  text: "In the abstract, replace \u201CAI agents rely on a harness of skills, tools,\
    \ and workflows\u201D with a plain statement such as \u201CAI agents need a set\
    \ of tools, prompts, and skills to operate\u201D."
- id: e72a9a203c5e
  severity: writing
  text: "The abbreviation \u201CSWE\u2011Bench Pro\u201D is introduced without context;\
    \ add a short clause describing it as a software\u2011engineering benchmark."
- id: cdf811759fed
  severity: writing
  text: "The term \u201Ccoreset\u201D may be unfamiliar; add a brief explanation (e.g.,\
    \ \u201Ca small, representative subset of tasks\u201D)."
- id: 064f9f87e817
  severity: writing
  text: "When referring to \u201Cself\u2011validation\u201D and \u201Cself\u2011consistency\u201D\
    , provide a one\u2011sentence lay explanation of each."
- id: b4e5930abb0d
  severity: writing
  text: "The phrase \u201Csingle optimization round raises \u2026 pass rate \u2026\
    \ without external grading\u201D could be clarified to state that no additional\
    \ labeled data are required."
- id: 3decb7db2c0a
  severity: writing
  text: "In Table captions, replace technical shorthand like \u201CPass\u201D and\
    \ \u201C\u0394\u201D with full words (\u201CPass rate\u201D, \u201CAbsolute change\u201D\
    )."
- id: 806dcc616ced
  severity: writing
  text: "The term \u201Cagent calls\u201D in cost tables may be confusing; consider\
    \ renaming to \u201Cmodel invocations\u201D."
artifact_hash: 1dfb81df34347455cd78b0f836bbc4b7178b6fbb2681f9f18e5c917a00048d5b
artifact_path: projects/PROJ-690-evolving-agents-in-the-dark-retrospectiv/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T19:04:46.563540Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is densely packed with domain‑specific terminology and numerous acronyms that are introduced without definition, which hampers accessibility for readers outside the immediate sub‑field. The central concept of a “harness” is repeatedly used without an initial plain‑language description, leaving the audience to infer its meaning from context. Similarly, symbols such as k, G, N, θ, α, and S_j appear in equations before any textual grounding, making the mathematical sections opaque. Acronyms like “LLM”, “DPP”, and “self‑preference” are employed without parenthetical explanations, and phrases such as “best‑of‑N” and “diagnosis” are used as technical jargon without clarification. The paper would benefit from early, concise definitions of these terms, and from substituting or supplementing them with more intuitive language (e.g., “toolset” for “harness”, “select the best among N candidates” for “best‑of‑N”). Additionally, the abstract and several figure captions contain shorthand (“Pass”, “Δ”) that should be expanded for clarity. Addressing these points will make the work more readable to a broader audience while preserving its technical rigor.
