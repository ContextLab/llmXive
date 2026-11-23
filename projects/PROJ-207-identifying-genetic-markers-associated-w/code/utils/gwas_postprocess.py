"""
Utility to ensure PLINK output is correctly formatted and saved.
This script is called by code/03_gwas.sh to post-process the PLINK output.
It ensures the file exists at the correct path with the correct columns.
"""
import os
import sys
import pandas as pd
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Usage: python gwas_postprocess.py <input_plink_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        sys.exit(1)

    try:
        df = pd.read_csv(input_file, sep='\t')
        
        # Required columns mapping
        # PLINK2 default: CHR, SNP, BP, A1, TEST, NMISS, BETA, SE, Z, P, OR
        required_map = {
            'SNP': 'SNP',
            'CHR': 'CHR',
            'BP': 'POS',
            'P': 'P',
            'OR': 'Odds_Ratio',
            'SE': 'SE'
        }
        
        # Check if all required columns exist
        missing = [k for k in required_map.keys() if k not in df.columns]
        if missing:
            print(f"Error: Missing required PLINK columns: {missing}")
            sys.exit(1)
        
        # Select and rename columns
        result_df = df[list(required_map.keys())].copy()
        result_df.rename(columns=required_map, inplace=True)
        
        # Ensure column order
        result_df = result_df[['SNP', 'CHR', 'POS', 'P', 'Odds_Ratio', 'SE']]
        
        # Write to output
        result_df.to_csv(output_file, sep='\t', index=False)
        print(f"Successfully wrote {len(result_df)} rows to {output_file}")
        
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()