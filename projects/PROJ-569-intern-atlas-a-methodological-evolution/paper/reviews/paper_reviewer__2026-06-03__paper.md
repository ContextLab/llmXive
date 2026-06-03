---
action_items:
- id: 27cca22eabe3
  severity: science
  text: Provide quantitative error propagation analysis showing how the 70.4% Phase-1
    extraction accuracy impacts downstream idea evaluation scores and lineage reconstruction
    reliability.
- id: d79ed99fe928
  severity: writing
  text: Confirm verification_status for all bibliography entries in state/citations/PROJ-569-intern-atlas-a-methodological-evolution.yaml
    or update ref.bib to include DOIs/URLs for all entries.
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: Minor revisions needed on extraction error analysis and bibliography verification
  status.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T07:42:53.045266Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

# Free-form review body

## Strengths
- **Ambitious Scale and Infrastructure Focus:** The paper proposes a significant shift from document-centric to method-centric research infrastructure, addressing a critical gap for AI-driven research agents. The scale (1M+ papers, 9M+ edges) is impressive for this domain.
- **Strong Empirical Validation:** The evaluation suite is comprehensive, covering intrinsic graph quality (vs. survey benchmarks), lineage reconstruction (SGT-MCTS vs. baselines), and downstream utility (idea evaluation/generation). The results consistently favor Intern-Atlas over baselines.
- **Verifiable Evidence:** The requirement for verbatim quotes for bottleneck and mechanism annotations on every causal edge provides a strong audit trail, enhancing trust in the extracted relationships.
- **Clear Methodological Pipeline:** The two-phase extraction protocol and the SGT-MCTS algorithm are well-documented with hyperparameters and mathematical formulations provided in the main text and appendices.

## Concerns
- **Extraction Accuracy vs. Foundational Claims:** The Phase-1 edge classification accuracy is reported as 70.4% (production model). For a system positioned as "foundational data layer," this error rate is non-trivial. While confidence scores are used, the paper lacks a quantitative analysis of how these errors propagate to the downstream idea evaluation and generation tasks.
- **Bibliography Verification Status:** The `accept` criteria require all cited references to have `verification_status: verified`. The provided input includes `ref.bib` but does not include a `bibliography_summary` with explicit verification statuses. Some entries (e.g., `google_scholar`) lack DOIs or stable URLs.
- **Temporal Consistency:** The paper cites conferences and papers from 2025 and 2026 (e.g., `ICLR 2026`, `NeurIPS 2025`). While the arXiv ID (`2604.28158`) suggests a 2026 submission context, this requires explicit clarification for readers to ensure they understand the temporal setting of the evaluation data (Strata Dataset).
- **Benchmark Representativeness:** The method-evolution benchmark is derived from only 30 survey papers. While high-quality, this sample size may not fully capture the diversity of methodological evolution across all AI subfields.

## Recommendation
The paper presents a compelling and well-evaluated infrastructure for methodological evolution. The core contribution is novel and the experimental results are strong. However, to meet the `accept` criteria, the authors must address the verification status of the bibliography and provide a deeper analysis of how the extraction error rate impacts the reliability of the downstream operators. These are manageable revisions that do not require re-running the core research pipeline. I recommend `minor_revision`.
