---
action_items:
- id: 44e3e4b7613e
  severity: science
  text: The abstract claims a sensitivity analysis on autocorrelation (rho=0.3) with
    results in Appendix~\ref{app:autocorr}, but the provided LaTeX source contains
    no such appendix section. This prevents verification of the bootstrap validity
    claims under dependence.
- id: f36b1ef1f06d
  severity: science
  text: Table 1 reports 95% bootstrap CI half-widths for the randomized oracle but
    omits CIs for the bidirectional oracle, stating it is 'deterministic given outcomes.'
    However, the experiment uses 8 oracle seeds; the variance across these seeds should
    be reported to distinguish algorithmic stability from oracle stochasticity.
- id: 52031221b953
  severity: writing
  text: "The 'Multiple-Testing Correction' section states Benjamini-Hochberg was applied\
    \ to Appendix Tables A.10\u2013A.11, but the provided source only contains Tables\
    \ A.1\u2013A.4 and significance tables A.5\u2013A.6. The specific tables referenced\
    \ for FDR control are missing or misnumbered."
artifact_hash: 8b4e5d074a64eaa78e7927259e08b3cc001daf353c2dc417958eda25d90e918a
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:12:51.829068Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis framework is generally sound, employing non-parametric bootstrapping (10,000 resamples) to handle the non-Gaussian nature of NDCG@10 distributions and paired tests to control for query-level variance. The randomized-direction oracle derivation (Appendix) correctly establishes unbiasedness in expectation, and the use of Benjamini-Hochberg for multiple comparisons is appropriate given the 9 budget points and multiple ranker pairs.

However, critical gaps in reproducibility and reporting prevent full acceptance. First, the abstract explicitly references a sensitivity analysis on autocorrelation (Appendix~\ref{app:autocorr}) to validate bootstrap assumptions under API non-stationarity. This section is entirely absent from the provided LaTeX source, making the claim that "95% confidence interval coverage remains within 2% of the nominal level" unverifiable. Second, Table 1 reports confidence intervals for the randomized oracle but explicitly omits them for the bidirectional oracle, claiming determinism. Yet, the methodology states 8 oracle seeds were used. If the bidirectional results vary across seeds (due to LLM stochasticity), omitting these CIs hides potential instability; if they are truly deterministic, the seed count is irrelevant and should be clarified. Finally, the "Multiple-Testing Correction" section references Tables A.10–A.11 for FDR control, but the source only includes Tables A.1–A.6. The specific tables containing the adjusted p-values are missing, preventing verification of the statistical significance claims.
