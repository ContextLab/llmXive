---
action_items:
- id: 2af35b9b6003
  severity: writing
  text: "Define the macro \\modelname early (e.g., in the preamble) and ensure it\
    \ expands to the model\u2019s name consistently throughout the manuscript."
- id: d3d00b33af63
  severity: writing
  text: Introduce all abbreviations (e.g., MoE, GQA, YaRN, RULER, RLVR, BFCL) at first
    use; currently some appear without explanation.
- id: b5aab13d48ca
  severity: writing
  text: Replace placeholder table rows marked with "(... N rows omitted ...)" with
    the actual data or a clear statement that the rows are omitted for brevity in
    the arXiv version.
- id: 3fbe35c0101a
  severity: writing
  text: 'Standardize figure and table references: some captions use "Fig." while the
    text uses "Figure"; pick one style and apply uniformly.'
- id: 2d27db62e707
  severity: writing
  text: "Correct minor grammatical issues (e.g., missing articles, subject\u2011verb\
    \ agreement) in sentences such as \"The model attains 59.3% on MMLU\u2011Pro (best\
    \ among comparators)\" and \"RL yields large gains on BFCL v3 (up to 66.3%)\"."
- id: 55bfc81be40c
  severity: writing
  text: "Improve sentence flow in the Introduction and Architecture sections by breaking\
    \ long, comma\u2011heavy sentences into shorter, clearer statements."
- id: bd2b11b9e0a3
  severity: writing
  text: "Add a brief description of the \u201CMulti\u2011Token Prediction head\u201D\
    \ when first mentioned; readers unfamiliar with the term may be confused."
- id: 54783c9104f2
  severity: writing
  text: "Ensure consistent numeric formatting (e.g., use either \"131\u202F072\" or\
    \ \"131,072\" throughout, but not both)."
- id: 8e8382f3588a
  severity: writing
  text: Check and correct any mismatched references (e.g., \cref{sec:sft} appears
    before the section is defined in some places).
- id: 7389ff317a33
  severity: writing
  text: "Provide a concise summary of the evaluation methodology (e.g., number of\
    \ runs, random seeds) in the post\u2011training evaluation section to aid reproducibility."
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:35:47.744884Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The manuscript presents a technically rich description of the Mellum 2 model, but the writing exhibits several issues that hinder readability and professional polish. Overall, the narrative is coherent, yet it suffers from inconsistent terminology, occasional grammatical slips, and incomplete placeholders that disrupt the flow.

**Clarity & Terminology**  
The macro `\modelname` is used extensively without an explicit definition; readers must infer its meaning from context. Defining it early (e.g., in the preamble) would eliminate ambiguity. Numerous abbreviations—MoE, GQA, YaRN, RULER, RLVR, BFCL—appear without first‑time explanations, which can alienate readers not intimately familiar with the field. Introducing each acronym at its initial occurrence would greatly improve accessibility.

**Sentence Structure & Grammar**  
Several sentences are overly long and packed with commas, reducing clarity. For example, the opening paragraph of the Introduction combines multiple ideas into a single sentence, making it hard to parse. Breaking such sentences into shorter, focused statements would enhance readability. Minor grammatical errors (missing articles, subject‑verb agreement) appear in statements like “The model attains 59.3 % on MMLU‑Pro (best among comparators)” and “RL yields large gains on BFCL v3 (up to 66.3 %)”. These should be corrected.

**Placeholders & Omitted Content**  
The tables contain placeholders such as “(... 21 rows omitted ...)” and “(... N rows omitted ...)”. While understandable for an internal draft, the final arXiv version must either include the full data or explicitly state that rows are omitted for brevity, preferably with a footnote. Similarly, figures are referenced with both “Fig.” and “Figure” inconsistently; a uniform citation style should be adopted.

**Numeric Formatting**  
Numbers are sometimes presented with spaces as thousands separators (e.g., “131 072”) and other times with commas (“131,072”). Consistency is essential; choose one format and apply it throughout the text.

**Figure & Table Captions**  
Captions are generally informative but could be more self‑contained. For instance, the caption for Figure 1 mentions “RULER score versus evaluation context length” without briefly explaining what RULER measures. Adding a short clause would aid readers skimming the paper.

**Reference Management**  
Cross‑references occasionally point to sections that appear later in the document (e.g., `\cref{sec:sft}` before the SFT section). Reordering or adjusting the references will prevent broken links in the compiled PDF.

**Additional Explanations**  
The “Multi‑Token Prediction head” is introduced as an auxiliary objective and a draft model, but its mechanics are not described until later. A brief description at first mention would help orient readers.

In summary, the technical content is solid, but the manuscript would benefit from a focused editorial pass addressing the points above. Implementing the listed action items should raise the paper’s readability to the level expected for a high‑visibility arXiv submission.
