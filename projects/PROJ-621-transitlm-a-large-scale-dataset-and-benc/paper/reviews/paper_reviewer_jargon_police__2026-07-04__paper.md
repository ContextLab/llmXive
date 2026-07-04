---
action_items:
- id: 23e8ce354cf4
  severity: writing
  text: 'Section 5.2 (Evaluation Metrics): Acronyms SG, DP, LO, SSO, REM, and EA are
    introduced as abbreviations for metrics (e.g., ''Station Grounding (SG)'') but
    are never explicitly defined as acronyms in the text. While the expansion is provided,
    the acronym usage is inconsistent (e.g., ''MAPE'' is used without expansion).
    Define each acronym at first use (e.g., ''Station Grounding (SG)'') and ensure
    MAPE is expanded to ''Mean Absolute Percentage Error'' at first mention.'
- id: 14282e771f78
  severity: writing
  text: 'Section 5.1 (Task Definitions): The terms ''ORG'', ''PRG'', and ''DRG'' appear
    in Figure 2 caption (''TransitBench defines three evaluation tasks (ORG, PRG,
    DRG)'') but are never defined in the main text. The text describes the tasks (Optimal
    Route Generation, etc.) but does not map them to these acronyms. Add a sentence
    mapping the acronyms to the full task names.'
- id: 9fbe2af5cb57
  severity: writing
  text: 'Section 5.2 (Evaluation Metrics): The metric ''Route Exact Match'' is abbreviated
    as ''REM'' in the text and tables, but the text does not explicitly state ''Route
    Exact Match (REM)''. Similarly, ''Line Overlap'' and ''Station Sequence Overlap''
    are abbreviated as LO and SSO without explicit parenthetical definition in the
    prose. Ensure all metric acronyms are defined at first occurrence in the text.'
- id: a75d6c36cbcf
  severity: writing
  text: 'Section 6.1 (Experimental Setup): The term ''4B-Joint'' is used to refer
    to a specific model variant. While ''Joint'' is explained as ''fine-tuned on combined
    tasks'', the specific naming convention ''4B-Joint'' (implying the 4B parameter
    model) is introduced without a clear definition of the ''Joint'' suffix in the
    context of the model name. Clarify that ''4B-Joint'' refers to the 4B-parameter
    model trained on the combined task dataset.'
artifact_hash: edae6ae2d895f06d190c806d301a85f463bbdd062907b9af82e2ca86a0aa3cf7
artifact_path: projects/PROJ-621-transitlm-a-large-scale-dataset-and-benc/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T00:12:00.312010Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally accessible to a competent reader from an adjacent field (e.g., NLP or transportation systems), as core concepts like "Continual Pre-Training (CPT)" and "Supervised Fine-Tuning (SFT)" are standard or well-explained. However, there are several instances of undefined or inconsistently defined acronyms and shorthand that create minor friction for an outsider.

Specifically, Section 5.2 introduces a dense list of metric acronyms (SG, DP, LO, SSO, REM, EA) with their full names in parentheses, but the text does not consistently treat them as defined acronyms for subsequent use, and "MAPE" is used without expansion. This forces the reader to constantly cross-reference the list. Similarly, the acronyms ORG, PRG, and DRG appear in Figure 2 but are never explicitly mapped to their full task names in the main text, requiring the reader to infer the mapping from context. Finally, the model variant name "4B-Joint" is used frequently without a clear, explicit definition of the "Joint" component in the naming convention, though the context makes it understandable.

These issues are minor and easily resolved by adding a few parenthetical definitions or a mapping sentence. They do not obscure the core scientific contribution but do slightly increase the cognitive load for a non-specialist reader.
