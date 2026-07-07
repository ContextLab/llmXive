---
action_items:
- id: 6b47547939f8
  severity: writing
  text: 'Section ''Extended Related Work'' (Appendix) uses ''Q-formers'' without definition.
    While ''cross-attention'' is mentioned, the specific architecture component ''Q-former''
    (Query-former) is a named method from BLIP-2 that may not be known to all adjacent-field
    readers. Add a brief gloss: ''Q-formers (query-based cross-attention modules)''.'
- id: 7ccf6c816e7e
  severity: writing
  text: 'Section ''Train-Test Decontamination'' (Appendix) introduces ''SSCD'' (self-supervised
    copy-detection descriptor) and ''MinHash'' without expansion. While ''MinHash''
    is standard in NLP, ''SSCD'' is specific to this pipeline. Define SSCD at first
    use: ''SSCD (self-supervised copy-detection descriptor)''.'
- id: c6cae189de60
  severity: writing
  text: 'Section ''Train-Test Decontamination'' (Appendix) uses ''Jaccard'' similarity
    without defining the metric or the set operation (intersection over union) for
    a reader who might know MinHash but not the specific similarity metric used. Add:
    ''Jaccard similarity (intersection over union of the n-gram sets)''.'
- id: 378b5ba0a5c0
  severity: writing
  text: 'Section ''Evaluation Suite Details'' (Appendix) lists ''MTL'' as a benchmark
    category without defining the acronym. In this context, it likely means ''Multilingual'',
    but ''MTL'' often stands for ''Multi-Task Learning'' in adjacent fields. Define
    explicitly: ''MTL (Multilingual)''.'
- id: fd7f2b3092bd
  severity: writing
  text: 'Section ''Data Mixing'' (Appendix) uses ''pp'' as an abbreviation for ''percentage
    points'' (e.g., ''+1.1pp''). While common in economics and some ML subfields,
    it is often confused with ''percent'' by readers from adjacent disciplines. Define
    at first use: ''percentage points (pp)''.'
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:42:39.816071Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally well-structured for a technical audience, but it relies on several subfield-specific acronyms and named methods that are not defined at their first occurrence. A competent PhD from an adjacent field (e.g., NLP or general ML) might stumble on terms like "Q-formers," "SSCD," and the abbreviation "pp" (percentage points), as these are not universal standard vocabulary across the broader discipline.

Specifically, "Q-formers" appears in the Related Work without explanation, assuming the reader knows the specific architecture of BLIP-2. Similarly, "SSCD" is introduced as a proper noun for a specific descriptor model without expanding the acronym or briefly explaining its function beyond "copy-detection." The use of "pp" for percentage points is a common source of confusion for non-specialists who might interpret it as a relative percent change. Finally, "MTL" is used as a category label for benchmarks; while likely "Multilingual" here, the ambiguity with "Multi-Task Learning" creates a potential barrier to immediate comprehension.

These are minor, easily fixable issues that do not detract from the paper's quality but are necessary to ensure the work is accessible to the "adjacent-field PhD" standard required by the review panel. Defining these terms at first use would eliminate the need for the reader to guess or search external sources.
