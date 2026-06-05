---
action_items:
- id: feab0c7fdc84
  severity: writing
  text: Define all acronyms at first use (IoU, RAG, SFT, CoT, LLM, VQA, QA). Currently
    used without definition in Section 4.1 and Appendix.
- id: f22368cde61f
  severity: writing
  text: Replace dense jargon in evaluation metrics section (Section 4.1). Terms like
    "Traceability Metrics," "element-level bounding-box citations," and "masking ablation"
    need plain-language alternatives or definitions.
- id: 380a5e3ea5e2
  severity: writing
  text: "Simplify technical terms in Appendix sections (e.g., \"bijective function\"\
    \ \u2192 \"one-to-one mapping,\" \"semantic truncation\" \u2192 \"meaning loss,\"\
    \ \"heterogeneous data\" \u2192 \"mixed data types\")."
artifact_hash: 343bba3cbfbb16bee3f79c8a33c3a51555292623f2cdbd016ca7ae51e6fbc39c
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T21:47:07.547637Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

**Jargon Overuse Review — CiteVQA Paper**

This manuscript contains significant jargon density that may exclude non-specialist readers. Below are specific concerns:

**Acronyms Not Defined at First Use**
- **IoU** (Intersection over Union): Used in Section 4.1 without definition. First-time readers unfamiliar with computer vision metrics will be lost.
- **RAG** (Retrieval-Augmented Generation): Appears in Related Work without definition.
- **SFT** (Supervised Fine-Tuning): Used in Appendix Auxiliary Training Validation without definition.
- **CoT** (Chain-of-Thought): Appears in Appendix without definition.
- **LLM** (Large Language Model): Used frequently but not consistently defined at first mention in each section.
- **VQA/QA**: Used interchangeably without clear distinction.

**Jargon That Could Be Simplified**
| Original Term | Location | Suggested Alternative |
|---------------|----------|----------------------|
| "element-level bounding-box citations" | Abstract, Introduction | "specific region citations" |
| "Traceability Metrics" | Introduction (line 45) | "tracking metrics" |
| "Attribution Hallucination" | Abstract, Introduction | "misattributed evidence" (define as a coined term) |
| "masking ablation" | Abstract, Section 3.3 | "systematic removal testing" |
| "bijective function" | Appendix | "one-to-one mapping" |
| "semantic truncation" | Appendix | "meaning loss" |
| "heterogeneous data" | Section 3.1 | "mixed data types" |
| "stratified sampling" | Section 3.1 | "layered sampling" |
| "semantic alignment" | Section 3.2 | "meaning matching" |
| "ground-truth" | Throughout | "correct answer" or "verified reference" |
| "pseudo-faithful behavior" | Section 5.1 | "seemingly faithful behavior" |
| "logical fracture" | Section 1 | "reasoning gap" |
| "instrumentation" | Abstract | "tools" or "methods" |

**Overuse of Coarse-grained/Fine-grained**
These terms appear 20+ times throughout the paper. Varying language (e.g., "broad" vs. "detailed," "general" vs. "precise") would improve readability without sacrificing precision.

**Mathematical Notation Without Plain-Language Explanation**
Section 4.1 presents four evaluation metrics with formulas. Each should include a one-sentence plain-language summary (e.g., "Recall measures whether the model found the correct evidence region").

**Recommendation**
Add a "Glossary of Terms" section or ensure all technical terms are defined at first use with parenthetical plain-language explanations. This is especially critical for the evaluation metrics section, which is central to the paper's contribution.
