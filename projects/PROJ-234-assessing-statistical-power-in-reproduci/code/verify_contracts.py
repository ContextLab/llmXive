import yaml
import jsonschema
from pathlib import Path
import sys

def verify_schema(schema_name, minimal_instance):
    print(f"Verifying {schema_name}...")
    schema_path = Path(f"contracts/{schema_name}")
    
    if not schema_path.exists():
        print(f"  ✗ File not found: {schema_path}")
        return False
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        print(f"  ✓ Parsed with yaml.safe_load")
        
        jsonschema.Draft7Validator.check_schema(schema)
        print(f"  ✓ Valid Draft-07 schema structure")
        
        jsonschema.validate(instance=minimal_instance, schema=schema)
        print(f"  ✓ Passed validation against minimal instance")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    test_cases = [
        ("dataset_metadata.schema.yaml", {
            "dataset_id": 1,
            "name": "Test Dataset",
            "download_count": 100,
            "task_type": "Supervised Classification"
        }),
        ("power_audit_result.schema.yaml", {
            "dataset_id": 1,
            "observed_power": 0.85,
            "mdes": 0.2,
            "threshold_met": True,
            "status": "success"
        }),
        ("extracted_params.schema.yaml", {
            "dataset_id": 1,
            "sample_size": 100,
            "effect_size": 0.5,
            "metric_type": "Cohen's d",
            "source_url": "https://example.com/pub",
            "status": "success"
        }),
        ("report.schema.yaml", {
            "report_metadata": {
                "generated_at": "2024-05-21T12:00:00Z",
                "pipeline_version": "1.0.0",
                "total_datasets_analyzed": 50
            },
            "dataset_ingestion_summary": {
                "total_fetched": 50,
                "total_filtered": 40,
                "type_distribution": {"binary": 30, "multi": 10}
            },
            "extraction_statistics": {
                "success_rate": 0.6,
                "failure_reasons": {"paywalled": 5, "unparseable": 9},
                "sensitivity_delta": {
                    "full_text_rate": 0.5,
                    "combined_rate": 0.6,
                    "delta": 0.1
                }
            },
            "observed_power_results": {
                "histogram_path": "figures/power_hist.png",
                "fraction_below_threshold": 0.4
            },
            "mdes_results": {
                "histogram_path": "figures/mdes_hist.png",
                "summary_statistics": {
                    "median": 0.2,
                    "iqr": 0.1,
                    "min": 0.1,
                    "max": 0.3
                }
            },
            "success_metrics": {
                "observed_power_below_threshold": 0.4,
                "mdes_above_threshold": 0.3
            },
            "disclaimer": "Observed power is a monotone function of the p-value."
        })
    ]
    
    all_passed = True
    for schema_name, instance in test_cases:
        if not verify_schema(schema_name, instance):
            all_passed = False
    
    if all_passed:
        print("\nALL CONTRACTS VERIFIED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("\nSOME CONTRACTS FAILED VERIFICATION")
        sys.exit(1)

if __name__ == "__main__":
    main()