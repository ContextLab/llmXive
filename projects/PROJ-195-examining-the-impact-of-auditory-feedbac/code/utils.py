import os
import sys
import logging
import json
import re
from pathlib import Path
from typing import List, Set, Dict, Optional

def setup_logging(log_file_path: Path) -> logging.Logger:
    """
    Sets up logging to both console and a JSON-formatted log file.
    """
    logger = logging.getLogger("preprocessing")
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler (JSON format for structured logging as per task T019)
    fh = logging.FileHandler(log_file_path)
    fh.setLevel(logging.INFO)
    # Custom formatter to output JSON
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "message": record.getMessage(),
                "subject": getattr(record, 'subject', None),
                "step": getattr(record, 'step', None),
                "details": getattr(record, 'details', None)
            }
            return json.dumps(log_record)

    json_formatter = JsonFormatter()
    fh.setFormatter(json_formatter)
    logger.addHandler(fh)

    return logger


def get_bids_subject_path(bids_root: Path, subject_id: str) -> Path:
    return bids_root / subject_id


def get_bids_func_file(subject_path: Path) -> Path:
    # Typical BIDS structure: sub-XX/func/sub-XX_task-*_bold.nii.gz
    func_dir = subject_path / "func"
    if not func_dir.exists():
        raise FileNotFoundError(f"Func directory not found in {func_dir}")
    files = list(func_dir.glob("*bold.nii.gz"))
    if not files:
        raise FileNotFoundError(f"No bold files found in {func_dir}")
    return files[0]


def get_fmriprep_output_path(derivatives_root: Path, subject_id: str) -> Path:
    return derivatives_root / "sub-" + subject_id.replace("sub-", "") / "func"


def get_motion_file(derivatives_root: Path, subject_id: str) -> Path:
    # fMRIPrep output: sub-XX/func/sub-XX_desc-preproc_bold.json (metadata)
    # Motion parameters are usually in sub-XX/func/sub-XX_desc-confounds_regressors.tsv
    # Or specifically motion files if generated separately.
    # We look for the confounds regressors file which contains motion parameters.
    sub_dir = derivatives_root / subject_id / "func"
    if not sub_dir.exists():
        return Path("")
    
    # Look for confounds file
    confounds_files = list(sub_dir.glob("*confounds_regressors.tsv"))
    if confounds_files:
        return confounds_files[0]
    
    # Fallback or specific motion file if structure differs
    return Path("")


def parse_motion_parameters(confounds_file: Path) -> List[float]:
    """
    Parses the framewise displacement or translation/rotation parameters from the confounds file.
    Returns a list of displacement values (in mm) for each frame.
    """
    displacements = []
    if not confounds_file.exists():
        return displacements

    try:
        with open(confounds_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                return displacements
            
            header = lines[0].strip().split('\t')
            
            # Find columns for translation (trans_x, trans_y, trans_z) and rotation (rot_x, rot_y, rot_z)
            # Or if 'framewise_displacement' exists, use that directly.
            if 'framewise_displacement' in header:
                fd_idx = header.index('framewise_displacement')
                for line in lines[1:]:
                    if line.strip():
                        vals = line.strip().split('\t')
                        try:
                            displacements.append(float(vals[fd_idx]))
                        except (ValueError, IndexError):
                            continue
            else:
                # Calculate FD from trans and rot if FD column missing
                # Standard FD: |dx| + |dy| + |dz| + |drot_x| + |drot_y| + |drot_z| (rot in mm approx)
                # We need to convert rotation (rad) to mm. Approx: 50mm radius * rad.
                indices = {}
                for col in ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']:
                    if col in header:
                        indices[col] = header.index(col)
                
                if len(indices) < 6:
                    # Fallback: just return 0.0 if we can't calculate
                    return [0.0] * (len(lines) - 1)

                prev_vals = None
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    vals = line.strip().split('\t')
                    try:
                        curr_vals = [float(vals[indices[col]]) for col in ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']]
                        if prev_vals:
                            fd = sum(abs(curr - prev) for curr, prev in zip(curr_vals, prev_vals))
                            # Convert rotation diff to mm (approx 50mm radius)
                            # The first 3 are already mm. The last 3 are radians.
                            # FD = |dx| + |dy| + |dz| + 50*(|drot_x| + |drot_y| + |drot_z|)
                            fd = abs(curr_vals[0]-prev_vals[0]) + abs(curr_vals[1]-prev_vals[1]) + abs(curr_vals[2]-prev_vals[2]) + \
                                 50 * (abs(curr_vals[3]-prev_vals[3]) + abs(curr_vals[4]-prev_vals[4]) + abs(curr_vals[5]-prev_vals[5]))
                            displacements.append(fd)
                        else:
                            displacements.append(0.0) # First frame is 0 displacement
                        prev_vals = curr_vals
                    except (ValueError, IndexError):
                        continue
    except Exception as e:
        # Log error but return empty to avoid crash
        print(f"Error parsing motion parameters: {e}")
        return []

    return displacements


def calculate_frame_displacement(motion_params: List[float]) -> float:
    """
    Calculates the maximum frame displacement from a list of values.
    """
    if not motion_params:
        return 0.0
    return max(motion_params)


def check_motion_threshold(displacement: float, threshold: float = 2.0) -> bool:
    """
    Returns True if displacement is within threshold, False otherwise.
    """
    return displacement <= threshold


def log_qc_metrics(logger: logging.Logger, subject_id: str, max_disp: float, threshold: float):
    """
    Logs QC metrics for a subject.
    """
    logger.info(f"Subject {subject_id}: Max Motion = {max_disp:.2f}mm (Threshold: {threshold}mm)")


def log_preprocessing_deviations(logger: logging.Logger, deviation: Dict):
    """
    Logs a specific pipeline deviation to the logger.
    The logger is configured to output JSON to the file.
    """
    # Create a record with extra fields
    extra = {
        'subject': deviation.get('subject'),
        'step': deviation.get('step'),
        'details': json.dumps(deviation.get('details', '')) if not isinstance(deviation.get('details'), str) else deviation.get('details')
    }
    msg = f"Deviation in {deviation.get('step')} for {deviation.get('subject')}: {deviation.get('status')}"
    logger.info(msg, extra=extra)


def filter_subjects_by_motion(subjects: List[str], output_dir: Path, threshold: float = 2.0) -> List[str]:
    """
    Filters subjects based on motion threshold.
    """
    valid = []
    for sub in subjects:
        motion_file = get_motion_file(output_dir, sub)
        if motion_file.exists():
            params = parse_motion_parameters(motion_file)
            max_disp = max(params) if params else 0.0
            if max_disp <= threshold:
                valid.append(sub)
    return valid


def get_event_file_path(bids_root: Path, subject_id: str) -> Path:
    subject_path = get_bids_subject_path(bids_root, subject_id)
    func_dir = subject_path / "func"
    files = list(func_dir.glob("*events.tsv"))
    if not files:
        raise FileNotFoundError(f"No events file found for {subject_id}")
    return files[0]


def validate_event_labels(bids_root: Path, subject_id: str, required_labels: List[str]) -> bool:
    """
    Validates that the events file contains all required labels (normal, delayed, pitch-shifted).
    """
    try:
        events_path = get_event_file_path(bids_root, subject_id)
        with open(events_path, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                return False
            
            header = lines[0].strip().split('\t')
            if 'trial_type' not in header:
                return False
            
            idx = header.index('trial_type')
            found_labels = set()
            for line in lines[1:]:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) > idx:
                        found_labels.add(parts[idx])
            
            return all(label in found_labels for label in required_labels)
    except Exception:
        return False


def validate_all_subjects_events(bids_root: Path, subject_ids: List[str], required_labels: List[str]) -> bool:
    """
    Validates event labels for all subjects. Returns False if any subject is missing labels.
    """
    for sub in subject_ids:
        if not validate_event_labels(bids_root, sub, required_labels):
            return False
    return True
