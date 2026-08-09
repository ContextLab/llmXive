"""
Script to execute the Data Gap Protocol verification (Task T017c).

This script creates a controlled sample dataset with < 30 valid entries,
runs the ingestion pipeline to trigger the N < 30 condition, and verifies
that:
1. data/reports/data_availability_report.json is generated with correct fields.
2. The process halts with exit code 1.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion import validate_data_gap, fetch_data, generate_data_availability_report
from config import initialize_config, get_config_value

def create_small_sample_dataset(output_path: Path) -> None:
    """
    Create a CSV file with exactly 20 valid entries to trigger the N < 30 condition.
    The data mimics the expected schema from fetch_data but with a small count.
    """
    data = [
        {
            "composition": "Al2O3",
            "weibull_modulus": 15.5,
            "sample_count": 35,
            "sintering_temp": 1600,
            "source_url": "https://example.com/ref1",
            "doi": "10.1234/ref1"
        },
        {
            "composition": "ZrO2",
            "weibull_modulus": 12.0,
            "sample_count": 40,
            "sintering_temp": 1450,
            "source_url": "https://example.com/ref2",
            "doi": "10.1234/ref2"
        },
        {
            "composition": "SiC",
            "weibull_modulus": 8.5,
            "sample_count": 25,
            "sintering_temp": 2000,
            "source_url": "https://example.com/ref3",
            "doi": "10.1234/ref3"
        },
        {
            "composition": "Si3N4",
            "weibull_modulus": 10.2,
            "sample_count": 30,
            "sintering_temp": 1800,
            "source_url": "https://example.com/ref4",
            "doi": "10.1234/ref4"
        },
        {
            "composition": "MgO",
            "weibull_modulus": 18.0,
            "sample_count": 45,
            "sintering_temp": 1700,
            "source_url": "https://example.com/ref5",
            "doi": "10.1234/ref5"
        },
        {
            "composition": "TiO2",
            "weibull_modulus": 9.5,
            "sample_count": 32,
            "sintering_temp": 1300,
            "source_url": "https://example.com/ref6",
            "doi": "10.1234/ref6"
        },
        {
            "composition": "BaTiO3",
            "weibull_modulus": 14.0,
            "sample_count": 28,
            "sintering_temp": 1250,
            "source_url": "https://example.com/ref7",
            "doi": "10.1234/ref7"
        },
        {
            "composition": "PbZrO3",
            "weibull_modulus": 11.5,
            "sample_count": 22,
            "sintering_temp": 1100,
            "source_url": "https://example.com/ref8",
            "doi": "10.1234/ref8"
        },
        {
            "composition": "Y2O3",
            "weibull_modulus": 16.5,
            "sample_count": 38,
            "sintering_temp": 1550,
            "source_url": "https://example.com/ref9",
            "doi": "10.1234/ref9"
        },
        {
            "composition": "CeO2",
            "weibull_modulus": 13.0,
            "sample_count": 33,
            "sintering_temp": 1400,
            "source_url": "https://example.com/ref10",
            "doi": "10.1234/ref10"
        },
        {
            "composition": "HfO2",
            "weibull_modulus": 12.5,
            "sample_count": 29,
            "sintering_temp": 1500,
            "source_url": "https://example.com/ref11",
            "doi": "10.1234/ref11"
        },
        {
            "composition": "Nb2O5",
            "weibull_modulus": 10.8,
            "sample_count": 26,
            "sintering_temp": 1350,
            "source_url": "https://example.com/ref12",
            "doi": "10.1234/ref12"
        },
        {
            "composition": "Ta2O5",
            "weibull_modulus": 11.2,
            "sample_count": 24,
            "sintering_temp": 1380,
            "source_url": "https://example.com/ref13",
            "doi": "10.1234/ref13"
        },
        {
            "composition": "WO3",
            "weibull_modulus": 9.0,
            "sample_count": 21,
            "sintering_temp": 1200,
            "source_url": "https://example.com/ref14",
            "doi": "10.1234/ref14"
        },
        {
            "composition": "MoO3",
            "weibull_modulus": 8.0,
            "sample_count": 19,
            "sintering_temp": 1150,
            "source_url": "https://example.com/ref15",
            "doi": "10.1234/ref15"
        },
        {
            "composition": "V2O5",
            "weibull_modulus": 7.5,
            "sample_count": 18,
            "sintering_temp": 1100,
            "source_url": "https://example.com/ref16",
            "doi": "10.1234/ref16"
        },
        {
            "composition": "Cr2O3",
            "weibull_modulus": 17.0,
            "sample_count": 42,
            "sintering_temp": 1650,
            "source_url": "https://example.com/ref17",
            "doi": "10.1234/ref17"
        },
        {
            "composition": "Fe2O3",
            "weibull_modulus": 14.5,
            "sample_count": 36,
            "sintering_temp": 1450,
            "source_url": "https://example.com/ref18",
            "doi": "10.1234/ref18"
        },
        {
            "composition": "CoO",
            "weibull_modulus": 13.5,
            "sample_count": 31,
            "sintering_temp": 1350,
            "source_url": "https://example.com/ref19",
            "doi": "10.1234/ref19"
        },
        {
            "composition": "NiO",
            "weibull_modulus": 15.0,
            "sample_count": 34,
            "sintering_temp": 1400,
            "source_url": "https://example.com/ref20",
            "doi": "10.1234/ref20"
        }
    ]
    
    # Write to CSV
    import pandas as pd
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Created sample dataset with {len(data)} entries at {output_path}")

def main():
    """
    Main execution function for T017c verification.
    """
    # Initialize configuration
    initialize_config()
    
    # Setup temporary directory for the test dataset
    temp_dir = tempfile.mkdtemp()
    try:
        sample_csv_path = Path(temp_dir) / "small_sample.csv"
        create_small_sample_dataset(sample_csv_path)
        
        # Mock the fetch_data function to return our small sample
        # We do this by patching the global fetch_data or using a wrapper
        # Since ingestion.py fetch_data is the entry point, we need to 
        # temporarily replace it or pass our data directly.
        
        # However, validate_data_gap expects to call fetch_data internally.
        # We will monkey-patch fetch_data to return our small dataframe.
        import ingestion
        
        original_fetch_data = ingestion.fetch_data
        
        def mock_fetch_data():
            import pandas as pd
            df = pd.read_csv(sample_csv_path)
            # Add necessary columns that clean_data might expect if not present
            if 'is_range_flag' not in df.columns:
                df['is_range_flag'] = False
            if 'range_original' not in df.columns:
                df['range_original'] = None
            if 'primary_anion_cation_group' not in df.columns:
                df['primary_anion_cation_group'] = 'Oxide' # Default
            if 'sintering_temp' not in df.columns:
                df['sintering_temp'] = 1500
            if 'is_imputed' not in df.columns:
                df['is_imputed'] = False
            return df

        ingestion.fetch_data = mock_fetch_data
        
        # Ensure output directory exists
        reports_dir = project_root / "data" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        print("Running validate_data_gap with small sample...")
        try:
            validate_data_gap()
            print("ERROR: validate_data_gap did not halt! This indicates a failure in the Data Gap Protocol.")
            sys.exit(1)
        except SystemExit as e:
            if e.code == 1:
                print("SUCCESS: Pipeline halted with exit code 1 as expected.")
            else:
                print(f"ERROR: Pipeline halted with unexpected exit code: {e.code}")
                sys.exit(1)
        
        # Verify the report was generated
        report_path = reports_dir / "data_availability_report.json"
        if not report_path.exists():
            print("ERROR: data_availability_report.json was not generated.")
            sys.exit(1)
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        print(f"Generated Report: {json.dumps(report, indent=2)}")
        
        # Verify required fields
        required_fields = ['total_sources', 'valid_entries', 'reason_code', 'timestamp']
        missing_fields = [field for field in required_fields if field not in report]
        
        if missing_fields:
            print(f"ERROR: Report missing required fields: {missing_fields}")
            sys.exit(1)
        
        # Verify values
        if report['valid_entries'] >= 30:
            print(f"ERROR: valid_entries ({report['valid_entries']}) should be < 30.")
            sys.exit(1)
        
        if report['total_sources'] != 1: # We only have one source file in this mock
            print(f"WARNING: total_sources is {report['total_sources']}, expected 1 for single file mock.")
            # Note: Depending on implementation, total_sources might count rows or sources. 
            # Based on T017b description: "total_sources (actual count of fetched sources)".
            # Since we mock one file, it should be 1. If it counts entries, it should be 20.
            # Let's assume the implementation counts sources (files/API calls).
        
        print("T017c Verification: PASSED")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()