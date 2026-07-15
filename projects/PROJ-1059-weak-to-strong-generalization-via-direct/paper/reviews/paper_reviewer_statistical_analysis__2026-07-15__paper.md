---
action_items:
- id: 6c9a8c90987b
  severity: writing
  text: "Table 1 and Section 4.1 report single-point accuracy (e.g., 58.3%) without\
    \ uncertainty metrics (SD/SE/CI) or seed counts. Report mean \xB1 SD over \u2265\
    3 seeds for all main results to distinguish signal from noise."
- id: 6d9133646670
  severity: science
  text: "Section 4.2 claims Direct-OPD 'outperforms' direct RL based on single runs.\
    \ Report mean \xB1 SD over \u22653 seeds for both methods to statistically validate\
    \ the comparative claim."
artifact_hash: fe03c20c23e17e66c41241fcf88a5ad32b5f8c89483ca27ec649ff3d3b355988
artifact_path: projects/PROJ-1059-weak-to-strong-generalization-via-direct/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T02:40:06.074887Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents a novel method for weak-to-strong generalization, but the statistical reporting of quantitative results is insufficient to support the strength of the claims.

**Missing Uncertainty Reporting:**
Throughout Section 4 and Table 1, the authors report single-point accuracy metrics (e.g., "58.3% on AIME 2024") without mentioning the number of random seeds used or providing standard deviations (SD), standard errors (SE), or confidence intervals (CI). In LLM training, performance varies due to initialization and sampling stochasticity. Reporting a single number implies unjustified precision. The field standard is to report mean ± SD over at least 3 independent seeds. Without this, it is impossible to determine if improvements (e.g., +10.0%) are robust or artifacts of a specific seed.

**Comparative Claims Without Variance:**
In Section 4.2, the claim that Direct-OPD "outperforms step-matched direct RL" relies on comparing single trajectories in Figure 3. Since both methods are stochastic, a single-run comparison is statistically weak. To validly claim one method "outperforms" another, the authors must demonstrate consistent performance differences across multiple runs. The current presentation precludes hypothesis testing (e.g., paired t-tests) and does not allow readers to assess distribution overlap.

**Recommendation:**
The authors should re-run main experiments with at least 3 random seeds and report mean ± SD in all tables and figures. If variance is low, point estimates may suffice with a note; if high, the "outperforms" claim requires statistical support. This is a writing fix if data exists, or a science fix if new runs are needed.
