## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about a substantive ecological phenomenon (species tracking or failing to track climate change via niche shifts) and whether patterns vary across taxa and regions. The methodology (GBIF + WorldClim + regression) is clearly a tool to answer the question, not the question itself.

### Circularity check

**Verdict**: pass

The predictor (regional warming rate) comes from gridded climate data (WorldClim), while the predicted variable (species niche shift) is derived from occurrence locations paired with climate values. Although both use the same climate dataset, the occurrence records themselves are independent observations of where species were actually found, so the relationship is not mechanically guaranteed by construction.

### Triviality check

**Verdict**: pass

Both outcomes are informative: a positive correlation confirms climate tracking and identifies which taxa are resilient, while a null/weak correlation indicates widespread niche lags and elevated extinction risk. Either result provides actionable evidence for conservation prioritization, making the question non-trivial.

### Question-narrowing check

**Verdict**: pass

The question names a domain relationship (niche shifts in response to climate change across taxa/regions) rather than implementation constraints. It asks "how do species behave under changing climate" rather than "can method X handle data Y within budget Z."

### Overall verdict

**Verdict**: validated

All four checks pass. The research question is well-structured, asks a substantive ecological question independent of method choice, avoids circularity, and would yield informative results regardless of outcome direction. The project can proceed to initialization.
