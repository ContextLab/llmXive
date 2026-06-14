"""
Data saver module for T018: Save raw data and cleaned data to disk.

This module handles saving:
- Raw downloaded data to data/raw/knot_atlas_raw.json
- Cleaned/processed data to data/processed/knots_cleaned.csv
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from download.knot_atlas_loader import KnotRecord, KnotAtlasDownloader
from data.parser import ParsedKnotData, parse_knot_atlas_data
from data.validator import (
    validate_dataset_data_quality,
    write_data_quality_report,
    DataQualityFlags
)
from reproducibility.logs import log_operation, get_logger
from reproducibility.hashing import record_artifact_hash, compute_file_hash


class DataSaver:
    """Handles saving raw and cleaned knot data to disk."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.raw_data_path = project_root / "data" / "raw" / "knot_atlas_raw.json"
        self.cleaned_data_path = project_root / "data" / "processed" / "knots_cleaned.csv"
        self.logger = get_logger(project_root)
        
    def save_raw_data(self, records: List[KnotRecord]) -> Path:
        """Save raw downloaded data to JSON.
        
        Args:
            records: List of KnotRecord objects from download
            
        Returns:
            Path to the saved JSON file
        """
        # Ensure directory exists
        self.raw_data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and save
        data = [record.to_dict() for record in records]
        with open(self.raw_data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Log operation
        log_operation(
            self.logger, 
            "save_raw_data",
            input_file="knot_atlas_download",
            output_file=str(self.raw_data_path),
            parameters={"record_count": len(records)},
            status="success"
        )
        
        # Record artifact hash for reproducibility
        record_artifact_hash(
            self.project_root,
            "knot_atlas_raw",
            compute_file_hash(self.raw_data_path)
        )
        
        return self.raw_data_path
    
    def save_cleaned_data(self, records: List[ParsedKnotData],
                         flags: Optional[DataQualityFlags] = None) -> Path:
        """Save cleaned/processed data to CSV.
        
        Args:
            records: List of ParsedKnotData objects
            flags: Optional data quality flags to include
            
        Returns:
            Path to the saved CSV file
        """
        # Ensure directory exists
        self.cleaned_data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Define CSV fields based on ParsedKnotData structure
        fieldnames = [
            'knot_id', 'crossing_number', 'braid_index', 'hyperbolic_volume',
            'is_alternating', 'dt_code', 'braid_word', 'flags'
        ]
        
        with open(self.cleaned_data_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in records:
                row = {
                    'knot_id': record.knot_id,
                    'crossing_number': record.crossing_number,
                    'braid_index': record.braid_index,
                    'hyperbolic_volume': record.hyperbolic_volume,
                    'is_alternating': record.is_alternating,
                    'dt_code': record.dt_code,
                    'braid_word': record.braid_word,
                    'flags': flags.get_flags(record.knot_id).to_json() if flags else ''
                }
                writer.writerow(row)
        
        # Log operation
        log_operation(
            self.logger,
            "save_cleaned_data",
            input_file="parsed_knot_data",
            output_file=str(self.cleaned_data_path),
            parameters={"record_count": len(records)},
            status="success"
        )
        
        # Record artifact hash for reproducibility
        record_artifact_hash(
            self.project_root,
            "knots_cleaned",
            compute_file_hash(self.cleaned_data_path)
        )
        
        return self.cleaned_data_path
    
    def save_raw_and_cleaned_data(self, raw_records: List[KnotRecord]) -> tuple:
        """Complete pipeline: save raw data, parse, validate, and save cleaned data.
        
        Args:
            raw_records: List of raw KnotRecord objects from download
            
        Returns:
            Tuple of (raw_data_path, cleaned_data_path)
        """
        # Step 1: Save raw data
        raw_path = self.save_raw_data(raw_records)
        
        # Step 2: Parse raw data
        parsed_records = parse_knot_atlas_data(raw_records)
        
        # Step 3: Validate data quality
        flags, report = validate_dataset_data_quality(parsed_records)
        
        # Step 4: Write data quality report
        report_path = self.project_root / "docs" / "reproducibility" / "data_quality_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        write_data_quality_report(report, report_path)
        
        # Step 5: Save cleaned data
        cleaned_path = self.save_cleaned_data(parsed_records, flags)
        
        return raw_path, cleaned_path
    
    def save_raw_data_from_downloader(self, downloader: KnotAtlasDownloader) -> tuple:
        """Download data and save both raw and cleaned versions.
        
        Args:
            downloader: KnotAtlasDownloader instance
            
        Returns:
            Tuple of (raw_data_path, cleaned_data_path)
        """
        # Download raw data
        raw_records = downloader.download()
        
        # Save both versions
        return self.save_raw_and_cleaned_data(raw_records)

def save_raw_and_cleaned_data(project_root: Path, 
                              raw_records: List[KnotRecord]) -> tuple:
    """Convenience function to save raw and cleaned data.
    
    Args:
        project_root: Path to project root directory
        raw_records: List of raw KnotRecord objects
        
    Returns:
        Tuple of (raw_data_path, cleaned_data_path)
    """
    saver = DataSaver(project_root)
    return saver.save_raw_and_cleaned_data(raw_records)

def main():
    """Main entry point for data saving pipeline."""
    import sys
    
    project_root = Path(__file__).parent.parent.parent
    
    # Initialize downloader and saver
    downloader = KnotAtlasDownloader(project_root)
    saver = DataSaver(project_root)
    
    # Download and save data
    print("Downloading knot data from Knot Atlas...")
    raw_path, cleaned_path = saver.save_raw_data_from_downloader(downloader)
    
    print(f"Raw data saved to: {raw_path}")
    print(f"Cleaned data saved to: {cleaned_path}")
    
    return raw_path, cleaned_path

if __name__ == "__main__":
    main()
