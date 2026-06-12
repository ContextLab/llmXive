## Research-question validation

### Phenomenon-vs-method check

**Verdict**: concern

The question asks whether specific models (higher-order Markov, stochastic volatility) outperform a random-walk baseline, which frames the core inquiry as a method-evaluation comparison rather than a direct question about the phenomenon itself. The underlying phenomenon question is "is there exploitable serial correlation in cryptocurrency price returns?" but this is buried beneath the model-performance framing.

### Circularity check

**Verdict**: pass

The predictor (historical price returns) and predicted variable (future price returns) are temporally distinct measurements of the same underlying process. This is standard for time-series forecasting and does not create a mechanical guarantee of the relationship.

### Triviality check

**Verdict**: pass

Either outcome is informative: a positive result would demonstrate exploitable serial correlation in cryptocurrency markets (challenging weak-form EMH), while a null result would support the random-walk hypothesis for digital assets. Both findings have publication value in financial statistics.

### Question-narrowing check

**Verdict**: concern

The question names a domain relationship (serial correlation in crypto prices) but frames it through implementation constraints (specific models, statistical significance thresholds, 5% improvement margin). A cleaner domain question would focus on the existence and magnitude of temporal dependence rather than model comparison metrics.

### Overall verdict

**Verdict**: validator_revise

[REVISED]
What is the magnitude and structure of serial correlation in Bitcoin and Ethereum returns across different time horizons, and can this dependence be distinguished from random noise using out-of-sample forecast accuracy?
[/REVISED]
Reframing shifts focus from "do these models beat random walk" to "what temporal structure exists in crypto returns," allowing the model comparison to serve as evidence rather than being the question itself.
