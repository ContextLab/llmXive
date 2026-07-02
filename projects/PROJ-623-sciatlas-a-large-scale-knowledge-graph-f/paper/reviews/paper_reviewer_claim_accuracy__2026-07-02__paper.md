---
action_items:
- id: 50a94e8f1662
  severity: writing
  text: Table 1 (e001) lists CITES edges as 1.2B and COAUTHOR as 800M, but Table 1
    (e000) and the text (e000) state 213.88M CITES and 2.06B COAUTHOR. These are direct
    contradictions. The authors must reconcile these numbers and ensure the table
    matches the text.
- id: fcd85e5a8e8b
  severity: writing
  text: The abstract and introduction claim the KG contains '3B triplets' (edges),
    but the sum of the specific edge counts provided in the detailed table (e000)
    is approximately 2.8B. The authors should clarify if '3B' is a rounded estimate
    or if the detailed counts are incomplete.
- id: af4d5cb3df43
  severity: writing
  text: The paper cites 'Qwen3-30B-A3B-Instruct' (e001) and 'Qwen3' (e000). As of
    the current date, Qwen3 is not a publicly released model family (Qwen2.5 is the
    latest). The authors must verify the model name/version or provide a citation
    if this is a pre-release/internal model.
- id: 76e66537ac95
  severity: writing
  text: The bibliography lists the OpenAlex URL (c-001) as 'unreachable'. While external
    links can change, the authors should verify the stability of the data source link
    or provide a DOI/Archive link for the specific snapshot used.
artifact_hash: f3ce028cf68a2eb124d9418ea236e7f52f710c30a6edb26c69bffcf6c534c941
artifact_path: projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T07:05:13.924659Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript presents a large-scale knowledge graph (SciAtlas) and a retrieval pipeline. While the core concept is sound, there are significant factual inconsistencies regarding the dataset statistics and citation accuracy that must be resolved before acceptance.

**1. Contradictory Statistics:**
There is a direct conflict between the detailed statistics provided in the text and the summary table in the second chunk (e001).
- In **e000** (Section "Statistics" and Table 1), the paper states there are **213.88M** `CITES` relations and **2.06B** `COAUTHOR` relations.
- In **e001** (Table 1), the same table lists **1.2B** `CITES` and **800M** `COAUTHOR`.
These numbers are not just slightly different; they are orders of magnitude apart and contradict each other directly. The `COAUTHOR` count in e001 (800M) is less than half the count in e000 (2.06B), while the `CITES` count in e001 (1.2B) is nearly six times higher than in e000 (213.88M). The authors must unify these figures across the manuscript.

**2. "3 Billion Triplets" Claim:**
The abstract and introduction claim the graph contains "3B triplets" (edges). However, summing the specific edge counts provided in the detailed table in **e000** (213.88M + 101.38M + 105.89M + 149.00M + 195.94M + 2.06B + 60.37M + 252 + 68.38M + 40.90M + 26) yields approximately **2.83B**. While "3B" is a reasonable rounded figure, the discrepancy with the contradictory numbers in e001 (where the sum would be vastly different) makes the claim ambiguous. The authors should clarify if the 3B figure is an upper bound, a rounded total, or if the detailed counts are missing a significant category.

**3. Citation Validity (Qwen3):**
The paper cites `Qwen3-30B-A3B-Instruct` (e001) and `Qwen3` (e000) as the keyword extraction model. As of the current date, the Qwen3 series has not been publicly released (Qwen2.5 is the latest stable version). Unless this is a specific internal or pre-release model with a verifiable technical report, this citation is likely hallucinated or premature. The authors must verify the model name and provide a valid citation or correct the model version to the actual one used (e.g., Qwen2.5).

**4. Data Source Availability:**
The bibliography entry for OpenAlex (c-001) is flagged as "unreachable". While external links can rot, the authors should ensure the primary data source link is stable or provide a DOI/Archive link for the specific data snapshot used to construct the graph to ensure reproducibility.

These issues are primarily writing and factual consistency errors that can be fixed by cross-referencing the data generation logs and updating the text/tables accordingly.
