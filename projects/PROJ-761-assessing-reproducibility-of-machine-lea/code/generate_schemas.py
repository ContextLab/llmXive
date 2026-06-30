"""
Generates JSON Schema files for the project contracts.
This script validates the schema definitions and writes them to the contracts/ directory.
"""
import json
import os
import sys

# Define the schemas directly to ensure they are self-contained and valid
SCHEMAS = {
    "PaperManifest.schema.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://llmxive.org/schemas/PaperManifest.json",
        "title": "PaperManifest",
        "description": "Schema for validating paper metadata and dataset references for reproducibility studies.",
        "type": "object",
        "required": ["doi", "repo_url", "dataset_name", "reported_metrics"],
        "properties": {
            "doi": {
                "type": "string",
                "description": "Digital Object Identifier of the paper.",
                "pattern": "^10\\.[0-9]{4,}/[^\\s]+$"
            },
            "repo_url": {
                "type": "string",
                "format": "uri",
                "description": "URL to the code repository."
            },
            "dataset_name": {
                "type": "string",
                "description": "Name of the dataset used in the study."
            },
            "dataset_url": {
                "type": "string",
                "format": "uri",
                "description": "Direct URL to the dataset if available."
            },
            "supplementary_files": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "Patterns or names of supplementary files to extract (e.g., '*_supp.csv')."
                },
                "minItems": 0
            },
            "reported_metrics": {
                "type": "object",
                "required": ["mae", "r2"],
                "properties": {
                    "mae": {
                        "type": "number",
                        "description": "Reported Mean Absolute Error."
                    },
                    "r2": {
                        "type": "number",
                        "description": "Reported R-squared value."
                    },
                    "spearman_rho": {
                        "type": "number",
                        "description": "Reported Spearman's rank correlation coefficient."
                    },
                    "n_replicates": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Number of experimental replicates (per reviewer feedback)."
                    }
                }
            },
            "model_params": {
                "type": "integer",
                "minimum": 0,
                "description": "Number of parameters in the reported model."
            },
            "random_seed": {
                "type": ["integer", "null"],
                "description": "Reported random seed, or null if not specified."
            },
            "preprocessing_version": {
                "type": "string",
                "description": "Version of the preprocessing script used."
            },
            "library_versions": {
                "type": "object",
                "additionalProperties": {
                    "type": "string"
                },
                "description": "Key versions of critical libraries (e.g., 'torch': '2.2.0')."
            }
        }
    },
    "ReproResult.schema.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://llmxive.org/schemas/ReproResult.json",
        "title": "ReproResult",
        "description": "Schema for the result of a reproducibility attempt for a single paper.",
        "type": "object",
        "required": ["doi", "status", "metrics"],
        "properties": {
            "doi": {
                "type": "string",
                "description": "DOI of the paper being reproduced."
            },
            "status": {
                "type": "string",
                "enum": ["success", "partial", "failed", "unavailable"],
                "description": "Overall status of the reproduction attempt."
            },
            "failure_reason": {
                "type": "string",
                "description": "Detailed reason if status is failed or unavailable."
            },
            "metrics": {
                "type": "object",
                "required": ["mae", "r2"],
                "properties": {
                    "mae": {
                        "type": "number",
                        "description": "Reproduced Mean Absolute Error."
                    },
                    "r2": {
                        "type": "number",
                        "description": "Reproduced R-squared value."
                    },
                    "spearman_rho": {
                        "type": "number",
                        "description": "Reproduced Spearman's rank correlation."
                    }
                }
            },
            "deviations": {
                "type": "object",
                "properties": {
                    "delta_mae": {
                        "type": "number",
                        "description": "Absolute difference between reproduced and reported MAE."
                    },
                    "delta_r2": {
                        "type": "number",
                        "description": "Absolute difference between reproduced and reported R2."
                    },
                    "delta_rho": {
                        "type": "number",
                        "description": "Absolute difference between reproduced and reported Spearman rho."
                    }
                }
            },
            "reproducibility_score": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Deviation Index S (FR-009)."
            },
            "model_substituted": {
                "type": "boolean",
                "description": "True if the original model was too large and a baseline was used."
            },
            "seed_used": {
                "type": ["integer", "null"],
                "description": "The seed actually used for the run."
            },
            "seed_sweep_std": {
                "type": "object",
                "description": "Standard deviations from seed sensitivity analysis (FR-010).",
                "properties": {
                    "mae_std": { "type": "number" },
                    "r2_std": { "type": "number" },
                    "rho_std": { "type": "number" },
                    "max_metric_std": { "type": "number" }
                }
            },
            "environment": {
                "type": "object",
                "properties": {
                    "python_version": { "type": "string" },
                    "os": { "type": "string" },
                    "docker_hash": { "type": "string" }
                }
            }
        }
    },
    "StatSummary.schema.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://llmxive.org/schemas/StatSummary.json",
        "title": "StatSummary",
        "description": "Schema for aggregated statistical analysis across multiple reproducibility studies.",
        "type": "object",
        "required": ["n_papers", "paired_t_tests", "bland_altman_refs"],
        "properties": {
            "n_papers": {
                "type": "integer",
                "minimum": 0,
                "description": "Total number of papers analyzed."
            },
            "n_successful": {
                "type": "integer",
                "minimum": 0,
                "description": "Number of successful reproductions."
            },
            "paired_t_tests": {
                "type": "object",
                "description": "Results of paired t-tests between reported and reproduced metrics.",
                "properties": {
                    "mae": {
                        "type": "object",
                        "properties": {
                            "t_statistic": { "type": "number" },
                            "p_value": { "type": "number" },
                            "p_value_corrected": { "type": "number" }
                        }
                    },
                    "r2": {
                        "type": "object",
                        "properties": {
                            "t_statistic": { "type": "number" },
                            "p_value": { "type": "number" },
                            "p_value_corrected": { "type": "number" }
                        }
                    },
                    "spearman_rho": {
                        "type": "object",
                        "properties": {
                            "t_statistic": { "type": "number" },
                            "p_value": { "type": "number" },
                            "p_value_corrected": { "type": "number" }
                        }
                    }
                }
            },
            "mixed_effects_model": {
                "type": "object",
                "description": "Variance components from Linear Mixed-Effects Model.",
                "properties": {
                    "variance_paper_intercept": { "type": "number" },
                    "variance_residual": { "type": "number" },
                    "icc": { "type": "number" }
                }
            },
            "heterogeneity": {
                "type": "object",
                "description": "I-squared and pooled effect size.",
                "properties": {
                    "i_squared": { "type": "number" },
                    "pooled_effect": { "type": "number" }
                }
            },
            "bland_altman_refs": {
                "type": "array",
                "items": { "type": "string" },
                "description": "List of paths to generated Bland-Altman plot PNGs."
            },
            "failure_log_summary": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "doi": { "type": "string" },
                        "reason": { "type": "string" },
                        "category": { "type": "string" }
                    }
                },
                "description": "Summary of excluded papers and failure modes."
            }
        }
    }
}

def main():
    contracts_dir = "contracts"
    
    # Ensure directory exists
    if not os.path.exists(contracts_dir):
        os.makedirs(contracts_dir)
        print(f"Created directory: {contracts_dir}")

    success = True
    for filename, schema in SCHEMAS.items():
        filepath = os.path.join(contracts_dir, filename)
        try:
            # Validate JSON structure by dumping and reloading
            json.dumps(schema)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2)
            
            print(f"Generated: {filepath}")
        except Exception as e:
            print(f"Error generating {filepath}: {e}", file=sys.stderr)
            success = False

    if success:
        print("All schemas generated successfully.")
        sys.exit(0)
    else:
        print("Failed to generate all schemas.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()