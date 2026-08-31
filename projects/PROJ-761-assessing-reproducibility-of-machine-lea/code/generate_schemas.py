import json
import os
import sys
from pathlib import Path

def main():
    """
    Generates JSON Schema files for PaperManifest, ReproResult, and StatSummary
    and saves them to the contracts/ directory.
    """
    project_root = Path(__file__).resolve().parent.parent
    contracts_dir = project_root / "contracts"
    
    # Ensure contracts directory exists
    contracts_dir.mkdir(exist_ok=True)

    schemas = {
        "PaperManifest.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://llmxive.org/schemas/PaperManifest.schema.json",
            "title": "PaperManifest",
            "description": "Schema for validating paper metadata and dataset references for reproducibility studies.",
            "type": "object",
            "required": [
                "doi",
                "repo_url",
                "dataset_name",
                "reported_metrics"
            ],
            "properties": {
                "doi": {
                    "type": "string",
                    "description": "Digital Object Identifier of the paper.",
                    "pattern": "^10\\.\\d{4,9}/[-._;()/:A-Z0-9]+$"
                },
                "repo_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL to the code repository."
                },
                "dataset_name": {
                    "type": "string",
                    "description": "Name or identifier of the dataset used."
                },
                "dataset_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "Optional direct URL to the dataset files."
                },
                "supplementary_files": {
                    "type": "array",
                    "description": "Patterns or names of supplementary files to extract.",
                    "items": {
                        "type": "string"
                    }
                },
                "reported_metrics": {
                    "type": "object",
                    "description": "Metrics reported in the paper.",
                    "required": ["mae", "r2"],
                    "properties": {
                        "mae": {
                            "type": "number",
                            "description": "Mean Absolute Error reported."
                        },
                        "r2": {
                            "type": "number",
                            "description": "R-squared value reported."
                        },
                        "spearman_rho": {
                            "type": "number",
                            "description": "Spearman's rank correlation coefficient reported."
                        }
                    }
                },
                "model_params": {
                    "type": "integer",
                    "description": "Number of parameters in the original model."
                },
                "random_seed": {
                    "type": "integer",
                    "description": "Random seed used in the original study, if reported."
                },
                "preprocessing_version": {
                    "type": "string",
                    "description": "Version of the preprocessing script used."
                },
                "library_versions": {
                    "type": "object",
                    "description": "Library versions used.",
                    "additionalProperties": {
                        "type": "string"
                    }
                }
            },
            "additionalProperties": False
        },
        "ReproResult.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://llmxive.org/schemas/ReproResult.schema.json",
            "title": "ReproResult",
            "description": "Schema for the results of a single reproducibility run for a paper.",
            "type": "object",
            "required": [
                "doi",
                "metrics",
                "deviations",
                "reproducibility_score",
                "status"
            ],
            "properties": {
                "doi": {
                    "type": "string",
                    "description": "DOI of the paper being reproduced."
                },
                "status": {
                    "type": "string",
                    "enum": ["success", "partial", "failed", "substituted"],
                    "description": "Status of the reproduction attempt."
                },
                "failure_reason": {
                    "type": "string",
                    "description": "Reason for failure if status is not success."
                },
                "metrics": {
                    "type": "object",
                    "description": "Reproduced metrics.",
                    "required": ["mae", "r2"],
                    "properties": {
                        "mae": {
                            "type": "number"
                        },
                        "r2": {
                            "type": "number"
                        },
                        "spearman_rho": {
                            "type": "number"
                        }
                    }
                },
                "deviations": {
                    "type": "object",
                    "description": "Absolute deviations from reported metrics.",
                    "properties": {
                        "mae": {
                            "type": "number"
                        },
                        "r2": {
                            "type": "number"
                        },
                        "spearman_rho": {
                            "type": "number"
                        }
                    }
                },
                "reproducibility_score": {
                    "type": "number",
                    "description": "Deviation Index (S) score.",
                    "minimum": 0,
                    "maximum": 1
                },
                "seed_used": {
                    "type": "integer",
                    "description": "Seed used for reproduction."
                },
                "model_substituted": {
                    "type": "boolean",
                    "description": "Whether the model was substituted due to size."
                },
                "metric_std": {
                    "type": "object",
                    "description": "Standard deviation of metrics across sensitivity seeds.",
                    "properties": {
                        "mae": {
                            "type": "number"
                        },
                        "r2": {
                            "type": "number"
                        },
                        "spearman_rho": {
                            "type": "number"
                        }
                    }
                },
                "max_metric_std": {
                    "type": "number",
                    "description": "Maximum standard deviation observed across all metrics."
                },
                "parameter_count": {
                    "type": "integer",
                    "description": "Number of parameters in the reproduced model."
                }
            },
            "additionalProperties": False
        },
        "StatSummary.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://llmxive.org/schemas/StatSummary.schema.json",
            "title": "StatSummary",
            "description": "Schema for the aggregated statistical summary of reproducibility results.",
            "type": "object",
            "required": [
                "t_tests",
                "bland_altman_files",
                "generated_at"
            ],
            "properties": {
                "t_tests": {
                    "type": "object",
                    "description": "Results of paired t-tests.",
                    "properties": {
                        "mae": {
                            "type": "object",
                            "properties": {
                                "statistic": { "type": "number" },
                                "pvalue": { "type": "number" },
                                "pvalue_bonferroni": { "type": "number" }
                            }
                        },
                        "r2": {
                            "type": "object",
                            "properties": {
                                "statistic": { "type": "number" },
                                "pvalue": { "type": "number" },
                                "pvalue_bonferroni": { "type": "number" }
                            }
                        },
                        "spearman_rho": {
                            "type": "object",
                            "properties": {
                                "statistic": { "type": "number" },
                                "pvalue": { "type": "number" },
                                "pvalue_bonferroni": { "type": "number" }
                            }
                        }
                    }
                },
                "tost": {
                    "type": "object",
                    "description": "Results of Two One-Sided Tests for equivalence.",
                    "properties": {
                        "mae": {
                            "type": "object",
                            "properties": {
                                "pvalue_lower": { "type": "number" },
                                "pvalue_upper": { "type": "number" },
                                "equivalent": { "type": "boolean" }
                            }
                        },
                        "r2": {
                            "type": "object",
                            "properties": {
                                "pvalue_lower": { "type": "number" },
                                "pvalue_upper": { "type": "number" },
                                "equivalent": { "type": "boolean" }
                            }
                        }
                    }
                },
                "mixed_effects": {
                    "type": "object",
                    "description": "Linear Mixed-Effects model results.",
                    "properties": {
                        "variance_components": {
                            "type": "object",
                            "description": "Variance components (e.g., paper intercept variance, residual variance)."
                        },
                        "fixed_effects": {
                            "type": "object",
                            "description": "Fixed effects estimates (if any)."
                        }
                    }
                },
                "heterogeneity": {
                    "type": "object",
                    "description": "Heterogeneity statistics (I-squared, pooled effect).",
                    "properties": {
                        "i2": {
                            "type": "number",
                            "description": "I-squared statistic."
                        },
                        "i2_interpretation": {
                            "type": "string"
                        },
                        "pooled_effect": {
                            "type": "object",
                            "description": "Pooled effect size estimate."
                        }
                    }
                },
                "bland_altman_files": {
                    "type": "array",
                    "description": "List of generated Bland-Altman plot filenames.",
                    "items": {
                        "type": "string"
                    }
                },
                "failure_log_summary": {
                    "type": "array",
                    "description": "Summary of qualitative failure modes.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "doi": { "type": "string" },
                            "reason": { "type": "string" }
                        }
                    }
                },
                "generated_at": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Timestamp of summary generation."
                }
            },
            "additionalProperties": False
        }
    }

    for filename, schema_content in schemas.items():
        file_path = contracts_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(schema_content, f, indent=2)
        print(f"Generated schema: {file_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
