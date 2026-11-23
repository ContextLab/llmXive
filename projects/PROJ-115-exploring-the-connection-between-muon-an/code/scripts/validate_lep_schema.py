"""
Script to generate sample LEP data and validate the LEP_Exclusion_Data schema.

This script demonstrates the schema usage by generating a sample dataset
and running validation checks. It also saves the sample data to disk
for reference.
"""
import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path
from schemas.lep_exclusion_data import LEPExclusionData, LEPExclusionPoint, validate_lep_schema


def generate_sample_lep_data() -> LEPExclusionData:
    """
    Generate a sample LEP exclusion dataset.

    This creates a mock dataset mimicking the structure of real LEP
    exclusion limits (mass vs coupling). The values are illustrative
    and not real experimental data.

    Returns:
        LEPExclusionData: A populated dataset instance.
    """
    # Create a mock exclusion curve: lower coupling for higher mass
    # Typical LEP limits: m_V > 100 MeV, g < 10^-3
    points = []

    # Simulate a simple exclusion boundary
    m_V_values = [100.0, 150.0, 200.0, 250.0, 300.0, 400.0, 500.0, 600.0, 800.0, 1000.0]
    g_values = [5.0e-3, 3.0e-3, 2.0e-3, 1.5e-3, 1.2e-3, 0.8e-3, 0.6e-3, 0.5e-3, 0.3e-3, 0.2e-3]

    for m_v, g in zip(m_V_values, g_values):
        point = LEPExclusionPoint(
            m_V=m_v,
            g=g,
            source="LEP-II (Mock)",
            comment="Sample exclusion point for schema validation"
        )
        points.append(point)

    data = LEPExclusionData(
        points=points,
        metadata={
            "source": "Simulated for schema validation",
            "description": "Mock LEP exclusion limits",
            "units": {"m_V": "MeV", "g": "dimensionless"}
        }
    )
    return data


def main():
    """Main entry point for the schema validation script."""
    print("=== LEP Exclusion Data Schema Validation ===")

    # Generate sample data
    print("\n1. Generating sample LEP exclusion data...")
    sample_data = generate_sample_lep_data()
    print(f"   Generated {len(sample_data.points)} points.")

    # Validate the schema
    print("\n2. Validating schema and content...")
    validation_result = validate_lep_schema(sample_data)

    if validation_result['valid']:
        print("   ✅ Validation PASSED.")
    else:
        print("   ❌ Validation FAILED.")
        for error in validation_result['errors']:
            print(f"      - {error}")

    if validation_result['warnings']:
        print("   ⚠️  Warnings:")
        for warning in validation_result['warnings']:
            print(f"      - {warning}")

    # Convert to DataFrame and display
    print("\n3. Converting to DataFrame...")
    df = sample_data.to_dataframe()
    print(df.head())

    # Save to disk
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "sample_lep_exclusion.json"

    print(f"\n4. Saving sample data to {output_path}...")
    sample_data.to_json(output_path)
    print("   Saved successfully.")

    # Load back and verify
    print("\n5. Loading data back from JSON...")
    loaded_data = LEPExclusionData.from_json(output_path)
    print(f"   Loaded {len(loaded_data.points)} points.")

    # Final check
    final_validation = validate_lep_schema(loaded_data)
    if final_validation['valid']:
        print("   ✅ Round-trip validation PASSED.")
    else:
        print("   ❌ Round-trip validation FAILED.")
        for error in final_validation['errors']:
            print(f"      - {error}")

    print("\n=== Schema Validation Complete ===")
    return 0 if validation_result['valid'] else 1


if __name__ == "__main__":
    sys.exit(main())
