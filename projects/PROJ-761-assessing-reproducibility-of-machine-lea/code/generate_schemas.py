"""
Script to generate JSON Schema files for the project.
This script ensures that the contracts directory is populated with the correct schemas.
"""
import json
import os
import sys
from pathlib import Path

# Define the directory where schemas will be stored
CONTRACTS_DIR = Path("contracts")

# Define the schemas as dictionaries
PAPER_MANIFEST_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "PaperManifest",
    "description": "Schema for validating paper metadata and dataset references for reproducibility studies.",
    "type": "object",
    "required": ["doi", "repo_url", "dataset_name", "reported_metrics", "reaction_conditions"],
    "properties": {
        "doi": {
            "type": "string",
            "description": "Digital Object Identifier of the paper.",
            "pattern": "^10\\.\\d{4,9}/[-._;()/:A-Z0-9]+$",
            "examples": ["10.1021/acscatal.0c01234"]
        },
        "repo_url": {
            "type": "string",
            "description": "URL to the code repository.",
            "format": "uri",
            "examples": ["https://github.com/example/reaction-yield-model"]
        },
        "dataset_name": {
            "type": "string",
            "description": "Name of the dataset used in the study."
        },
        "reported_metrics": {
            "type": "object",
            "required": ["mae", "r2", "spearman_rho"],
            "properties": {
                "mae": {"type": "number", "description": "Reported Mean Absolute Error."},
                "r2": {"type": "number", "description": "Reported R-squared value."},
                "spearman_rho": {"type": "number", "description": "Reported Spearman correlation coefficient."}
            }
        },
        "reaction_conditions": {
            "type": "object",
            "description": "Key experimental conditions to ensure reproducibility.",
            "properties": {
                "temperature_celsius": {"type": "number", "description": "Reaction temperature in Celsius."},
                "solvent": {"type": "string", "description": "Primary solvent used."},
                "catalyst_loading_mol_percent": {"type": "number", "description": "Catalyst loading in mol%."}
            }
        },
        "seed": {"type": ["integer", "null"], "description": "Random seed used in the original study, if reported."},
        "model_params": {"type": "object", "description": "Hyperparameters of the original model.", "additionalProperties": True},
        "supplementary_files": {
            "type": "array",
            "description": "List of supplementary file patterns to extract.",
            "items": {"type": "string"},
            "examples": ["*_supp.csv", "data.parquet"]
        }
    }
}

REPRO_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ReproResult",
    "description": "Schema for storing the results of a single paper reproducibility attempt.",
    "type": "object",
    "required": ["doi", "reproduced_metrics", "deviations", "reproducibility_score", "status"],
    "properties": {
        "doi": {"type": "string", "description": "Digital Object Identifier of the paper."},
        "status": {
            "type": "string",
            "enum": ["success", "model_substituted", "data_unavailable", "failed"],
            "description": "Overall status of the reproduction attempt."
        },
        "reproduced_metrics": {
            "type": "object",
            "required": ["mae", "r2", "spearman_rho"],
            "properties": {
                "mae": {"type": "number", "description": "Reproduced Mean Absolute Error."},
                "r2": {"type": "number", "description": "Reproduced R-squared value."},
                "spearman_rho": {"type": "number", "description": "Reproduced Spearman correlation coefficient."}
            }
        },
        "deviations": {
            "type": "object",
            "required": ["delta_mae", "delta_r2", "delta_spearman_rho"],
            "properties": {
                "delta_mae": {"type": "number", "description": "Absolute difference between reproduced and reported MAE."},
                "delta_r2": {"type": "number", "description": "Absolute difference between reproduced and reported R2."},
                "delta_spearman_rho": {"type": "number", "description": "Absolute difference between reproduced and reported Spearman rho."}
            }
        },
        "reproducibility_score": {"type": "number", "description": "The Deviation Index S (0 to 1, where 1 is perfect reproduction)."},
        "sensitivity_analysis": {
            "type": "object",
            "description": "Results from seed sensitivity analysis.",
            "properties": {
                "metric_std": {
                    "type": "object",
                    "properties": {"mae": {"type": "number"}, "r2": {"type": "number"}, "spearman_rho": {"type": "number"}}
                },
                "max_metric_std": {"type": "number", "description": "Maximum standard deviation observed across metrics."}
            }
        },
        "flags": {"type": "array", "description": "List of flags indicating issues (e.g., missing seed, model substitution).", "items": {"type": "string"}},
        "environment_log": {"type": "string", "description": "Snapshot of the execution environment."}
    }
}

STAT_SUMMARY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "StatSummary",
    "description": "Schema for aggregated statistical meta-analysis results across multiple papers.",
    "type": "object",
    "required": ["total_papers", "successful_reproductions", "t_tests", "mixed_effects_model", "heterogeneity"],
    "properties": {
        "total_papers": {"type": "integer", "description": "Total number of papers attempted."},
        "successful_reproductions": {"type": "integer", "description": "Number of papers successfully reproduced."},
        "t_tests": {
            "type": "object",
            "description": "Results of paired t-tests comparing reported vs. reproduced metrics.",
            "properties": {
                "mae": {"type": "object", "properties": {"t_statistic": {"type": "number"}, "p_value": {"type": "number"}, "bonferroni_p_value": {"type": "number"}}},
                "r2": {"type": "object", "properties": {"t_statistic": {"type": "number"}, "p_value": {"type": "number"}, "bonferroni_p_value": {"type": "number"}}},
                "spearman_rho": {"type": "object", "properties": {"t_statistic": {"type": "number"}, "p_value": {"type": "number"}, "bonferroni_p_value": {"type": "number"}}}
            }
        },
        "mixed_effects_model": {
            "type": "object",
            "description": "Results from the Linear Mixed-Effects model analysis.",
            "properties": {
                "variance_components": {"type": "object", "description": "Variance attributed to random effects (e.g., paper ID).", "additionalProperties": {"type": "number"}},
                "fixed_effects": {"type": "object", "description": "Coefficients for fixed effects (if any were modeled).", "additionalProperties": {"type": "number"}},
                "convergence_status": {"type": "string", "description": "Convergence status of the optimization."}
            }
        },
        "heterogeneity": {
            "type": "object",
            "description": "Heterogeneity statistics (I-squared, etc.).",
            "properties": {
                "i_squared": {"type": "number", "description": "I-squared statistic representing percentage of variation due to heterogeneity."},
                "pooled_effect_size": {"type": "number", "description": "Pooled effect size across studies."}
            }
        },
        "bland_altman_plots": {"type": "array", "description": "List of generated Bland-Altman plot file paths.", "items": {"type": "string"}},
        "equivalence_tests": {
            "type": "object",
            "description": "Results of TOST (Two One-Sided Tests) for equivalence.",
            "properties": {
                "mae": {"type": "object", "properties": {"equivalent": {"type": "boolean"}, "p_value_lower": {"type": "number"}, "p_value_upper": {"type": "number"}}},
                "r2": {"type": "object", "properties": {"equivalent": {"type": "boolean"}, "p_value_lower": {"type": "number"}, "p_value_upper": {"type": "number"}}},
                "spearman_rho": {"type": "object", "properties": {"equivalent": {"type": "boolean"}, "p_value_lower": {"type": "number"}, "p_value_upper": {"type": "number"}}}
            }
        }
    }
}

def main():
    """Generate JSON schema files to the contracts directory."""
    # Ensure the contracts directory exists
    os.makedirs(CONTRACTS_DIR, exist_ok=True)

    schemas = [
        ("PaperManifest", PAPER_MANIFEST_SCHEMA),
        ("ReproResult", REPRO_RESULT_SCHEMA),
        ("StatSummary", STAT_SUMMARY_SCHEMA)
    ]

    for name, schema in schemas:
        file_path = CONTRACTS_DIR / f"{name}.schema.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)
        print(f"Generated: {file_path}")

    print("All schemas generated successfully.")

if __name__ == "__main__":
    main()
