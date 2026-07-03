---
action_items:
- id: b14024b037fa
  severity: science
  text: The claim that KVarN achieves 'SOTA' on AIME24, MATH500, HumanEval, and IFEval
    (Abstract, Conclusion) is overreaching. Table 1 and Table 3 show KVarN matches
    or slightly exceeds baselines (e.g., +0.1% on AIME24, +0.1% on IFEval Strict)
    but does not demonstrate a statistically significant or substantial improvement
    over all SOTA methods, particularly given the small margins and standard deviations.
- id: ead292f4669d
  severity: writing
  text: The paper claims 'substantial improvement' (Contributions, Introduction) and
    'best performance' (Experiments) based on differences often within the noise margin
    (e.g., 60.0% vs 55.5% on AIME24 is significant, but 80.4% vs 80.3% on IFEval is
    not). The language should be tempered to reflect 'competitive' or 'comparable'
    performance where margins are negligible, reserving 'substantial' for clear wins.
- id: 5650c854b7d5
  severity: science
  text: The assertion that 'outlier errors contribute disproportionally to end-to-end
    quality' (Contributions) is supported by Fig. 3 (KL divergence) but the paper
    extrapolates this to claim that fixing *only* magnitude errors (via VarN) is the
    *sole* reason for the performance gains. It does not rule out that the Sinkhorn
    iterations might also be stabilizing the distribution in ways not captured by
    the simple magnitude/direction decomposition.
- id: e890f75010b4
  severity: writing
  text: The runtime overhead claim of '0.18%' (Abstract, Conclusion) is derived from
    a specific micro-benchmark (1.9ms vs 1050ms). Extrapolating this to a general
    'negligible overhead' for all inference scenarios is an overreach, as the relative
    cost of normalization may increase significantly for shorter sequences or different
    hardware configurations not tested.
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:18:26.988914Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the immediate evidence provided in the results.

First, the use of the term "SOTA" (State-of-the-Art) and "substantial improvement" in the Abstract, Contributions, and Conclusion is an overreach. While the method performs well, the quantitative results in Tables 1, 2, and 3 show margins that are often marginal or within the standard deviation of the baselines. For instance, on IFEval (Table 3), KVarN achieves 80.4% vs. KIVI's 80.3% (Strict) and 83.4% vs. 83.2% (Loose). These differences are statistically indistinguishable given the reported variances (e.g., $\pm 0.3\%$). Claiming "substantial improvement" or "best performance" across the board for such narrow margins misrepresents the magnitude of the gain. The authors should qualify these claims, perhaps stating "competitive performance" or "comparable to SOTA with lower bit-width" where the gains are not statistically significant.

Second, the causal link between "magnitude errors" and the observed performance gains is asserted too strongly. The paper decomposes error into magnitude and direction (Eq. 1) and shows magnitude errors dominate the top 5% outliers (Fig. 1a). It then claims KVarN's success is *because* it fixes these magnitude errors. However, the Sinkhorn-Knopp algorithm (VarN) is a complex iterative process that alters the entire distribution of the matrix, not just the magnitude of outliers. The paper does not provide an ablation study isolating the effect of the variance normalization from the Hadamard rotation or the specific iterative balancing to prove that *only* the magnitude correction is responsible for the end-to-end gains. The claim that "outlier errors contribute disproportionally" is supported by the KL-divergence analysis, but the leap to "therefore, fixing magnitude errors is the key" is an extrapolation not fully backed by the provided ablation data.

Third, the runtime overhead claim of "0.18%" is based on a specific measurement (1.9ms vs 1050ms) for a specific context length and batch size. Extrapolating this to a general claim of "negligible overhead" for all reasoning tasks is an overreach. In scenarios with shorter contexts or different hardware, the fixed cost of the Sinkhorn iterations could become a more significant fraction of the total latency. The paper should clarify the conditions under which this overhead holds or provide a sensitivity analysis.

Finally, the claim that KVarN is "not suitable for SSMs or MLA architectures" (Limitations) is a necessary limitation, but the paper does not discuss *why* the variance normalization specifically fails for these architectures beyond a brief mention. While this is a limitation, the broader claim that the method is universally applicable to "reasoning tasks" (Title/Abstract) might be slightly overreaching if the "reasoning" tasks tested are limited to standard Transformer-based benchmarks and do not include the specific long-context reasoning challenges where SSMs/MLA are often deployed.
