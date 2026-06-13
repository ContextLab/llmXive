## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about the relationship between urban geographic features (building density, vegetation, impervious surfaces from OSM) and surface temperature (from satellite data), which is a substantive scientific question about the world. It is not framed as whether a specific algorithm or architecture can perform a task, but whether a domain relationship exists between crowdsourced urban features and thermal patterns.

### Circularity check

**Verdict**: pass

The predictor data (OSM building footprints, land-use tags, tree nodes, road networks) comes from crowdsourced geographic vector data, while the predicted variable (surface temperature) comes from satellite thermal imaging (MODIS/Landsat). These are completely independent measurement modalities with no shared signal source, making any predictive relationship empirically informative rather than mechanically guaranteed.

### Triviality check

**Verdict**: pass

Both positive and null results would be informative. A strong predictive relationship would validate OSM as a cost-effective proxy for temperature monitoring in cities lacking dense sensor networks. A null result would indicate that OSM features miss critical aspects of urban heat dynamics (e.g., material albedo, microclimate effects), guiding future data collection priorities. While UHI effects are well-established, the specific question of OSM's predictive utility at 30m resolution across diverse cities remains an open applied question.

### Question-narrowing check

**Verdict**: pass

The question names a domain relationship (urban features → temperature) rather than implementation constraints. It does not specify a particular algorithm, budget, or computational requirement that would make it about method performance. The focus is on whether OSM data can serve as a proxy for expensive remote-sensing campaigns, which is a practical domain question.

### Overall verdict

**Verdict**: validated

All four checks pass. The research question is well-formulated for a statistics project investigating whether crowdsourced urban features can predict thermal patterns. The question targets a genuine domain relationship with independent data sources, and both positive and null outcomes would provide actionable insights for urban planning and data collection strategy.
