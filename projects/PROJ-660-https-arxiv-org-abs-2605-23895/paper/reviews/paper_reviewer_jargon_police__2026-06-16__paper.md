---
action_items:
- id: 34cb3d4a1ea8
  severity: writing
  text: Define every acronym at first appearance (e.g., fMRI, NSD, VLM, LLM, CLIP,
    ROI).
- id: e4624f2f349f
  severity: writing
  text: "Replace overly technical phrases such as \u201Ccausal specificity scores\u201D\
    , \u201Ccounterfactual negatives\u201D, and \u201Csemantic-negative generation\
    \ failures\u201D with plain alternatives like \u201Cspecificity score\u201D, \u201C\
    edited images that remove the target\u201D, and \u201Cfailed negative examples\u201D\
    ."
- id: e63044e8d1d6
  severity: writing
  text: "Shorten and simplify long, nested sentences (e.g., the multi\u2011clause\
    \ description in the Introduction and Methods). Break them into two sentences\
    \ and use everyday verbs where possible."
- id: 92c943cb02ec
  severity: writing
  text: "Avoid discipline\u2011specific jargon that may be opaque to non\u2011specialists,\
    \ e.g., replace \u201Cimage\u2011to\u2011fMRI encoding model\u201D with \u201C\
    model that predicts brain responses from images\u201D."
- id: 7644aec562a2
  severity: writing
  text: "Provide brief, lay\u2011person\u2011friendly explanations for specialized\
    \ concepts such as \u201Ccounterfactual editing\u201D and \u201Csemantic negative\
    \ images\u201D the first time they are introduced."
- id: 9ec9aa6ae4c5
  severity: writing
  text: "Standardize terminology: use either \u201Cpositive images\u201D or \u201C\
    target images\u201D consistently throughout, and likewise for \u201Cnegative images\u201D\
    ."
- id: ecc4570e59e0
  severity: writing
  text: Add a short glossary of key terms (e.g., causal dataset, voxel, region of
    interest) either in the appendix or as footnotes to aid readers from adjacent
    fields.
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T10:19:59.875929Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is rich in technical terminology and dense acronym usage, which hampers accessibility for readers outside the immediate neuro‑imaging community. While the target audience is likely familiar with many of these terms, the paper would benefit from a more inclusive writing style that clarifies concepts without sacrificing precision.

First, several acronyms appear without definition. “fMRI” is used in the abstract and throughout the text before any explanation, and similar omissions occur for “NSD”, “VLM”, “LLM”, “CLIP”, and “ROI”. Introducing each acronym at its first occurrence would immediately reduce cognitive load.

Second, the authors repeatedly employ compound nouns that are jargon‑heavy. Phrases such as “causal specificity scores”, “semantic‑negative generation failures”, and “counterfactual negatives” are opaque to non‑specialists. Simple rephrasings—e.g., “specificity score”, “failed negative examples”, and “edited images that remove the target concept”—preserve meaning while improving readability.

Third, many sentences are excessively long and contain multiple nested clauses, especially in the Introduction and Method sections. Breaking these into shorter sentences and using more direct verbs would make the narrative easier to follow. For example, the sentence describing the three image types could be split into three separate statements, each introducing one type.

Fourth, some domain‑specific terms (e.g., “image‑to‑fMRI encoding model”, “counterfactual editing”) are introduced without lay explanations. Brief, parenthetical clarifications would help readers from adjacent fields understand the pipeline without needing to consult external sources.

Fifth, terminology is not always consistent. The manuscript alternates between “positive images”, “target images”, and “concept images”. Selecting a single term and applying it uniformly would avoid confusion. Similarly, “negative images” should be used consistently for both semantic and counterfactual variants.

Finally, adding a concise glossary or footnote list of key concepts (voxel, region of interest, causal dataset) would serve readers who are not experts in neuroimaging but are interested in the methodological contributions.

Addressing these writing‑focused concerns will make the paper more approachable, broaden its impact, and ensure that the innovative methodological contributions are communicated clearly to a wider scientific audience.
