# Project Scope and Ethics Declaration

## ⚠️ Critical Ethics Statement

**This project is strictly a synthetic data stress-test. No human participants are involved. No claims of human perception validation are made. Real data path is disabled due to unavailability.**

This declaration supersedes all other project documentation and must be referenced in all downstream tasks, analysis outputs, and publications derived from this codebase.

## Project Scope

### Primary Objective
To validate and stress-test an automated research pipeline for analyzing the relationship between visual motion characteristics and perceived agency in virtual interactions, using only synthetic data.

### What This Project Is
- A methodological stress-test of the research pipeline
- A demonstration of automated data processing and analysis workflows
- A validation of statistical modeling approaches under controlled conditions
- A template for future research with real human data (when available)

### What This Project Is NOT
- A study of actual human perception or behavior
- A validation of the synthetic data generator against human responses
- A basis for claims about real-world avatar interactions
- A substitute for IRB-approved human subjects research

## Data Sources

### Synthetic Data (Active)
- **Source**: `code/data/generate_synthetic_data.py`
- **Purpose**: Generate controlled datasets with known ground-truth relationships
- **Characteristics**:
 - Known correlation structures between motion features and agency scores
 - Configurable sample sizes and noise levels
 - Reproducible via random seed

### Real Human Data (Disabled)
- **Status**: Unavailable and disabled
- **Reason**: No accessible, ethically-approved dataset with required variables
- **Path**: `data/raw/` is reserved for future real data but currently contains only synthetic outputs
- **Note**: Any attempt to enable real data paths requires explicit ethical review and approval

## Ethical Constraints

1. **No Human Participants**: The project explicitly excludes human subjects. No recruitment, consent, or IRB approval is required or applicable.

2. **No Misrepresentation**: All outputs, reports, and visualizations must include a disclaimer stating the synthetic nature of the data.

3. **No Generalization**: Results cannot be generalized to human behavior or used to make claims about real-world interactions.

4. **Transparency**: The synthetic nature of the data must be visible in all generated artifacts, including:
 - Data file metadata
 - Plot captions
 - Model output summaries
 - Final reports

5. **Real Data Path Disabled**: The codebase includes a flag to disable any real data acquisition attempts. This flag is set to `true` by default and must not be changed without proper ethical oversight.

## Downstream Task References

All downstream tasks must include a reference to this scope declaration:

- **Data Generation Tasks**: Must log the synthetic data disclaimer in output metadata
- **Preprocessing Tasks**: Must preserve the "synthetic" flag in processed data
- **Modeling Tasks**: Must include the ethics statement in model output files
- **Visualization Tasks**: Must add disclaimers to all plot captions
- **Reporting Tasks**: Must prominently feature the scope declaration in final outputs

## Revision History

- **v1.0**: Initial scope definition with explicit ethics declaration
- **Status**: Active and enforced across all project phases

## Contact

For questions regarding project scope or ethics, refer to the project maintainers and the original specification documents in `specs/001-visual-motion-agency/`.