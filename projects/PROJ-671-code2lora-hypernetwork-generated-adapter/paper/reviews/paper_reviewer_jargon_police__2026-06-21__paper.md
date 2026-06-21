---
action_items:
- id: 84df67be9c87
  severity: writing
  text: Define all acronyms on first use (e.g., LoRA, GRU, RAG, DRC, FFT, QnA, EM,
    CodeBLEU).
- id: 4f10dbe96492
  severity: writing
  text: "Replace or explain domain\u2011specific jargon that may be opaque to non\u2011\
    specialist readers (e.g., \u201Chypernetwork\u2011generated adapters\u201D, \u201C\
    parameter\u2011efficient fine\u2011tuning\u201D, \u201Crepository\u2011specific\
    \ LoRA\u201D, \u201Crank\u202F$r$\u201D, \u201C$\alpha$ scaling\u201D, \u201C\
    truncated BPTT\u201D)."
- id: 3cf771702fa8
  severity: writing
  text: "Add brief plain\u2011language explanations for technical concepts such as\
    \ hypernetworks, LoRA adapters, and the role of the repository encoder, preferably\
    \ in the Introduction or a dedicated \u201CBackground\u201D paragraph."
- id: 71ad4643e6a5
  severity: writing
  text: "Introduce a glossary or inline parenthetical definitions for recurring technical\
    \ terms (e.g., \u201CGRU (gated recurrent unit)\u201D, \u201CRAG (retrieval\u2011\
    augmented generation)\u201D, \u201CDRC (dependency\u2011resolved context)\u201D\
    )."
- id: 609ce79cf8fa
  severity: writing
  text: Avoid overuse of shorthand symbols in equations without accompanying textual
    description (e.g., symbols $\mathbf{e}$, $\mathbf{h}$, $\mathbf{z}_t$). Provide
    a short sentence explaining what each represents.
- id: 5a7511d91e5d
  severity: writing
  text: "Clarify the meaning of \u201Cstatic\u201D vs. \u201Cevolution\u201D scenarios\
    \ in plain terms early in the paper, rather than relying on the symbols \\codelorastatic{}\
    \ and \\codeloraevo{} alone."
- id: a999f4424927
  severity: writing
  text: "In the Method section, replace the phrase \u201Czero inference\u2011time\
    \ token overhead\u201D with a more accessible description such as \u201Cadds no\
    \ extra tokens to the model\u2019s input during inference\u201D."
- id: 9d51f261bb1a
  severity: writing
  text: "When referring to datasets, replace macro placeholders like \\UseMacro{num-repos-total}\
    \ with the actual numbers or a clear statement (e.g., \u201Cwe collected 623 Python\
    \ repositories\u201D)."
- id: 70f2f357e5a4
  severity: writing
  text: "Explain abbreviations in table captions (e.g., \u201CEM\u201D = Exact Match,\
    \ \u201CCR\u201D = cross\u2011repo, \u201CIR\u201D = in\u2011repo) so readers\
    \ can interpret results without consulting the text."
- id: 5411a6fc8bba
  severity: writing
  text: "Provide a short, non\u2011technical summary of the benchmark construction\
    \ (Section\u202F4) for readers unfamiliar with software\u2011evolution terminology."
artifact_hash: fad4da344b5e72bb204a08d5e9a960cbc3b14e42d22c2e81bf4f3bf3224fac8e
artifact_path: projects/PROJ-671-code2lora-hypernetwork-generated-adapter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:47:20.586181Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is rich in domain‑specific terminology and numerous acronyms that are introduced without definition, which hampers accessibility for readers outside the immediate sub‑field of code‑language‑model adaptation.  

**Acronym overload** – The abstract and early sections use “LoRA”, “GRU”, “RAG”, “DRC”, “FFT”, “QnA”, “EM”, “CodeBLEU”, “QLoRA”, “DoRA”, “sLoRA”, “pLoRA”, and several citation‑based macros (e.g., `\codelora{}`) without spelling out their full forms. While these are standard in the community, a broader audience benefits from an explicit definition on first occurrence (e.g., “Low‑Rank Adaptation (LoRA)”).  

**Jargon density** – Phrases such as “hypernetwork‑generated adapters”, “parameter‑efficient fine‑tuning”, “repository‑specific LoRA”, “rank $r$”, “$\alpha$ scaling”, and “truncated BPTT” appear repeatedly without plain‑language paraphrase. Adding a concise explanatory clause (e.g., “a hypernetwork is a small neural network that predicts the weights of another network”) would greatly improve readability.  

**Macro placeholders** – The paper relies heavily on LaTeX macros like `\UseMacro{num-repos-total}` and `\UseMacro{cr-em-codelorastatic}`. In the compiled PDF these resolve to numbers, but the source text still contains opaque placeholders, making the raw manuscript difficult to follow. Replacing them with the actual values or providing a brief inline description would aid reviewers and readers who inspect the source.  

**Equation symbols** – Symbols $\\mathbf{e}$, $\\mathbf{h}$, $\\mathbf{z}_t$, etc., are introduced in the method equations with minimal textual grounding. A short sentence describing each (e.g., “$\\mathbf{e}$ denotes the aggregated repository embedding”) would prevent the reader from having to infer meaning from context alone.  

**Section‑specific jargon** – The “Static vs. Evolution” scenario terminology is expressed only via the macros `\codelorastatic{}` and `\codeloraevo{}`. A plain description of what “static snapshot” and “incremental commit‑based update” entail should be placed early, perhaps in the Introduction, to orient non‑expert readers.  

**Table and figure captions** – Abbreviations such as “EM”, “CR”, “IR”, and “CB” appear in tables without legend. Adding a one‑line explanation in each caption (or a common legend) would make the results self‑contained.  

**Overall recommendation** – The technical contributions are solid, but the manuscript’s heavy reliance on unexplained acronyms and specialist jargon limits its accessibility. Addressing the points above will make the paper readable to a wider audience without sacrificing technical depth.
