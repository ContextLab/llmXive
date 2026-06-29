---
action_items:
- id: 3add6fa9f58b
  severity: writing
  text: 'Verify that every cited reference in the bibliography has `verification_status:
    verified`. Update the bibliography_summary accordingly.'
- id: a8736b45680d
  severity: writing
  text: Replace LaTeX macros such as \numvideo, \numturn, \numsubmetric, etc., with
    their actual numeric values in the main text (or ensure they are defined in the
    preamble) so readers of the source can understand the scale without compilation.
- id: 12881898af29
  severity: writing
  text: "Provide public URLs or repository links for all external models used in the\
    \ evaluation suite (e.g., Doubao\u2011Seed\u20112.0\u2011lite, MegaSaM, Qwen3\u2011\
    VL\u201130B\u2011A3B) and include version identifiers to enable exact replication."
- id: a306d450a976
  severity: writing
  text: "Add a reproducibility checklist in the appendix that lists code, model weights,\
    \ prompts, and evaluation scripts required to compute each sub\u2011metric, and\
    \ indicate any licensing restrictions."
- id: 2d8a46e0e6e8
  severity: writing
  text: "Clarify the process for generating ground\u2011truth navigation trajectories\
    \ (GT) in the NavScore metric, including any hyper\u2011parameters or fallback\
    \ rules, to ensure the method can be re\u2011implemented by other researchers."
artifact_hash: 583182a56bc8cd93d801cd098b02d980b9a48cb375dac6cc8130da68f508615f
artifact_path: projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/paper/metadata.json
backend: dartmouth
feedback: minor writing and reproducibility fixes needed
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T05:35:21.260807Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

## Strengths
- Introduces a comprehensive multi‑turn benchmark (WBench) that covers five important evaluation dimensions for interactive video world models, filling a clear gap in existing benchmarks.
- Provides a large and diverse dataset with detailed world settings (scene, style, perspective, subject) and four interaction types, enabling systematic comparison across models.
- Designs a rich suite of automatic sub‑metrics (over 30) spanning video quality, setting adherence, interaction adherence, consistency, and physical compliance, and validates them against extensive human preference data (Spearman ρ ≥ 0.94).
- Conducts thorough experiments on a wide range of state‑of‑the‑art models (text‑driven, camera‑controlled, action‑conditioned), revealing insightful findings about the trade‑offs between rendering quality, controllability, consistency, and physics.
- Includes extensive appendices with metric definitions, prompts, and additional results, supporting transparency.

## Concerns
- The bibliography verification status is not shown; the review cannot confirm that all citations are verified, which is required for an `accept`.
- Several evaluation components rely on proprietary or unpublished models (e.g., Doubao‑Seed‑2.0‑lite, MegaSaM, Qwen3‑VL‑30B‑A3B). Their availability and exact versions are not documented, which hampers reproducibility.
- The main manuscript contains placeholder macros (`\numvideo`, `\numturn`, `\numsubmetric`, etc.) that are not expanded in the source view, making the text harder to read without compilation.
- While metric prompts are provided, the paper does not include a consolidated reproducibility checklist (code repository, model weights, exact prompt strings) that would allow other researchers to re‑run the benchmark end‑to‑end.
- The description of the ground‑truth navigation trajectory construction (GT) in the NavScore metric is complex and could benefit from a clearer algorithmic summary and hyper‑parameter listing.

## Recommendation
The paper presents a valuable and well‑executed benchmark that will likely become a standard reference for interactive video world model evaluation. However, to meet the strict acceptance criteria, the authors should address the minor writing and reproducibility issues listed above, especially ensuring all citations are verified and providing clear access information for the external models used in the evaluation suite. After these revisions, the manuscript should be ready for acceptance.
