---
action_items:
- id: daa50388764c
  severity: writing
  text: "Define every acronym at first use (e.g., SFT, LR, ReAct, LLM, etc.) and replace\
    \ obscure abbreviations like \u201CA3B\u201D with a plain description of the model\
    \ size or architecture."
- id: 43414132cc86
  severity: writing
  text: "Replace overloaded buzzwords such as \u201Cdelegation intelligence\u201D\
    , \u201Charness\u201D, \u201Ccore judgment retained\u201D, and \u201Ccitation\u2011\
    grounded reporting\u201D with clearer, more concrete phrasing (e.g., \u201Csystem\
    \ that decides when to delegate tasks\u201D); avoid using the same term repeatedly\
    \ across sections."
- id: f07c12a2f706
  severity: writing
  text: "Simplify tool\u2011name jargon (e.g., `call_sub_agent`, `search`, `visit`,\
    \ `google_scholar`, `python`) by providing a brief plain\u2011language description\
    \ the first time each appears, and consider using more intuitive names like \u201C\
    delegate task\u201D or \u201Cweb search\u201D."
- id: 2fb78fdea36a
  severity: writing
  text: "Reduce the density of technical shorthand in tables and figure captions (e.g.,\
    \ replace \u201C30B\u2011A3B\u201D with \u201C30\u2011billion\u2011parameter model\
    \ with architecture A3B\u201D) to improve readability for non\u2011specialist\
    \ readers."
- id: c7293c0174ba
  severity: writing
  text: "Avoid excessive use of the term \u201Cbenchmark\u201D without context; specify\
    \ what each benchmark measures (e.g., \u201CBrowseComp evaluates web\u2011browsing\
    \ ability\u201D) the first time it is mentioned."
- id: 4f650628f737
  severity: writing
  text: "Clarify the meaning of symbols and notation in equations (e.g., define \u03C4\
    _t, a_t, o_t, H_T) in plain language before presenting the formal notation."
artifact_hash: 23164a835e9fc14f10b36f04bd2aeba4213e5a3b759192c46a449dbfe25b61f3
artifact_path: projects/PROJ-689-searchswarm-towards-delegation-intellige/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:50:21.607323Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is rich in domain‑specific jargon and numerous acronyms that are introduced without definition, which hampers accessibility for readers outside the immediate sub‑field.  

- In the Introduction (Sec. 1, lines 1‑5) the phrase **“delegation intelligence”** is used repeatedly without a plain‑language explanation; a simple description such as “the ability of the system to decide when and what to delegate” would be clearer.  
- The term **“harness”** (Sec. 2.3, lines 12‑15) appears several times as a noun describing the control mechanism, yet no lay definition is provided. Consider rephrasing to “a set of rules that guide delegation”.  
- Acronyms such as **SFT** (Supervised Fine‑tuning), **LR** (learning rate), **ReAct**, **LLM**, **A3B**, **LR** (again), and **cosine** (referring to the learning‑rate schedule) are first mentioned in Sec. 2.3 and Sec. 3.2 without expansion. Each should be spelled out on first occurrence.  
- Tool names like **`call_sub_agent`**, **`search`**, **`visit`**, **`google_scholar`**, and **`python`** (Sec. 2.2, lines 8‑11) are presented as code tokens without any explanatory text; a brief description of their function would aid comprehension.  
- The tables (Tab. 1 and Tab. 2) repeatedly use compact model identifiers (e.g., “30B‑A3B”, “1T‑A32B”) that are opaque to non‑experts. Adding a footnote or expanding the notation would improve readability.  
- The paper frequently repeats the word **“benchmark”** (e.g., “BrowseComp benchmark”, “GAIA benchmark”) without clarifying what each benchmark evaluates. A one‑sentence description the first time each benchmark is introduced would contextualize the results.  
- Equation (1) introduces symbols τ_t, a_t, o_t, H_T without a preceding plain‑language description; readers would benefit from a short narrative explaining that τ_t is the model’s thought, a_t is the action taken, etc., before the formal notation.  

Overall, the technical content is solid, but the heavy reliance on unexplained jargon and shorthand reduces the paper’s accessibility. Addressing the points above will make the manuscript clearer to a broader audience without altering its scientific contributions.
