---
action_items:
- id: 1e2fed8cc2ee
  severity: fatal
  text: 'Table 1 (Data Engineering) contains a fatal statistical error: ''Optimized''
    hours (e.g., 18,332.7) exceed ''Baseline'' (612.0), yet the text claims a 29.9x
    speedup. The units or values are inverted. Correct the data presentation immediately.'
- id: 60f867d12e72
  severity: science
  text: Benchmark results (Tables 2-5) report point estimates without confidence intervals,
    standard deviations, or p-values. Given the claimed 'state-of-the-art' margins
    (e.g., 9.30 vs 9.26), statistical significance testing is required to validate
    these differences.
- id: 063abff0bd9c
  severity: science
  text: "The theoretical section (Sec 3) derives excess risk bounds but fails to empirically\
    \ validate these bounds on the test set. The connection between the theoretical\
    \ $\rho < 1$ contraction condition and the observed long-horizon performance is\
    \ missing."
- id: 8d6e77ddde1f
  severity: science
  text: Human evaluation win rates (e.g., 60.2%, 74.1%) are presented without sample
    sizes (N) or statistical significance tests (e.g., binomial test). The reliability
    of these claims cannot be assessed.
artifact_hash: 926e7dfe86ab0c8e4b8d20a90a842eec681ad7b82ae76075a7b3082533c6260d
artifact_path: projects/PROJ-740-kairos-a-native-world-model-stack-for-ph/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T11:52:29.771995Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the manuscript is currently insufficient to support the paper's central claims of "unprecedented execution fidelity" and "state-of-the-art" performance. Several critical issues must be addressed:

**1. Data Engineering Metrics (Table 1):**
There is a fundamental error in the presentation of throughput data in Table 1 (Section "Data Engineering Infrastructure"). The table lists "Baseline" as 612.0 hours and "Optimized" as 18,332.7 hours for Frame Filtering, yet claims a "29.9x speedup." Mathematically, if the optimized time is higher, the process is slower, not faster. It is highly probable the units are inverted (e.g., hours processed per day vs. hours to process a fixed dataset) or the values are swapped. This error invalidates the quantitative claim of a 30x throughput improvement. The units and values must be corrected and clearly defined.

**2. Lack of Statistical Significance in Benchmarks:**
The evaluation section (Section "Evaluation Results") relies entirely on point estimates. For instance, in Table 2 (WorldModelBench), Kairos scores 9.30 compared to Cosmos3-Nano's 9.26. Without reporting standard deviations, confidence intervals, or results from statistical significance tests (e.g., paired t-tests or Wilcoxon signed-rank tests across multiple seeds), it is impossible to determine if this 0.04 difference is meaningful or within the noise floor of the evaluation protocol. This applies to all benchmark tables (Tables 2, 3, 4, 5).

**3. Human Evaluation Methodology:**
The paper reports human win rates (e.g., "60.2% vs Cosmos-Predict2.5-14B") but omits the sample size ($N$) of the human evaluators and the number of comparisons made. Without $N$, the confidence interval for these proportions cannot be calculated. A win rate of 60.2% with $N=50$ is statistically weak, whereas $N=500$ is robust. The manuscript must include the sample size and a p-value to validate the superiority claim.

**4. Theoretical-Empirical Gap:**
Section 3 ("Theoretical Analysis") provides rigorous bounds on excess risk based on the contraction factor $\rho$. However, the paper does not report the empirical value of $\rho$ achieved by the trained model, nor does it plot the observed excess risk against the theoretical bound. The claim that the model "recovers near-Bayes-optimal prediction" remains unverified by the provided data.

**5. Reproducibility of Variance:**
The ablation studies (e.g., "Human-Centric Data Scaling") show performance jumps (e.g., 9.08 to 9.25). It is unclear if these results are from a single run or an average of multiple seeds. Given the stochastic nature of diffusion training and data sampling, single-run results are not reproducible or reliable. The authors must report mean and standard deviation over at least 3 independent runs for all ablation studies.
