import os
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import re

import pandas as pd
import numpy as np

from utils.logging import get_logger, log_error, log_warning, log_info

logger = get_logger(__name__)


@dataclass
class NormalPoint:
    """
    Represents a single SLR normal point observation.
    Corresponds to the 'Normal Point' data structure in ILRS files.
    """
    satellite_id: str
    epoch: datetime
    range_m: float
    range_rate: Optional[float] = None
    residual_m: Optional[float] = None
    sigma_m: Optional[float] = None
    station_id: Optional[str] = None
    flags: str = ""

class DataParsingError(Exception):
    """Raised when raw SLR file parsing fails."""
    pass


def parse_ilrs_normal_point_line(line: str, satellite_id: str) -> Optional[NormalPoint]:
    """
    Parses a single line from an ILRS normal point file into a NormalPoint object.
    
    Expected format (standard ILRS ASCII):
    YYYY MM DD HH MM SS.SSSS  RANGE  RANGE_RATE  RESIDUAL  SIGMA  ...
    Or strictly formatted columns depending on the specific source (UCI/ILRS).
    
    We use a robust whitespace-split approach to handle variations in spacing.
    """
    line = line.strip()
    if not line or line.startswith('#') or line.startswith('!'):
        return None

    parts = line.split()
    
    # Minimum expected columns: Date(6) + Time(1) + Range(1) = 8
    # Typical: Date(6) + Time(1) + Range(1) + RangeRate(1) + Residual(1) + Sigma(1) + Station(1)
    if len(parts) < 8:
        log_warning(f"Line too short to parse: {line[:50]}...")
        return None

    try:
        # Parse Date and Time
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        hour = int(parts[3])
        minute = int(parts[4])
        # Seconds might be float
        second_str = parts[5]
        if '.' in second_str:
            second = float(second_str)
        else:
            second = float(second_str)
        
        epoch = datetime(year, month, day, hour, minute, int(second), int((second % 1) * 1e6))
        
        # Parse Range (meters)
        range_m = float(parts[6])
        
        # Parse optional fields
        range_rate = None
        residual_m = None
        sigma_m = None
        station_id = None

        if len(parts) > 7:
            try:
                range_rate = float(parts[7])
            except ValueError:
                pass # Might be station ID if format varies

        if len(parts) > 8:
            try:
                residual_m = float(parts[8])
            except ValueError:
                pass

        if len(parts) > 9:
            try:
                sigma_m = float(parts[9])
            except ValueError:
                pass

        if len(parts) > 10:
            station_id = parts[10]

        return NormalPoint(
            satellite_id=satellite_id,
            epoch=epoch,
            range_m=range_m,
            range_rate=range_rate,
            residual_m=residual_m,
            sigma_m=sigma_m,
            station_id=station_id
        )
    except (ValueError, IndexError) as e:
        log_warning(f"Failed to parse line due to format error: {e} -> {line[:40]}...")
        return None


def parse_slr_file(file_path: str, satellite_id: str) -> list[NormalPoint]:
    """
    Reads a raw SLR file and parses it into a list of NormalPoint objects.
    
    Args:
        file_path: Path to the raw .txt or .dat file.
        satellite_id: Identifier for the satellite (e.g., 'LAGEOS-1').
        
    Returns:
        List of NormalPoint objects.
    """
    logger.info(f"Parsing SLR file: {file_path} for {satellite_id}")
    points = []
    errors = 0
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"SLR file not found: {file_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    point = parse_ilrs_normal_point_line(line, satellite_id)
                    if point:
                        points.append(point)
                except Exception as e:
                    errors += 1
                    if errors > 10:
                        log_warning("Too many parse errors, stopping early.")
                        break
                    continue
    except UnicodeDecodeError:
        # Fallback for binary or weird encoding
        log_warning(f"Retrying {file_path} with latin-1 encoding due to UTF-8 error.")
        with open(path, 'r', encoding='latin-1') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    point = parse_ilrs_normal_point_line(line, satellite_id)
                    if point:
                        points.append(point)
                except Exception:
                    continue

    logger.info(f"Parsed {len(points)} normal points from {file_path}. Skipped {errors} lines.")
    return points


def normal_points_to_dataframe(points: list[NormalPoint]) -> pd.DataFrame:
    """
    Converts a list of NormalPoint objects into a pandas DataFrame.
    """
    if not points:
        return pd.DataFrame()
    
    data = {
        'satellite_id': [p.satellite_id for p in points],
        'epoch': [p.epoch for p in points],
        'range_m': [p.range_m for p in points],
        'range_rate': [p.range_rate for p in points],
        'residual_m': [p.residual_m for p in points],
        'sigma_m': [p.sigma_m for p in points],
        'station_id': [p.station_id for p in points]
    }
    df = pd.DataFrame(data)
    
    # Ensure epoch is datetime type
    df['epoch'] = pd.to_datetime(df['epoch'])
    
    return df


def ingest_raw_data_to_dataframe(raw_files_map: dict[str, str]) -> pd.DataFrame:
    """
    Orchestrates the parsing of multiple raw SLR files into a single DataFrame.
    
    Args:
        raw_files_map: Dict mapping satellite_id -> file_path.
        
    Returns:
        Combined DataFrame of all NormalPoints.
    """
    all_points = []
    
    for sat_id, file_path in raw_files_map.items():
        try:
            points = parse_slr_file(file_path, sat_id)
            all_points.extend(points)
        except Exception as e:
            log_error(f"Failed to ingest {file_path}: {e}")
            continue
    
    if not all_points:
        log_warning("No data points parsed from any files.")
        return pd.DataFrame()
        
    return normal_points_to_dataframe(all_points)
