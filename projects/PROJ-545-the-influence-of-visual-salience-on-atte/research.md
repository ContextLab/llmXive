# Research Notes: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

## Model Specification: Choice-Only aDDM

### Acknowledgement of Data Limitations

This research implements a **Choice-Only** variant of the Attentional Drift Diffusion Model (aDDM). The underlying dataset (Moral Machine) consists of discrete binary choices (e.g., "Spare Left" vs. "Spare Right") derived from user interactions with moral dilemmas. Crucially, **Response Time (RT) data is not available** in the provided dataset.

Consequently, the standard aDDM, which jointly estimates drift rates and decision thresholds by fitting both choice proportions and RT distributions, cannot be applied in its full form. Instead, we utilize a reduced parameterization that relies solely on the choice outcomes.

### Parameter Identifiability Constraints

The absence of RT data introduces significant constraints on parameter identifiability:

1. **Threshold-Drift Trade-off**: In the standard diffusion framework, the decision threshold ($a$) and the drift rate ($v$) are confounded when RT is unobserved. A high drift rate with a high threshold produces the same choice probability distribution as a low drift rate with a low threshold.
2. **Normalization Strategy**: To resolve this, we fix the decision threshold ($a$) to a constant value (arbitrarily set to 1.0 in the simulation units) and estimate the drift rates ($v$) relative to this fixed boundary. This effectively treats the model as a logistic regression where the "drift" represents the log-odds of the choice, scaled by the fixed threshold.
3. **Salience Weight Interpretation**: The estimated salience weight ($w_s$) in this Choice-Only context represents the *influence* of visual attention on the *probability* of choosing the salient option, rather than its speed. We cannot claim that salience *accelerates* the decision process, only that it biases the final outcome.

### Philosophical and Methodological Framing

As noted in the simulated review by Socrates, defining morality by the locus of the gaze risks conflating the "spectacle" with the "good." By restricting our analysis to choice data alone, we explicitly acknowledge that we are measuring the *outcome* of a decision process, not the *temporal dynamics* of attention.

* **Associational Nature**: The findings must be framed as associational correlations. A positive salience weight indicates that higher visual salience is associated with a higher probability of being blamed or spared, but the lack of RT data prevents us from asserting that attention *caused* the decision in a temporal sense (i.e., we cannot rule out that the decision was made instantly based on salience, or that attention was a post-hoc rationalization).
* **System 1 vs. System 2**: While the aDDM is often used to model System 1 (fast, intuitive) processes, the absence of RT prevents us from distinguishing between a fast, salience-driven heuristic and a slow, deliberative process that happens to align with salience. We assume the "Choice-Only" model captures the net bias, regardless of the underlying cognitive speed.

### Implementation Details

* **Model Class**: `code/models/addm.py::aDDMChoiceOnly`
* **Simulation Logic**: The model simulates a random walk of evidence accumulation until a boundary is hit. However, for fitting purposes, we use the closed-form solution for choice probability given a fixed threshold and drift rate, bypassing the need for RT simulation.
* **Fitting Procedure**: Grid search over salience weights ($w_s \in [0.0, 1.0]$) and drift parameters, optimizing for the log-likelihood of the observed binary choices.
* **Validation**: Cross-validation is performed on the choice outcomes to ensure the model generalizes, acknowledging that overfitting is a risk given the reduced parameter space.

### Future Directions

Future iterations of this research should seek datasets with response time measurements to:
1. Decouple drift rate and threshold parameters.
2. Directly test the hypothesis that salience accelerates the accumulation of evidence for the salient option.
3. Distinguish between "fast" errors (System 1) and "slow" corrections (System 2).