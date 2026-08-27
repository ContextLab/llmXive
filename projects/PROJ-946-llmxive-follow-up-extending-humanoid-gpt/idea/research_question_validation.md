## Research-question validation

### Phenomenon-vs-method check

**Verdict**: concern

The question explicitly contrasts a specific class of models (Transformers) against another specific class (non-differentiable rule-based systems) to determine if the "performance gap" is irreducible. While this touches on the nature of motion representation, the framing is heavily fixated on the architectural properties (differentiability, scaling laws) rather than a pure domain phenomenon. It risks becoming a benchmark study on "which architecture handles X better" rather than a scientific inquiry into the fundamental limits of kinematic prediction.

### Circularity check

**Verdict**: pass

The predictor (kinematic state features like joint angles and velocities) and the predicted variable (teacher-generated joint trajectories) are derived from the same motion corpus but represent distinct stages in the distillation pipeline. The teacher model generates the target distribution based on its internal latent representations, while the student attempts to map raw inputs to these targets without access to those latents. There is no mechanical guarantee that a rule-based system can replicate the teacher's output, as the teacher leverages non-linear latent dynamics that the student explicitly lacks.

### Triviality check

**Verdict**: pass

Both outcomes are scientifically informative. If the non-differentiable system preserves generalization, it would challenge the prevailing assumption that continuous latent spaces are strictly necessary for complex control, suggesting that kinematic rules can approximate high-level dynamics. Conversely, if the gap is irreducible, it provides strong empirical evidence for the necessity of differentiable representations in zero-shot transfer, clarifying the computational complexity floor for humanoid control.

### Question-narrowing check

**Verdict**: concern

The question is currently framed as "Does distilling [Method A] into [Method B] preserve performance?", which is an implementation-method comparison. It narrows the inquiry to the success of a specific distillation strategy rather than asking a broader question about the information content of kinematic states versus latent representations. The focus on "non-differentiable rule-based systems" and "continuous, differentiable latent representations" makes the question about the *necessity of the method* rather than the *nature of the motion data* itself.

### Overall verdict

**Verdict**: validator_revise

The core idea is strong but the question is currently too focused on the specific distillation experiment rather than the underlying scientific principle. To validate, the question must be reframed to ask what information is required for zero-shot generalization, using the distillation attempt as the means to answer it, rather than making the distillation success the question itself.

[REVISED]
What information is necessary for zero-shot generalization in humanoid motion tracking: can raw kinematic states alone capture the complex dynamics required for unseen human movements, or is the continuous latent representation learned by large-scale Transformers strictly required to bridge the gap?
[/REVISED]
This reframing shifts the focus from the performance of a specific distillation pipeline to the fundamental question of whether kinematic data contains sufficient signal for the task, with the differentiability of the model serving as the variable to test the sufficiency of that signal.
