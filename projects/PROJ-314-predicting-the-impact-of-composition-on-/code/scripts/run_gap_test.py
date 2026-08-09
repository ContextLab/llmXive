"""
Script to execute T017c: Verify Data Gap Report generation.

This script:
1. Creates a test dataset with exactly 29 rows (N=29).
2. Runs the ingestion pipeline with --force-gap-check.
3. Verifies that data/reports/data_availability_report.json is generated.
4. Exits with code 1 to simulate the halting logic.
"""
import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
import logging

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from ingestion import validate_data_gap, generate_data_availability_report
from config import load_environment

def create_small_sample_dataset(output_path: Path):
    """
    Creates a test CSV with exactly 29 rows where each row has sample_count >= 30.
    This ensures the total valid entries N = 29, triggering the data gap halt.
    """
    data = {
        "composition": [],
        "weibull_modulus": [],
        "sample_count": [],
        "sintering_temp": [],
        "primary_anion_cation_group": []
    }
    
    # Define 29 distinct ceramic entries
    entries = [
        ("Al2O3", 10.5, 30, 1600.0, "O-Al"),
        ("Si3N4", 12.0, 30, 1400.0, "N-Si"),
        ("ZrO2", 8.5, 30, 1500.0, "O-Zr"),
        ("TiC", 15.0, 30, 2000.0, "C-Ti"),
        ("SiC", 11.0, 30, 1600.0, "C-Si"),
        ("BN", 9.0, 30, 1800.0, "N-B"),
        ("AlN", 10.0, 30, 1700.0, "N-Al"),
        ("MgO", 7.5, 30, 1900.0, "O-Mg"),
        ("CaO", 6.5, 30, 1800.0, "O-Ca"),
        ("Y2O3", 9.5, 30, 1500.0, "O-Y"),
        ("La2O3", 8.0, 30, 1400.0, "O-La"),
        ("CeO2", 7.0, 30, 1600.0, "O-Ce"),
        ("HfO2", 8.8, 30, 1550.0, "O-Hf"),
        ("TaC", 14.0, 30, 2100.0, "C-Ta"),
        ("NbC", 13.5, 30, 2050.0, "C-Nb"),
        ("WC", 16.0, 30, 1900.0, "C-W"),
        ("Mo2C", 12.5, 30, 1950.0, "C-Mo"),
        ("VC", 11.5, 30, 1900.0, "C-V"),
        ("Cr3C2", 10.5, 30, 1850.0, "C-Cr"),
        ("Fe3C", 5.5, 30, 900.0, "C-Fe"),
        ("TiN", 13.0, 30, 1700.0, "N-Ti"),
        ("ZrN", 12.5, 30, 1650.0, "N-Zr"),
        ("HfN", 12.0, 30, 1600.0, "N-Hf"),
        ("VN", 11.0, 30, 1550.0, "N-V"),
        ("TiB2", 14.5, 30, 2000.0, "B-Ti"),
        ("ZrB2", 13.5, 30, 1950.0, "B-Zr"),
        ("HfB2", 13.0, 30, 1900.0, "B-Hf"),
        ("LaB6", 10.0, 30, 1800.0, "B-La"),
        ("CeB6", 9.5, 30, 1750.0, "B-Ce"),
    ]
    
    for comp, wm, count, temp, group in entries:
        data["composition"].append(comp)
        data["weibull_modulus"].append(wm)
        data["sample_count"].append(count)
        data["sintering_temp"].append(temp)
        data["primary_anion_cation_group"].append(group)
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logging.info(f"Created test dataset with {len(df)} rows at {output_path}")
    return df

def main():
    """
    Main execution for T017c verification.
    """
    # Load environment config
    load_environment()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Ensure output directories exist
    project_root = Path(__file__).parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_reports_dir = project_root / "data" / "reports"
    
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    data_reports_dir.mkdir(parents=True, exist_ok=True)
    
    test_file_path = data_raw_dir / "test_n29.csv"
    
    # 1. Create the test dataset
    logging.info("Creating test dataset (N=29)...")
    df = create_small_sample_dataset(test_file_path)
    
    # 2. Run the gap check logic
    logging.info("Running data gap validation with force flag...")
    
    try:
        # Call the ingestion validation logic directly
        # This simulates the --force-gap-check behavior
        validate_data_gap(df, force_check=True)
        
        # If we reach here, the gap check passed (which shouldn't happen for N=29)
        logging.error("ERROR: Validation passed when it should have failed!")
        sys.exit(1)
        
    except SystemExit as e:
        # Expected exit code 1 from the gap check
        if e.code == 1:
            logging.info("Pipeline halted as expected (N < 30).")
            
            # 3. Verify the report was generated
            report_path = data_reports_dir / "data_availability_report.json"
            if report_path.exists():
                with open(report_path, 'r') as f:
                    report = json.load(f)
                
                logging.info(f"Report generated at: {report_path}")
                logging.info(f"Report contents: {json.dumps(report, indent=2)}")
                
                # Verify dynamic fields
                if "valid_entries" in report and report["valid_entries"] == 29:
                    logging.info("SUCCESS: valid_entries correctly set to 29.")
                else:
                    logging.error(f"ERROR: valid_entries is {report.get('valid_entries')}, expected 29.")
                    sys.exit(1)
                    
                if "total_sources" in report:
                    logging.info(f"SUCCESS: total_sources present ({report['total_sources']}).")
                else:
                    logging.error("ERROR: total_sources missing from report.")
                    sys.exit(1)
                    
                if "reason_code" in report:
                    logging.info(f"SUCCESS: reason_code present ({report['reason_code']}).")
                else:
                    logging.error("ERROR: reason_code missing from report.")
                    sys.exit(1)
                    
                logging.info("T017c VERIFICATION PASSED: Data Gap Report generated correctly.")
                sys.exit(0) # Exit 0 to indicate the TEST passed, even though the pipeline halted
            else:
                logging.error(f"ERROR: Report file not found at {report_path}")
                sys.exit(1)
        else:
            logging.error(f"Unexpected exit code: {e.code}")
            sys.exit(e.code)
    except Exception as e:
        logging.error(f"Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
