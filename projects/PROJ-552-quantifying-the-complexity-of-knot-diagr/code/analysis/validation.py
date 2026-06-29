"""
Hyperbolic Volume Validation Module.

This module contains the core logic for cross-checking hyperbolic volume
against KnotInfo reference values. It was refactored from hyperbolic_volume_validation.py
to separate validation logic from reporting.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import requests
import pandas as pd
from reproducibility.logs import get_logger, log_operation

logger = get_logger(__name__)

@dataclass
class ValidationEntry:
    """Represents the validation result for a single knot."""
    knot_id: str
    crossing_number: int
    atlas_volume: Optional[float]
    knotinfo_volume: Optional[float]
    match: bool
    error_message: Optional[str] = None
    source: str = "KnotAtlas"
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))

@dataclass
class ValidationResult:
    """Aggregates validation results for the dataset."""
    total_records: int
    successful_lookups: int
    failed_lookups: int
    matches_within_tolerance: int
    matches_percentage: float
    tolerance: float
    entries: List[ValidationEntry] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))

class HyperbolicVolumeValidator:
    """
    Validates hyperbolic volume values from Knot Atlas against KnotInfo.
    
    This class implements the cross-check logic required by FR-013.
    """
    
    KNOTOINFO_API_BASE = "https://knotinfo.math.indiana.edu/api/knotinfo"
    TOLERANCE = 1e-6
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.logger = get_logger(__name__)

    def _fetch_knotinfo_volume(self, knot_id: str) -> Optional[float]:
        """
        Fetch hyperbolic volume for a specific knot from KnotInfo API.
        
        Args:
            knot_id: The knot identifier (e.g., '3_1', '4_1').
            
        Returns:
            The hyperbolic volume as a float, or None if not found/error.
        """
        url = f"{self.KNOTOINFO_API_BASE}/knot/{knot_id}"
        params = {"fields": "hyperbolic_volume"}
        
        try:
            # Add a small delay to be polite to the API
            time.sleep(0.1)
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            # Adjust based on actual API response structure if known
            # Assuming a standard nested structure or flat
            if isinstance(data, dict):
                if 'hyperbolic_volume' in data:
                    val = data['hyperbolic_volume']
                    if val is not None and val != "":
                        return float(val)
                # Fallback for different JSON structures
                for key, value in data.items():
                    if 'volume' in key.lower() and isinstance(value, (int, float)):
                        return float(value)
            elif isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    for key, value in data[0].items():
                        if 'volume' in key.lower() and isinstance(value, (int, float)):
                            return float(value)
                            
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"API request failed for {knot_id}: {e}")
            return None
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to parse volume for {knot_id}: {e}")
            return None

    def validate_single_knot(self, knot_data: Dict[str, Any]) -> ValidationEntry:
        """
        Validate a single knot record.
        
        Args:
            knot_data: Dictionary containing knot information.
            
        Returns:
            ValidationEntry with the result.
        """
        knot_id = knot_data.get("knot_id", knot_data.get("name", "unknown"))
        atlas_volume = knot_data.get("hyperbolic_volume")
        
        entry = ValidationEntry(
            knot_id=knot_id,
            crossing_number=knot_data.get("crossing_number", 0),
            atlas_volume=atlas_volume,
            knotinfo_volume=None,
            match=False
        )
        
        if atlas_volume is None:
            entry.error_message = "Atlas volume missing"
            return entry
            
        try:
            atlas_vol_float = float(atlas_volume)
            if atlas_vol_float <= 0:
                entry.error_message = "Non-positive volume"
                return entry
        except (ValueError, TypeError):
            entry.error_message = "Invalid atlas volume format"
            return entry

        # Fetch from KnotInfo
        ki_volume = self._fetch_knotinfo_volume(knot_id)
        entry.knotinfo_volume = ki_volume
        
        if ki_volume is None:
            entry.error_message = "KnotInfo lookup failed or volume not found"
            return entry
            
        # Compare
        if abs(atlas_vol_float - float(ki_volume)) <= self.tolerance:
            entry.match = True
        else:
            entry.error_message = f"Mismatch: Atlas={atlas_vol_float}, KnotInfo={ki_volume}"
            
        return entry

    def validate_dataset(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate the entire dataset.
        
        Args:
            df: DataFrame containing knot data.
            
        Returns:
            ValidationResult with aggregated statistics.
        """
        results = []
        successful = 0
        failed = 0
        matches = 0
        
        total = len(df)
        logger.info(f"Starting validation for {total} knots.")
        
        for idx, row in df.iterrows():
            entry = self.validate_single_knot(row.to_dict())
            results.append(entry)
            
            if entry.error_message is None:
                successful += 1
                if entry.match:
                    matches += 1
            else:
                failed += 1
                
            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1}/{total} knots.")

        percentage = (matches / successful * 100) if successful > 0 else 0.0
        
        return ValidationResult(
            total_records=total,
            successful_lookups=successful,
            failed_lookups=failed,
            matches_within_tolerance=matches,
            matches_percentage=percentage,
            tolerance=self.tolerance,
            entries=results
        )

def load_cleaned_knots(path: Path) -> pd.DataFrame:
    """Helper to load the cleaned knots dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {path}")
    return pd.read_csv(path)

def run_validation(
    input_path: Path,
    output_json_path: Optional[Path] = None,
    output_md_path: Optional[Path] = None
) -> ValidationResult:
    """
    Main entry point for running the validation pipeline.
    
    Args:
        input_path: Path to the cleaned knots CSV.
        output_json_path: Optional path to save JSON results.
        output_md_path: Optional path to save Markdown report.
        
    Returns:
        ValidationResult object.
    """
    log_operation("validation_start", "Hyperbolic Volume Validation", {"input": str(input_path)})
    
    df = load_cleaned_knots(input_path)
    validator = HyperbolicVolumeValidator()
    result = validator.validate_dataset(df)
    
    if output_json_path:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json_path, 'w') as f:
            json.dump([asdict(e) for e in result.entries], f, indent=2)
        logger.info(f"Saved detailed results to {output_json_path}")
        
    if output_md_path:
        output_md_path.parent.mkdir(parents=True, exist_ok=True)
        # Report generation is delegated to validation_reporting.py
        # This function just returns the result for the caller to handle
        pass
        
    log_operation("validation_end", "Hyperbolic Volume Validation", {
        "status": "completed",
        "matches_percentage": result.matches_percentage
    })
    
    return result

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate hyperbolic volumes against KnotInfo.")
    parser.add_argument("--input", type=Path, default=Path("data/processed/knots_cleaned.csv"),
                        help="Path to cleaned knots CSV.")
    parser.add_argument("--output-json", type=Path, default=Path("data/processed/validation_results.json"),
                        help="Path to output JSON results.")
    parser.add_argument("--output-md", type=Path, default=Path("docs/reproducibility/hyperbolic_volume_validation.md"),
                        help="Path to output Markdown report.")
    
    args = parser.parse_args()
    
    result = run_validation(args.input, args.output_json, args.output_md)
    
    print(f"Validation Complete.")
    print(f"Total Records: {result.total_records}")
    print(f"Successful Lookups: {result.successful_lookups}")
    print(f"Matches: {result.matches_within_tolerance} ({result.matches_percentage:.2f}%)")
    
    return result

if __name__ == "__main__":
    main()
