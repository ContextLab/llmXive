## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question targets the physical linkage between moisture transport events (atmospheric rivers) and large-scale circulation states (500 hPa geopotential height), independent of any specific detection algorithm's performance. It focuses on the empirical relationship between two atmospheric variables rather than the capability of a specific model or method.

### Circularity check

**Verdict**: pass

The predictor (500 hPa geopotential height anomalies) and the predicted variable (AR frequency derived primarily from integrated water vapor transport) are distinct physical diagnostics. While both are sourced from the same ERA5 reanalysis product, they are not mathematically constructed from one another in a way that guarantees a specific correlation outcome.

### Triviality check

**Verdict**: pass

Considering both outcomes, a reasonable researcher would find the results informative: a strong correlation confirms dynamical control useful for seasonal forecasting, while a null result would highlight regions where local moisture convergence dominates over large-scale circulation patterns. Neither outcome is predetermined by basic domain knowledge given the global scope and seasonal breakdown.

### Question-narrowing check

**Verdict**: pass

The question names a relationship in the domain (AR frequency vs. circulation variability) and specifies spatiotemporal scales (latitudinal bands, seasons) rather than implementation constraints (e.g., computational budget, specific library usage). It asks how the atmosphere behaves, not how well a tool performs.

### Overall verdict

**Verdict**: validated

All four checks pass, indicating a scientifically substantive question that is empirically testable and avoids implementation fixation. The project can proceed to initialization without needing to reframe the core research question.
