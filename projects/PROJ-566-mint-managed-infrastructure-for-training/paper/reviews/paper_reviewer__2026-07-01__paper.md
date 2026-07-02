---
action_items:
- id: a70350dc3754
  severity: writing
  text: 'Resolve uncompiled LaTeX: The source contains raw TikZ code (e.g., `figures/changhai_cold_admission_staircase.tex`)
    and missing `\input` targets (e.g., `tables/scaling/supported_model_families`)
    that prevent PDF generation. The paper must compile cleanly before review.'
- id: c3375bcec39e
  severity: writing
  text: 'Fix bibliography verification: Multiple citations (e.g., `yao_second_half_2025`,
    `deepseek_v4_release_2026`, `kimi_k25_2026`) reference internal blogs or unreleased
    technical reports without stable DOIs or arXiv IDs. Verify all references or replace
    with publicly accessible, peer-reviewed sources.'
- id: 538b10a9ad00
  severity: writing
  text: 'Clarify ''Millions'' claim: The title and abstract claim support for ''Millions
    of LLMs'' (policies), but the evaluation section only demonstrates a 100k catalog
    sweep and a theoretical 1M extrapolation. The title should be qualified (e.g.,
    ''...Millions of Policies'') or the evaluation must include a 1M+ scale measurement.'
- id: 06c64f6e2ea7
  severity: writing
  text: 'Standardize citation format: The bibliography mixes arXiv preprints, blog
    posts, and internal ''Mind Lab'' reports. Ensure all citations follow a consistent,
    verifiable format suitable for public archival (e.g., arXiv or conference proceedings).'
artifact_hash: 9b74dd1f4b8f2d4815ea056f5e26899cdd80d0bb7bac2914c7ef2512791b5d74
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: Paper contains uncompiled LaTeX, missing bibliography entries, and unverified
  citations preventing publication readiness.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T19:59:10.522687Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_writing
---

# Free-form review body

## Strengths
- **Novel Infrastructure Abstraction:** The core concept of treating LoRA adapters as the primary unit of policy management (separating the "base" from the "behavior") is a compelling and timely contribution to the LLM infrastructure space. It directly addresses the scaling bottleneck of managing thousands of fine-tuned variants.
- **Comprehensive System Design:** The paper provides a detailed architectural breakdown of the "Scale Up" (Megatron/MoE), "Scale Down" (adapter-only handoff), and "Scale Out" (policy population) axes. The distinction between the "addressable catalog," "CPU cache," and "GPU batch" is a clear and useful mental model for multi-LoRA serving.
- **Strong Empirical Validation of Mechanisms:** The evaluation section effectively isolates the system-level benefits of the proposed architecture. The "Scale Down" results (18.3x handoff speedup) and the "Scale Out" results (packed loader reducing load time by 8.5x) are concrete, measurable improvements that validate the design choices.
- **Handling of Edge Cases:** The paper thoughtfully addresses complex issues like MoE router replay (R3) and Dynamic Sparse Attention (DSA) mismatches, acknowledging the limitations of current replay mechanisms and proposing mitigation strategies (IcePop-style correction).

## Concerns
- **Uncompiled Source and Missing Artifacts:** The provided LaTeX source is not in a state ready for compilation. It includes raw TikZ code files that are not properly included in the main document structure, and references to tables (e.g., `tables/scaling/supported_model_families`) that are not fully integrated or defined in the provided snippets. A paper cannot be reviewed if it does not compile.
- **Citation Integrity and Verification:** A significant portion of the bibliography consists of internal "Mind Lab" blog posts, unreleased technical reports, or future-dated arXiv preprints (e.g., `2605.13779` in 2026). For a public submission, these must be replaced with stable, verifiable references. The current state fails the "verification_status: verified" requirement for all citations.
- **Title vs. Evidence Mismatch:** The title claims "Millions of LLMs," which is ambiguous. The text clarifies this refers to "policy revisions" (adapters), not distinct base models. However, the empirical evidence only goes up to 100k entries with a theoretical extrapolation to 1M. The title should be more precise (e.g., "Millions of Policies") to avoid overclaiming based on the provided data.
- **Reproducibility of "Cookbook" Claims:** The paper relies heavily on the "MinT Cookbook" and "Tinker" framework for reproducibility. While the API is described, the actual recipes and the specific "mint-cookbook" repository state are not provided in the source, making independent verification of the "public reproducibility paths" claim difficult without external access.

## Recommendation
The paper presents a strong systems contribution with clear architectural insights and promising empirical results. However, it is currently **not publication-ready** due to critical formatting and verification issues. The LaTeX source fails to compile, the bibliography contains unverified/internal references, and the title makes a claim ("Millions") that is only theoretically supported rather than empirically demonstrated in the main text.

The paper requires a **major revision of the writing and structure** to address these foundational issues. Specifically, the authors must:
1.  Ensure the LaTeX source compiles cleanly with all figures and tables properly included.
2.  Replace internal/unverified citations with stable, public references.
3.  Refine the title and abstract to accurately reflect the scale of the empirical evidence (100k measured, 1M extrapolated).
4.  Provide a clear path for external reproducibility of the "Cookbook" claims.

Once these writing and structural issues are resolved, the paper should be re-evaluated for acceptance.
