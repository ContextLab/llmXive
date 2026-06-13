---
action_items:
- id: 4e9fd141cbb4
  severity: science
  text: No statistical significance tests reported for benchmark comparisons. Tables
    show point estimates only (e.g., LongBench Avg 54.24% vs 53.80% Full Attn) without
    p-values or confidence intervals. Add paired t-tests or bootstrap CIs across benchmark
    samples.
- id: d94c53874492
  severity: science
  text: Multiple comparisons problem unaddressed. Paper reports results across 16
    LongBench sub-benchmarks, 9 RULER tasks, and 9 reasoning benchmarks without correction
    (Bonferroni/FDR). Claim of 'near-lossless accuracy' is statistically unsupported.
- id: 9d1e72b5ee65
  severity: science
  text: Speedup measurements (9.36x, 2.01x) reported as single point estimates with
    no variance, standard deviation, or confidence intervals. Hardware benchmarking
    requires repeated measurements for statistical validity.
- id: 97c39903cdc3
  severity: science
  text: Head calibration stability claim ('one single long text sequence is sufficient',
    Section 3.1) lacks statistical evidence. No variance analysis across documents
    or power analysis justifying single-sequence sufficiency.
- id: a0ac75071d29
  severity: science
  text: Training reproducibility incomplete. No random seeds reported, no variance
    across multiple training runs, and no justification for 600 steps/1.2M label tokens
    via power analysis. Appendix D provides hyperparameters but not reproducibility
    guarantees.
artifact_hash: 2cdfc78b07a5bd64c78a8db6e3f4311cd8e2ebe3c52393699df0143a39308f60
artifact_path: projects/PROJ-617-full-attention-strikes-back-transferring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T07:27:20.444815Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on statistical analysis aspects of the manuscript.

**Statistical Significance and Variance Reporting**

The paper presents extensive benchmark comparisons (LongBench with 16 sub-tasks, RULER with 9 sub-tasks, and multiple reasoning benchmarks) but reports only point estimates without any measure of statistical uncertainty. For instance, Table 1 shows RTPurbo w/ top-p achieving 54.24% average on LongBench versus 53.80% for Full Attention, but no confidence intervals or p-values are provided to assess whether this difference is statistically meaningful. Similarly, Table 4 reports reasoning benchmark scores (e.g., AIME24: 86.67% vs 86.67% Full Attn) without indicating whether these are single-run results or averaged across multiple seeds.

**Multiple Comparisons Problem**

The manuscript conducts numerous statistical comparisons without addressing the multiple comparisons problem. Across LongBench, RULER, and reasoning benchmarks, there are approximately 34 distinct task comparisons. Without correction (Bonferroni, Holm, or FDR), the probability of at least one false positive claim is substantially inflated. The claim of "near-lossless accuracy" (Abstract) is particularly problematic given that some individual sub-benchmarks show noticeable drops (e.g., RULER 64K multi-K: 98.60% vs 99.66% Full Attn).

**Speedup Measurements**

The speedup claims (9.36× prefill at 1M context, 2.01× decode at 1M context, Figure 1) are presented without any variance measures. Hardware benchmarking inherently has measurement noise; standard practice requires reporting mean±std across multiple runs with different random seeds. The absence of this information undermines the reproducibility and statistical validity of efficiency claims.

**Head Calibration Stability**

Section 3.1 states that "running this calibration on just one single long text sequence is sufficient to robustly score and partition all query heads." This is a strong statistical claim requiring empirical support. The Appendix A.1 shows head retrieval score heatmaps but does not quantify stability across documents (e.g., coefficient of variation, intraclass correlation). A proper analysis would report variance in retrieval scores across multiple calibration documents and demonstrate that single-sequence calibration achieves equivalent partitioning quality.

**Training Reproducibility**

Appendix D provides training hyperparameters but omits critical reproducibility information: random seeds, number of training runs per configuration, and whether results represent single runs or averages. The claim that "only 600 steps" are sufficient for self-distillation lacks statistical justification—no power analysis or learning curve analysis demonstrates this is the minimum required.

**Recommendations**

1. Add paired t-tests or bootstrap confidence intervals for all benchmark comparisons
2. Apply multiple comparisons correction when claiming overall superiority
3. Report speedup measurements with variance (mean±std across ≥3 runs)
4. Provide statistical evidence for head calibration stability (variance across documents)
5. Include random seeds and run counts in Appendix D for reproducibility
