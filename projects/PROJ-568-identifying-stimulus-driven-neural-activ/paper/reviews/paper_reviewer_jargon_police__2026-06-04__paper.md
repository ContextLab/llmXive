---
action_items:
- id: f3a6ed200192
  severity: writing
  text: Abstract (e000/e001) lists 9+ acronyms (GLM, MVPA, RSA, etc.) without definition.
    Define each at first use or move to body text to improve accessibility for non-specialists.
- id: 4a7d94632fdb
  severity: writing
  text: Figure e002 caption mentions 'MNI152 space' without definition. Add a brief
    parenthetical explanation (e.g., 'standard anatomical coordinate space') for non-neuroimaging
    readers.
- id: c7295e37d264
  severity: writing
  text: Section 2 (e002) uses 'procrustean transformation' without simplification.
    Suggest adding 'geometric alignment' as a plain-language synonym to reduce barrier
    to entry.
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T13:37:22.475022Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

This manuscript is a comprehensive survey, yet it frequently employs specialized terminology and abbreviations that may exclude non-specialist readers. While the technical precision is appropriate for a neuroimaging audience, the density of acronyms in the abstract and key technical terms in the methods sections require clarification to meet broader accessibility standards.

In the **Abstract (e000/e001)**, the authors list nine distinct methodological acronyms (GLM, MVPA, RSA, TFA, HTFA, SRM, ISC, ISFC, CNN) in a single paragraph. None are defined in the abstract itself. For a review chapter intended for a broader cognitive neuroscience audience, this creates an immediate barrier. I recommend defining the most critical terms (e.g., GLM, RSA) in the abstract or moving the exhaustive list to the body text where definitions are provided.

In **Figure e002 caption**, the term "MNI152 space" is used without definition. While standard in fMRI/iEEG literature, it is opaque to readers from adjacent fields (e.g., psychology, NLP). A brief clarification (e.g., "standardized anatomical coordinate space") would suffice.

In **Section 2 (e002)**, the phrase "procrustean transformation" appears in the context of joint stimulus-activity models. This is a specific geometric term that may confuse readers unfamiliar with linear algebra or shape analysis. The text explains the function (aligning coordinates), but the label itself is jargon-heavy. Replacing it with "geometric alignment transformation" or adding a plain-language synonym would improve flow without losing precision.

Finally, terms like "broadband shifts" (Fig e001 caption) and "searchlights" (Section 2) are used as standard nouns without initial explanation. Given the goal of identifying stimulus-driven patterns, ensuring these operational terms are accessible is crucial for the chapter's utility as a survey. Addressing these points will reduce the jargon load while maintaining scientific rigor.
