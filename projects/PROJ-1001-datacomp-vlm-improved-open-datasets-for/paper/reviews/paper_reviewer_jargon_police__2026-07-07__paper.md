---
action_items:
- id: ce2a18eef94b
  severity: writing
  text: The paper is generally well-written for its target audience, but it relies
    on several acronyms and subfield-specific terms that are not expanded at their
    first occurrence, potentially creating friction for a competent reader from an
    adjacent field (e.g., a computer vision researcher less familiar with NLP data
    curation, or vice versa). Specifically, the term "pp" (percentage points) in the
    abstract and results sections is used without definition. While intuitive to many,
    it is a specific statist
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:30:11.353665Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally well-written for its target audience, but it relies on several acronyms and subfield-specific terms that are not expanded at their first occurrence, potentially creating friction for a competent reader from an adjacent field (e.g., a computer vision researcher less familiar with NLP data curation, or vice versa).

Specifically, the term "pp" (percentage points) in the abstract and results sections is used without definition. While intuitive to many, it is a specific statistical shorthand that should be explicitly defined (e.g., "percentage points (pp)") to avoid ambiguity with "parts per" or other metrics.

The language detection metrics in Section 3.1 reference "Lingua" and "NLLB" without expansion. "NLLB" is a specific Meta project (No Language Left Behind), and "Lingua" is ambiguous without context (likely a specific library or model). These should be expanded to ensure the reader understands the source of the language statistics.

In the decontamination sections (4.1 and 4.2), the paper introduces "SSCD" (Self-Supervised Copy Detection) and "MinHash" without defining them. While FAISS is widely known in retrieval, SSCD is a more niche descriptor, and MinHash, while standard in NLP/IR, is not universal to all ML subfields. A brief gloss or expansion at first use would significantly improve accessibility for a cross-disciplinary reader.

Finally, ensure that "SFT" (Supervised Fine-Tuning) is expanded at its very first occurrence in the document. If it first appears in Section 5, it should be defined there, as it is a core methodological term.

These are minor, low-effort edits (adding parenthetical expansions) that would make the paper fully self-contained for the intended "adjacent-field PhD" audience.
