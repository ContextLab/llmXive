---
action_items:
- id: 1cb771987d1a
  severity: writing
  text: The logical consistency of the proposed method relies heavily on the equivalence
    between the proposed MSE objective and a KL-divergence minimization, as well as
    the linearity of the guidance field composition. First, in Section 3.4 and Appendix
    A.1, the authors derive that minimizing the KL divergence between the student
    and teacher transition kernels reduces to a velocity MSE objective. This derivation
    explicitly assumes that the student and teacher share the same local covariance
    ($\sigma_t^2
artifact_hash: 345c406695aa2dde1374386d01dde68941ce2b695d941d4807a3dc21f8ee698f
artifact_path: projects/PROJ-797-danceopd-on-policy-generative-field-dist/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:39:11.787327Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the proposed method relies heavily on the equivalence between the proposed MSE objective and a KL-divergence minimization, as well as the linearity of the guidance field composition.

First, in Section 3.4 and Appendix A.1, the authors derive that minimizing the KL divergence between the student and teacher transition kernels reduces to a velocity MSE objective. This derivation explicitly assumes that the student and teacher share the **same local covariance** ($\sigma_t^2 I$). While this is a standard assumption in flow matching, the paper does not logically justify why the student's on-policy rollout distribution (which is being actively trained) would maintain the same local covariance structure as the frozen teacher field, especially given that the student is learning to compose conflicting capabilities. If the student's local variance differs significantly from the teacher's, the MSE objective is no longer the exact maximum likelihood estimator for the KL divergence, introducing a potential logical gap between the theoretical motivation and the practical objective.

Second, regarding the CFG absorption results in Section 4.1.D, the paper argues that the effective guidance strength is the product $\alpha\beta$ (Eq. 14 in Appendix A.8). This logic holds strictly only if the student $v_\theta$ perfectly approximates the guided teacher field $v_\alpha$ (i.e., $v_\theta \approx v_\alpha$). The paper presents empirical evidence of "over-guidance" when $\alpha\beta$ is large but does not provide a logical bound or analysis of how approximation errors in $v_\theta$ propagate through the composition $v_{\emptyset} + \beta(v_\theta - v_{\emptyset})$. If the student fails to perfectly absorb the teacher, the resulting field is not a simple affine scaling, and the claim that the performance drop is solely due to the $\alpha\beta$ magnitude is an oversimplification that lacks rigorous support in the text.

Finally, the argument that "dense trajectory queries" fail due to "trajectory-query correlation" (Sec 3.3) is logically sound in principle, but the paper assumes that the correlation $\rho$ is high enough to negate the variance reduction of averaging $K$ samples. While the SDE decorrelation experiment supports this, the paper does not explicitly quantify the correlation coefficient $\rho$ in the ODE rollout case to prove that the variance reduction factor $1+(K-1)\rho$ is indeed close to $K$ (i.e., $\rho \approx 1$). Without this quantitative link, the leap from "states are correlated" to "dense queries are strictly worse than single queries" remains a qualitative assertion rather than a derived necessity.
