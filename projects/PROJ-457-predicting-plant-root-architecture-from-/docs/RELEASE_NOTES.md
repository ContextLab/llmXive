# Release Notes

## Version 1.0.0 (Current)

### Overview

Initial release of the root architecture prediction pipeline with full implementation of all three user stories.

### Features

#### User Story 1: Data Ingestion and Preprocessing (MVP)
- ✅ Root phenotype data ingestion from RootReader/PlantPheno
- ✅ ISRIC soil nutrient data fetching with streaming support
- ✅ KNN interpolation for missing nutrients
- ✅ Data filtering (n≥20 per species, exclude experimental data)
- ✅ Dataset merging with species-level integrity
- ✅ Log-transformation and z-score normalization
- ✅ KNN imputation (k=5) with mean fallback
- ✅ Comprehensive logging of exclusion counts

#### User Story 2: Statistical Modeling
- ✅ Species-stratified k-fold cross-validation
- ✅ Linear Mixed-Effects Model (LMM) with REML estimation
- ✅ Random Forest baseline (max_depth=5)
- ✅ R² difference calculation and success criterion evaluation (SC-002)
- ✅ F-tests and p-value calculations
- ✅ Multiple comparison correction (Bonferroni/FDR)
- ✅ Sensitivity analysis against literature ranges
- ✅ Final metrics report generation

#### User Story 3: Visualization and Reporting
- ✅ Partial dependence plots (5th-95th percentile range)
- ✅ Scatter plots with fit lines
- ✅ Image size enforcement (≤100MB total)
- ✅ Final report compilation with associational framing
- ✅ Merge success rate calculation (SC-001)
- ✅ Biological plausibility verification (SC-006)
- ✅ Comprehensive documentation

### Success Criteria Status

- **SC-001**: Merge success rate documented ✅
- **SC-002**: LMM vs RF R² difference ≤ 5% (evaluated, status in report) ✅
- **SC-004**: Total output size ≤ 100MB ✅
- **SC-005**: Excluded species documented ✅
- **SC-006**: Biological plausibility verified ✅

### Technical Specifications

- **Python Version**: 3.11+
- **Runtime**: ≤ 6 hours
- **Memory**: ≤ 7GB RAM
- **Output Size**: ≤ 100MB
- **Execution**: CPU-only (no GPU required)

### Dependencies

- pandas
- scikit-learn
- statsmodels
- geopandas
- seaborn
- matplotlib
- pyyaml

### Known Limitations

- Requires network access for data fetching
- Large datasets may require streaming configuration
- Some data sources may have rate limits

### Breaking Changes

None in initial release.

### Migration Guide

Not applicable for initial release.

### Future Roadmap

#### Planned Enhancements
- Additional data sources integration
- More sophisticated model architectures
- Real-time data processing capabilities
- Web interface for results visualization
- Interactive dashboards
- Batch processing support

#### Under Consideration
- Cloud deployment options
- Containerization improvements
- Automated pipeline orchestration
- Extended sensitivity analysis

### Contributors

- Implementation team
- Reviewers
- Data scientists
- Domain experts

### Acknowledgments

Special thanks to:
- RootReader and PlantPheno for data provision
- ISRIC for soil data
- The open-source community for library support

### Support

For issues and questions:
- Open an issue on GitHub
- Check documentation in `docs/`
- Review `USAGE.md` for common scenarios

### License

[License information]

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2024 | Initial release with full pipeline implementation |

### Changelog

#### Added
- Complete data ingestion pipeline
- Preprocessing with transformations and imputation
- LMM and Random Forest modeling
- Visualization and reporting
- Comprehensive documentation
- Test suite (unit, contract, integration)
- Configuration management
- Sensitivity analysis

#### Changed
- N/A (initial release)

#### Fixed
- N/A (initial release)

#### Removed
- N/A (initial release)