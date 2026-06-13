## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about the predictive reliability of species-distribution models for forecasting range shifts under climate change, which is a substantive scientific question about ecological forecasting accuracy. While it references SDMs as the tool, the core question is whether historical occurrence-climate relationships can generalize to future distributions—a genuinely debated issue in conservation biology, not a narrow method-benchmark question.

### Circularity check

**Verdict**: pass

The predictor (historical occurrence records + historical climate rasters from 1970-2000) and the validation variable (recent occurrence records from 2005-2020) are temporally independent and drawn from different observation periods. The model is trained on past data and evaluated on future observations, breaking any potential circularity.

### Triviality check

**Verdict**: pass

A positive result (SDMs achieve moderate-to-high predictive accuracy) would validate their use for long-term conservation planning and forecasting. A null result (poor predictive accuracy) would reveal fundamental limitations in current SDM approaches and suggest need for alternative data or methods. Both outcomes directly address the debated reliability of SDMs noted in the motivation, making either result scientifically informative.

### Question-narrowing check

**Verdict**: pass

The question names a domain relationship: the connection between historical occurrence-climate patterns and future species distributions under climate change. It does not fixate on implementation constraints (e.g., specific algorithms, computational budgets, or hardware), but rather on the ecological forecasting problem itself.

### Overall verdict

**Verdict**: validated

All four checks pass. The research question addresses a genuine scientific debate about SDM predictive reliability, uses temporally independent training and validation data, and would yield informative results regardless of outcome. The project can proceed to initialization.
