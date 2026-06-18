---
action_items:
- id: 55007e74d46d
  severity: writing
  text: "Replace the term \u201Cepistemic resilience\u201D with a plain phrase such\
    \ as \u201Cability to stay correct when given misleading medical information\u201D\
    ."
- id: cc41f1e8b66f
  severity: writing
  text: "Define all acronyms at first use (e.g., RAG, LLM\u2011as\u2011judge, Gwet\
    \ AC2, qw\u2011\u03BA) or replace them with descriptive language."
- id: 5f08cc3fae35
  severity: writing
  text: "Simplify the taxonomy description; avoid phrases like \u201Ccontent\u2011\
    corruption\u201D and \u201Cprovenance framing\u201D and instead say \u201Ctype\
    \ of false claim\u201D and \u201Cwho is said to have made the claim\u201D."
- id: c6c084bd62cc
  severity: writing
  text: "Rename \u201CType\u202F1\u201D and \u201CType\u202F2\u201D delivery protocols\
    \ to \u201Cfocused false\u2011claim test\u201D and \u201Cfull\u2011evidence test\u201D\
    \ and explain them in plain language when first introduced."
- id: 264618a3b81c
  severity: writing
  text: "Reduce reliance on specialist jargon such as \u201Cauthority\u2011framed\u201D\
    , \u201Cexception poisoning\u201D, \u201Cspurious anchoring\u201D, and replace\
    \ with everyday terms like \u201Cofficial\u2011sounding false claim\u201D, \u201C\
    fabricated exception\u201D, and \u201Cirrelevant detail\u201D."
- id: d7d76a687f4f
  severity: writing
  text: "When mentioning model configurations (e.g., \u201Chigh reasoning\u201D, \u201C\
    medium reasoning\u201D), briefly explain what the reasoning setting entails for\
    \ non\u2011technical readers."
- id: 6eb7f0df8a37
  severity: writing
  text: "Avoid dense abbreviation clusters in tables (e.g., \u201CASR\u201D, \u201C\
    TASR\u201D, \u201CT1\u201D, \u201CT2\u201D) without a clear legend; add a short\
    \ caption or footnote that spells them out."
- id: b8f0ee129a27
  severity: writing
  text: "Clarify the meaning of statistical terms like \u201Cattack success rate\u201D\
    \ by adding a one\u2011sentence lay explanation (e.g., \u201Cthe percentage of\
    \ times a model\u2019s correct answer was changed by the misleading context\u201D\
    )."
- id: f771e2f5f8e8
  severity: writing
  text: "Replace the phrase \u201Cstatic reusable benchmark\u201D with \u201Ca fixed\
    \ set of test items that can be shared and reused by other researchers\u201D."
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T21:49:58.527187Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is densely packed with specialist terminology that makes it difficult for readers outside the immediate LLM‑medical community to follow. The central concept, repeatedly called “epistemic resilience”, is never explained in plain language; a simple phrase such as “the ability of a model to keep giving the right answer even when the surrounding text contains false medical information” would be far clearer. Similarly, the two evaluation settings are labeled “Type 1” and “Type 2” without an intuitive description; renaming them to “focused false‑claim test” (where only one misleading sentence is shown) and “full‑evidence test” (where all generated sentences are shown) would immediately convey their purpose.

Several acronyms appear without definition. “RAG” (retrieval‑augmented generation) is mentioned in related work but never expanded. The statistical agreement metrics “Gwet AC2” and “qw‑κ” are listed in the clinician‑review tables without any explanation, leaving non‑specialists puzzled. The term “LLM‑as‑judge” is used in the methodology section without context; a brief description of what this means would help.

The taxonomy of misleading context relies on jargon such as “content‑corruption”, “provenance framing”, “authority‑framed”, “exception poisoning”, and “spurious anchoring”. While precise for experts, these labels obscure the underlying idea. Re‑phrasing them as “type of false claim” and “who is said to have made the claim” (e.g., “an official‑sounding false claim”) would make the table and discussion more accessible.

Model configuration descriptors like “high reasoning” or “medium reasoning” are introduced without indicating what changes in the model’s behavior (e.g., longer chain‑of‑thought prompting). A short parenthetical note would aid comprehension.

Tables are dense with abbreviations (ASR, TASR, T1, T2) and assume the reader remembers their meanings from earlier sections. Adding a concise legend or expanding the abbreviations in the table captions would prevent readers from having to flip back and forth.

Finally, the paper repeatedly uses phrases such as “static reusable benchmark” and “paired judgment‑preservation test”. These could be replaced with more straightforward language (“a fixed set of test items that can be shared and reused” and “a test that checks whether the correct answer stays the same after adding misleading information”).

Addressing these points will greatly improve readability for a broader audience while preserving the technical rigor of the work.
