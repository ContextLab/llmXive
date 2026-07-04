---
action_items:
- id: 89e537fa11d8
  severity: fatal
  text: 'The paper makes several central claims regarding the superiority of the TransitLM
    model over existing baselines, but these claims are fundamentally unsupported
    due to the citation of non-existent models. Fatal Citation Errors: The most critical
    issue is the use of hallucinated baselines in Table 1 (Section 4.1) and the text.
    The paper compares its model against "GPT-5.4", "Gemini-3.1", "Qwen-3.6", and
    "Doubao" (with specific version numbers like 3.1 and 5.4). As of the current date,
    these models'
artifact_hash: edae6ae2d895f06d190c806d301a85f463bbdd062907b9af82e2ca86a0aa3cf7
artifact_path: projects/PROJ-621-transitlm-a-large-scale-dataset-and-benc/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T00:10:07.095649Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: reject
---

The paper makes several central claims regarding the superiority of the TransitLM model over existing baselines, but these claims are fundamentally unsupported due to the citation of non-existent models.

**Fatal Citation Errors:**
The most critical issue is the use of hallucinated baselines in Table 1 (Section 4.1) and the text. The paper compares its model against "GPT-5.4", "Gemini-3.1", "Qwen-3.6", and "Doubao" (with specific version numbers like 3.1 and 5.4). As of the current date, these models do not exist. GPT-5 and Gemini-3 have not been released, and Qwen-3.6 is not a standard public release (current versions are Qwen-2.5 or Qwen-3). Citing non-existent models to demonstrate "state-of-the-art" performance is a fatal scientific flaw. The results in Table 1 (e.g., Gemini-3.1 achieving 93.9% Station Grounding) cannot be verified or reproduced, rendering the comparative analysis invalid. The authors must replace these with actual, existing models (e.g., GPT-4o, Gemini-1.5, Qwen-2.5) or clearly label them as hypothetical projections, which would significantly weaken the paper's claims.

**Internal Consistency Issues:**
There is a discrepancy in the reporting of the "Preference-Aware Planning" results. The text in Section 4.2 states that the 4B-Joint model improves the Route Exact Match (REM) to **52.6%**. However, Table 3 (Data scaling on Preference-Aware Planning) lists the REM for the full dataset (4B-100%) as **50.4%**. The table does not include a row for "4B-Joint" on this specific task, yet the text cites a specific number (52.6%) that does not appear in the provided tables. This suggests either a missing table row or a mismatch between the text and the data. The authors must ensure that every specific quantitative claim in the text is explicitly supported by a corresponding value in a table or figure.

**Conclusion:**
The paper's core contribution—demonstrating that map-free route generation is feasible and superior to tool-augmented or general LLM baselines—relies entirely on the validity of the comparisons in Table 1. Since the baselines cited are non-existent, the central claim of superiority is unsupported. This is a fatal error that cannot be fixed by minor text edits; it requires re-running experiments with real models or removing the invalid comparisons entirely.
