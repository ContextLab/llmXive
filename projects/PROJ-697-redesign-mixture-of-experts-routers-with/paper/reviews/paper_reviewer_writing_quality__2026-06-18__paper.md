---
action_items:
- id: 52af49df9d2f
  severity: writing
  text: "Clarify the motivation paragraph in Section\u202F1 (lines\u202F31\u201145).\
    \ The current prose mixes several ideas without clear transitions, making it hard\
    \ for readers to follow why router\u2011expert alignment is a problem."
- id: 9acea5359522
  severity: writing
  text: "Standardize terminology for the proposed method. The paper alternates between\
    \ \u201CManifold Power\u2011Iteration\u201D, \u201CPower\u2011then\u2011Retract\u201D\
    , and \u201CMPI\u201D (e.g., lines\u202F61\u201170, 124\u2011130). Choose one\
    \ term and use it consistently."
- id: 5a9fec2ceb45
  severity: writing
  text: "Fix numerous grammatical errors and missing articles (e.g., \u201CRouter\
    \ is the cornerstone component\u201D \u2192 \u201CThe router is the cornerstone\
    \ component\u201D in the abstract, line\u202F2)."
- id: 63b6b1044345
  severity: writing
  text: "Improve figure and table captions for self\u2011containment. Captions such\
    \ as Figure\u202F1\u2019s lack a description of what the plotted curves represent\
    \ (lines\u202F159\u2011165)."
- id: 5dfb2b4b12ba
  severity: writing
  text: "Re\u2011write overly long sentences that hinder readability, especially in\
    \ Section\u202F3.1 (lines\u202F203\u2011218) where a single sentence spans >80\
    \ words."
- id: 5f0b309c9c94
  severity: writing
  text: "Add explicit paragraph breaks to separate distinct ideas in the \u201CMethodology\u201D\
    \ section. Currently, several paragraphs contain multiple unrelated points, reducing\
    \ cohesion."
- id: be9b4e37d629
  severity: writing
  text: "Correct inconsistent use of LaTeX commands for math notation (e.g., missing\
    \ backslashes before \u201Ctexttt\u201D in equations on lines\u202F88\u201192)."
- id: 22ed862b0009
  severity: writing
  text: "Provide a concise summary of contributions at the end of the Introduction\
    \ (lines\u202F101\u2011115). The current list is scattered and repeats earlier\
    \ points."
- id: 22fde68c37f8
  severity: writing
  text: "Remove duplicated or placeholder comments (e.g., \u201C% \u2026\u201D lines\
    \ in the source) that appear in the compiled PDF, as they distract the reader."
- id: 910c582873c9
  severity: writing
  text: "Ensure all abbreviations are defined on first use (e.g., \u201CLMO\u201D\
    \ appears without definition in the abstract)."
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:38:29.465558Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The manuscript presents an interesting technical contribution, but its current presentation suffers from several writing‑related issues that impede comprehension.  

**Clarity and Flow:** The abstract (lines 1‑12) introduces the problem and solution in a single dense paragraph. It would benefit from a two‑sentence structure: first stating the limitation of existing routers, then summarizing the proposed “Power‑then‑Retract” approach. Throughout the Introduction (lines 31‑45), the narrative jumps between describing MoE benefits, router design, and challenges without clear transitional sentences, leaving the reader uncertain about the logical progression.  

**Sentence‑Level Grammar:** Numerous grammatical slips appear, such as missing articles (“Router is the cornerstone component” → “The router is the cornerstone component”) and subject‑verb agreement errors (“this design introduces negligible overhead… while \name incurs a mere slowdown” – the verb “incurs” should agree with the singular subject). These errors are scattered across the abstract, Section 3, and the experimental description, detracting from professionalism.  

**Paragraph Cohesion:** Several sections contain overly long paragraphs that bundle multiple concepts. For instance, Section 3.1 (lines 203‑218) combines motivation, mathematical formulation, and intuition in one paragraph, making it hard to parse. Breaking this into three focused paragraphs—(1) motivation, (2) formal objective, (3) intuition—would improve readability.  

**Notation Consistency:** The paper alternates between “Manifold Power‑Iteration (MPI)”, “Power‑then‑Retract”, and “\name”. While the macro definitions allow flexibility, the compiled text should consistently refer to the method by a single name, preferably “Manifold Power‑Iteration (MPI)”, and reserve “\name” for internal references only. Inconsistent naming confuses readers, especially in the Methodology and Experiment sections.  

**Figure and Table Captions:** Captions are terse and sometimes omit essential information. Figure 2’s caption (lines 159‑165) mentions “Convergence comparisons” but does not explain which axes represent loss or which models are compared. Adding a brief description of the plotted quantities and the significance of the curves would make the figures self‑explanatory.  

**LaTeX Formatting:** Some equations lack proper formatting (e.g., missing backslashes before “texttt” in the gating equation on lines 88‑92), which can lead to compilation warnings and affect the PDF’s appearance.  

**Redundancy and Placeholder Text:** The source contains numerous commented-out notes and placeholder comments (e.g., “% …”) that appear in the final PDF. These should be removed before publication to maintain a polished appearance.  

**Abbreviation Definitions:** Certain abbreviations, such as “LMO” in the abstract, are never defined. All acronyms should be expanded on first use to aid readers unfamiliar with the terminology.  

Addressing the items listed in the action‑items section will substantially improve the manuscript’s readability, grammatical correctness, and overall professionalism, allowing the technical contributions to be appreciated without distraction.
