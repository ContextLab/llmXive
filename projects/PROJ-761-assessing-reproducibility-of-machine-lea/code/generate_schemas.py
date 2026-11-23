import json
import os
import sys
from pathlib import Path

def main():
    """
    Generates JSON Schema files for PaperManifest, ReproResult, and StatSummary.
    These schemas are used by the ingest pipeline and result validators.
    """
    # Define the base directory for contracts
    base_dir = Path(__file__).parent.parent
    contracts_dir = base_dir / "contracts"

    # Ensure contracts directory exists
    contracts_dir.mkdir(parents=True, exist_ok=True)

    # Define schemas as dictionaries (YAML content represented as strings for simplicity in generation)
    # In a real scenario, we might use a library like jsonschema to validate, but here we write the files directly.
    # The content below matches the YAML definitions required by the project.

    schemas = {
        "PaperManifest.schema.yaml": """
$schema: http://json-schema.org/draft-07/schema#
title: PaperManifest
description: Schema for validating the paper manifest containing dataset references and reported metrics.
type: object
required:
  - doi
  - repo_url
  - dataset_name
  - reported_metrics
properties:
  doi:
    type: string
    description: Digital Object Identifier of the research paper.
    pattern: "^10\\\\.[0-9]{4,}/[^\\\\s]*$"
  repo_url:
    type: string
    description: URL to the code repository (e.g., GitHub).
    format: uri
  dataset_name:
    type: string
    description: Name of the dataset used in the study.
  dataset_url:
    type: string
    description: Optional direct URL to the dataset file.
    format: uri
  supplementary_files:
    type: array
    description: List of supplementary file patterns to fetch.
    items:
      type: string
  reported_metrics:
    type: object
    required:
      - mae
      - r2
      - rho
    properties:
      mae:
        type: number
        description: Reported Mean Absolute Error.
      r2:
        type: number
        description: Reported R-squared value.
      rho:
        type: number
        description: Reported Spearman's rank correlation coefficient.
      seed:
        type: integer
        description: Random seed used in the original study (optional).
      model_parameters:
        type: integer
        description: Approximate number of model parameters.
      notes:
        type: string
        description: Additional notes about the reported metrics.
  reaction_conditions:
    type: object
    description: Optional metadata about reaction conditions (temperature, solvent, etc.).
    properties:
      temperature:
        type: number
        description: Temperature in Celsius.
      solvent:
        type: string
        description: Solvent used.
      catalyst_loading:
        type: number
        description: Catalyst loading percentage.
  experimental_replicates:
    type: integer
    description: Number of experimental replicates performed.
  yield_std_dev:
    type: number
    description: Standard deviation of reported yields if available.
""",
        "ReproResult.schema.yaml": """
$schema: http://json-schema.org/draft-07/schema#
title: ReproResult
description: Schema for the reproducibility results of a single paper.
type: object
required:
  - doi
  - flags
properties:
  doi:
    type: string
    description: Digital Object Identifier of the paper.
  mae:
    type: number
    nullable: true
    description: Reproduced Mean Absolute Error.
  r2:
    type: number
    nullable: true
    description: Reproduced R-squared value.
  rho:
    type: number
    nullable: true
    description: Reproduced Spearman's rank correlation coefficient.
  deviation_mae:
    type: number
    nullable: true
    description: Deviation of reproduced MAE from reported MAE.
  deviation_r2:
    type: number
    nullable: true
    description: Deviation of reproduced R2 from reported R2.
  deviation_rho:
    type: number
    nullable: true
    description: Deviation of reproduced rho from reported rho.
  score_s:
    type: number
    nullable: true
    description: Reproducibility score S (1 - average relative deviation).
  max_metric_std_dev:
    type: number
    nullable: true
    description: Maximum standard deviation of metrics across seed sensitivity analysis.
  flags:
    type: array
    description: List of flags indicating issues (e.g., 'Model Substitution', 'Data Unavailable').
    items:
      type: string
  experimental_replicates:
    type: integer
    nullable: true
    description: Number of experimental replicates found in the dataset.
  reaction_conditions:
    type: object
    nullable: true
    description: Extracted reaction conditions.
    properties:
      temperature:
        type: number
      solvent:
        type: string
      catalyst_loading:
        type: number
  yield_std_dev:
    type: number
    nullable: true
    description: Standard deviation of yields across experimental replicates.
  failure_mode:
    type: string
    nullable: true
    description: Specific failure mode if the paper could not be reproduced.
  details:
    type: string
    nullable: true
    description: Detailed log of the reproduction attempt.
""",
        "StatSummary.schema.yaml": """
$schema: http://json-schema.org/draft-07/schema#
title: StatSummary
description: Schema for the aggregated statistical summary of reproducibility across studies.
type: object
required:
  - t_test_results
  - mixed_effects_results
  - heterogeneity
properties:
  t_test_results:
    type: object
    description: Results of paired t-tests for each metric.
    properties:
      mae:
        type: object
        properties:
          statistic:
            type: number
          pvalue:
            type: number
          pvalue_corrected:
            type: number
      r2:
        type: object
        properties:
          statistic:
            type: number
          pvalue:
            type: number
          pvalue_corrected:
            type: number
      rho:
        type: object
        properties:
          statistic:
            type: number
          pvalue:
            type: number
          pvalue_corrected:
            type: number
  tost_results:
    type: object
    description: Results of Two One-Sided Tests for equivalence.
    properties:
      mae:
        type: object
        properties:
          pvalue_lower:
            type: number
          pvalue_upper:
            type: number
          equivalent:
            type: boolean
      r2:
        type: object
        properties:
          pvalue_lower:
            type: number
          pvalue_upper:
            type: number
          equivalent:
            type: boolean
      rho:
        type: object
        properties:
          pvalue_lower:
            type: number
          pvalue_upper:
            type: number
          equivalent:
            type: boolean
  mixed_effects_results:
    type: object
    description: Results of the Linear Mixed-Effects Model.
    properties:
      fixed_effects_variance_explained:
        type: number
        description: R-squared of fixed effects.
      random_effects_variance:
        type: number
        description: Variance of random intercepts.
      residual_variance:
        type: number
        description: Residual variance.
      fixed_effects_summary:
        type: array
        items:
          type: object
          properties:
            term:
              type: string
            estimate:
              type: number
            std_err:
              type: number
            t_value:
              type: number
            p_value:
              type: number
  heterogeneity:
    type: object
    description: Heterogeneity statistics.
    properties:
      I2:
        type: number
        description: I-squared statistic.
      pooled_effect_size:
        type: number
        description: Pooled effect size (mean absolute deviation).
      confidence_interval:
        type: array
        items:
          type: number
        description: 95% confidence interval [lower, upper].
  bland_altman_plots:
    type: array
    description: List of generated Bland-Altman plot filenames.
    items:
      type: string
  failure_log_summary:
    type: array
    description: Summary of failures from the failure log.
    items:
      type: object
      properties:
        paper_doi:
          type: string
        failure_mode:
          type: string
        details:
          type: string
"""
    }

    for filename, content in schemas.items():
        filepath = contracts_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            # Clean up leading/trailing whitespace from the multiline string
            f.write(content.strip() + "\n")
        print(f"Generated schema: {filepath}")

    print("Schema generation complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
