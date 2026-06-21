---
action_items:
- id: 8154307cbeac
  severity: writing
  text: "Several sentences contain overly long clauses and missing commas, which hampers\
    \ readability (e.g., the abstract sentence starting with \u201CWe present Kwai\
    \ Keye\u2011VL\u20112.0\u201130B\u2011A3B\u2026\u201D)."
- id: e8dd708a4512
  severity: writing
  text: "Inconsistent use of hyphens and en\u2011dashes (e.g., \u201CMoE multimodal\
    \ foundation model (3\u202FB active parameters)\u201D vs. \u201CDeepSeek Sparse\
    \ Attention (DSA)\u201D). Standardize punctuation."
- id: b8addf95ef2b
  severity: writing
  text: "Section headings sometimes lack parallel structure (e.g., \u201CModel Architecture\u201D\
    \ uses bullet list, while \u201CPre\u2011Training\u201D mixes narrative and tables).\
    \ Re\u2011organize for uniform flow."
- id: 5ae763ccec3e
  severity: writing
  text: Figure and table captions are duplicated (the teaser figure appears twice
    with identical caption). Remove redundancy to avoid confusion.
- id: 3a1d192fed10
  severity: writing
  text: "References to sections/tables use inconsistent labeling (e.g., \u201CSec.~\\\
    ref{stage_0}\u201D vs. \u201CSection\_2\u201D). Ensure consistent cross\u2011\
    reference style."
- id: bd4336cca157
  severity: writing
  text: "The case study subsections use non\u2011standard headings like \u201CCase\
    \ I: Logical Constraint Solving\u201D without clear hierarchy; consider using\
    \ \\\\subsection or \\\\subsubsection consistently."
- id: e4259d85bd31
  severity: writing
  text: "Numerical values are sometimes presented without units or context (e.g.,\
    \ \u201C20\u202F% throughput gain\u201D). Add clarifying units or explanations."
- id: 8797b2dee32f
  severity: writing
  text: The bibliography contains mixed citation styles and missing punctuation (e.g.,
    missing periods after journal names). Standardize to a single bibliography style.
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:51:49.944132Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The manuscript is technically impressive but suffers from several writing‑related issues that affect clarity and flow. The abstract, while concise, packs multiple complex ideas into a single sentence, making it difficult for readers to grasp the core contributions. Breaking this into two sentences—one describing the model architecture and another summarizing the evaluation results—would improve readability.

Throughout the paper, many sentences are excessively long and contain multiple commas without clear separation of clauses. For example, the sentence in the “Model Architecture” section describing the Sparse Attention Module mixes mathematical notation with prose, leading to a dense block that can be split into shorter, more digestible statements. Adding commas where appropriate and limiting each sentence to a single main idea will help readers follow the technical narrative.

Punctuation inconsistencies are noticeable: hyphens, en‑dashes, and em‑dashes are used interchangeably (e.g., “MoE multimodal foundation model (3 B active parameters)” vs. “DeepSeek Sparse Attention (DSA)”). Adopt a consistent style—preferably en‑dashes for ranges and hyphens for compound adjectives—to maintain a professional tone.

The document’s structure shows uneven hierarchy. Some sections, like “Model Architecture,” rely heavily on bullet lists, while others blend narrative text with tables. Aligning the presentation style (e.g., using subsections for each major component and consistent table placement) will create a smoother reading experience.

Redundant content appears in the figures: the teaser image is included twice with identical captions (Fig. 1 and Fig. 2). Removing the duplicate will declutter the visual layout and prevent confusion.

Cross‑references are inconsistently formatted. The manuscript alternates between “Sec.~\ref{stage_0}” and “Section 2”. Choose a single convention and apply it uniformly.

Case study headings use a non‑standard “Case I: …” format without clear hierarchical markup, making navigation harder. Using proper LaTeX sectioning commands (e.g., \subsection) and consistent numbering will improve the document’s organization.

Numerical results sometimes lack context or units (e.g., “20 % throughput gain”). Adding brief explanatory phrases clarifies the significance of these numbers for readers unfamiliar with the baseline.

Finally, the bibliography mixes citation styles and omits punctuation in several entries. Standardizing to a single bibliography style (e.g., ACM or IEEE) and ensuring each entry ends with a period will enhance the paper’s professionalism.

Addressing these writing concerns will significantly improve the manuscript’s clarity, cohesion, and overall readability.
