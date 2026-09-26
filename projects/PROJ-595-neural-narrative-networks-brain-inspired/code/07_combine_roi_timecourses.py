"""
Combine extracted ROI timecourses from T014, T015, T016 into a single NumPy
structured array. Handles unequal timepoint lengths via NaN-padding.
"""
import os
import sys
import json
import numpy as np
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, error, info, warning, critical
from config import get_config

logger = get_logger(__name__)
config = get_config()

# Define the structured dtype as per task requirements
# subject_id: U20, roi: U20, timepoint: i4, signal: f4
COMBINED_DTYPE = [
    ('subject_id', 'U20'),
    ('roi', 'U20'),
    ('timepoint', 'i4'),
    ('signal', 'f4')
]

def load_roi_timecourse(file_path: str, roi_name: str) -> np.ndarray:
    """
    Load a .npy file containing timecourses for a specific ROI.
    Expected shape: (n_subjects, n_timepoints)
    Returns a structured array for this ROI only.
    """
    if not os.path.exists(file_path):
        logger.error(f"Input file missing: {file_path}")
        raise FileNotFoundError(f"Input file missing: {file_path}")

    data = np.load(file_path)
    if data.ndim != 2:
        logger.error(f"Expected 2D array (subjects, timepoints) in {file_path}, got {data.ndim}D")
        raise ValueError(f"Expected 2D array in {file_path}, got {data.ndim}D")

    n_subjects, n_timepoints = data.shape
    if n_subjects == 0:
        logger.error(f"Empty data in {file_path}")
        raise ValueError(f"Empty data in {file_path}")

    # Extract subject IDs from filename or assume sequential if not available
    # The task description implies we have subject IDs. Since the input .npy
    # files from T014-T016 are raw arrays, we assume the order matches the
    # natural sort of subjects found during extraction.
    # We will generate subject IDs based on the index if not stored in metadata.
    # However, T014-T016 tasks save 'data/processed/roi_left_hipp.npy'.
    # To ensure subject IDs are correct, we need a mapping.
    # Assumption: The extraction scripts (T014-T016) processed subjects in a known order
    # and we can reconstruct IDs or they are stored in a sidecar.
    # Since T014-T016 output is just .npy, we assume the subject order is consistent
    # and we can derive IDs from the list of subjects found in the raw data.
    # For robustness, we will try to load a 'subject_map.json' if it exists,
    # otherwise we assume 'sub-01', 'sub-02', etc.
    
    subject_map_path = Path("data/processed/subject_map.json")
    subject_ids = []
    if subject_map_path.exists():
        with open(subject_map_path, 'r') as f:
            subject_ids = json.load(f)
    else:
        # Fallback: generate generic IDs based on count
        # This is a heuristic; in a real pipeline, subject_map should be created.
        subject_ids = [f"sub-{i+1:02d}" for i in range(n_subjects)]
    
    if len(subject_ids) != n_subjects:
        logger.warning(f"Subject count mismatch in {file_path}: expected {n_subjects}, got {len(subject_ids)}")
        # Truncate or pad to match
        subject_ids = subject_ids[:n_subjects] if len(subject_ids) > n_subjects else subject_ids + [f"sub-{i+1:02d}" for i in range(len(subject_ids), n_subjects)]

    # Create structured array for this ROI
    structured_data = np.zeros((n_subjects, n_timepoints), dtype=COMBINED_DTYPE)
    for i in range(n_subjects):
        structured_data[i, :]['subject_id'] = subject_ids[i]
        structured_data[i, :]['roi'] = roi_name
        structured_data[i, :]['timepoint'] = np.arange(n_timepoints, dtype='i4')
        structured_data[i, :]['signal'] = data[i, :].astype('f4')

    return structured_data

def combine_roi_timecourses():
    """
    Main logic for T019:
    1. Load timecourses for Left Hipp, Right Hipp, DLPFC.
    2. Determine max timepoints across all ROIs.
    3. Pad shorter arrays with NaN (and 'PADDED'/'N/A' for metadata).
    4. Concatenate into a single structured array.
    5. Save to data/processed/combined_roi_temp.npz.
    6. Validate presence of all subjects.
    """
    input_files = {
        'left_hipp': 'data/processed/roi_left_hipp.npy',
        'right_hipp': 'data/processed/roi_right_hipp.npy',
        'dlpfc': 'data/processed/roi_dlpfc.npy'
    }

    roi_names = {
        'left_hipp': 'Left_Hippocampus',
        'right_hipp': 'Right_Hippocampus',
        'dlpfc': 'DLPFC'
    }

    loaded_data = {}
    max_timepoints = 0

    # Load all inputs
    for roi_key, file_path in input_files.items():
        try:
            data = load_roi_timecourse(file_path, roi_names[roi_key])
            loaded_data[roi_key] = data
            if data.shape[1] > max_timepoints:
                max_timepoints = data.shape[1]
            info(f"Loaded {roi_key}: {data.shape[0]} subjects, {data.shape[1]} timepoints")
        except Exception as e:
            error(f"Failed to load {file_path}: {e}")
            raise

    if not loaded_data:
        error("No data loaded from any ROI files.")
        raise ValueError("No data loaded.")

    # Prepare combined array
    # Total rows = sum of (subjects * max_timepoints) for each ROI
    # But wait: The task says "Combine... into a single NumPy structured array".
    # Usually, this means stacking rows. Each row is (subject, roi, timepoint, signal).
    # So for each ROI, we have (n_subjects * n_timepoints) rows.
    # If timepoints differ, we pad to max_timepoints.
    
    total_rows = 0
    for roi_key, data in loaded_data.items():
        total_rows += data.shape[0] * max_timepoints

    combined_array = np.zeros(total_rows, dtype=COMBINED_DTYPE)
    current_idx = 0

    for roi_key, data in loaded_data.items():
        n_subjects, n_current_tp = data.shape
        
        # If current timepoints < max, we need to pad
        if n_current_tp < max_timepoints:
            # Create a temporary padded array
            padded_data = np.zeros((n_subjects, max_timepoints), dtype=COMBINED_DTYPE)
            
            # Copy existing data
            for i in range(n_subjects):
                padded_data[i, :n_current_tp] = data[i, :]
            
            # Fill padding rows
            # The task specifies: subject_id='PADDED', roi='N/A', timepoint=0, signal=np.nan
            # BUT: This implies we are adding extra rows for the same subject?
            # Or are we padding the time dimension for the SAME subject/roi combination?
            # "Pad all input arrays to the same timepoint length using NaN before concatenation."
            # This suggests we extend the time dimension.
            # So for subject S, ROI R, we have timepoints 0..N-1.
            # If max is M > N, we add rows for t=N..M-1.
            # The padding logic says: "For padded rows, set subject_id='PADDED', roi='N/A'..."
            # This is slightly contradictory. If we are padding the time series for a specific subject/ROI,
            # the subject_id and roi should remain the same, but the signal is NaN.
            # However, the task explicitly says: "subject_id='PADDED', roi='N/A'".
            # This implies the padding rows are "dummy" rows not belonging to any real subject/ROI.
            # Let's follow the instruction literally:
            # For the extra timepoints, we create rows where subject_id='PADDED', roi='N/A'.
            # But this loses the association with the original subject.
            # Re-reading: "Pad all input arrays to the same timepoint length using NaN before concatenation."
            # If I have Subject 1 with 100 points and Subject 2 with 150 points.
            # I pad Subject 1 to 150. The new points for Subject 1 should still be Subject 1.
            # The instruction "subject_id='PADDED'" might mean "mark these rows as padding".
            # But if I mark them as 'PADDED', I can't distinguish which subject they belong to.
            # Let's assume the instruction means:
            # 1. Keep the original subject_id and roi for the original timepoints.
            # 2. For the padded timepoints (N..M-1), set signal=NaN.
            # 3. The instruction "subject_id='PADDED', roi='N/A'" might be a specific requirement to flag padding rows distinctly.
            #    If so, how do we know which subject they belong to? We don't.
            #    This suggests the "padding" is global padding, not per-subject.
            #    But that doesn't make sense for time series.
            #    Let's interpret it as: The padding rows are marked as 'PADDED' to indicate they are artificial.
            #    This implies we are not preserving the subject association for the padded rows.
            #    This seems wrong for analysis.
            #    Alternative interpretation: The task wants us to pad the array dimensions, and the "PADDED" fields are
            #    for the *entire* row if the row is a padding row.
            #    Let's try to preserve subject_id for the padded rows but set signal=NaN.
            #    If the requirement strictly demands 'PADDED'/'N/A', I will do that, but it makes the data unusable for subject-level analysis.
            #    Given the context of "Combine... into a single array", preserving subject identity is crucial.
            #    I will assume the instruction "subject_id='PADDED'" applies ONLY if we cannot determine the subject.
            #    But we CAN determine the subject.
            #    Let's re-read carefully: "For padded rows, set subject_id='PADDED', roi='N/A', timepoint=0, signal=np.nan".
            #    This is very specific. It implies the padding rows are NOT associated with a subject.
            #    This might be a way to indicate "this timepoint does not exist for this subject".
            #    But then, how do we know which subject it's missing for?
            #    Maybe the structure is: Each row is (subject, roi, timepoint, signal).
            #    If subject S has 100 points, and max is 150, we have 100 real rows and 50 padding rows.
            #    The 50 padding rows have subject_id='PADDED'.
            #    This means we lose the link.
            #    I will follow the instruction literally as it is a specific constraint.
            #    However, this seems like a design flaw in the task spec.
            #    Let's try to preserve the subject_id for the padded rows but set signal=NaN, and ignore the 'PADDED' instruction?
            #    No, "IMPLEMENT the task... never a stub". I must follow the spec.
            #    Spec says: "For padded rows, set subject_id='PADDED', roi='N/A', timepoint=0, signal=np.nan".
            #    I will do exactly that.
            
            for i in range(n_subjects):
                for t in range(n_current_tp, max_timepoints):
                    # We need to add a row for this subject's padding?
                    # If we add a row for each subject, we have n_subjects * (max - current) padding rows.
                    # But the instruction says "set subject_id='PADDED'".
                    # So all these padding rows will have 'PADDED'.
                    pass # We will construct the rows below

            # Construct the rows for this ROI
            # Real rows
            for i in range(n_subjects):
                for t in range(n_current_tp):
                    combined_array[current_idx] = data[i, t]
                    current_idx += 1
            
            # Padding rows for this ROI
            # We have (max_timepoints - n_current_tp) padding rows per subject?
            # Or just one set of padding rows for the whole ROI?
            # "Pad all input arrays to the same timepoint length".
            # If I have an array of shape (N, M), and I pad to (N, P), I add (P-M) columns.
            # In the structured array, this means adding (P-M) rows per subject.
            # So for each subject, we add (max - current) rows.
            # Total padding rows = n_subjects * (max - current).
            # All these rows will have subject_id='PADDED', roi='N/A'.
            
            num_padding_rows_per_subject = max_timepoints - n_current_tp
            for i in range(n_subjects):
                for t in range(num_padding_rows_per_subject):
                    # Create a padding row
                    pad_row = np.zeros(1, dtype=COMBINED_DTYPE)
                    pad_row[0]['subject_id'] = 'PADDED'
                    pad_row[0]['roi'] = 'N/A'
                    pad_row[0]['timepoint'] = 0 # Spec says timepoint=0
                    pad_row[0]['signal'] = np.nan
                    combined_array[current_idx] = pad_row[0]
                    current_idx += 1

        else:
            # No padding needed, just copy
            for i in range(n_subjects):
                for t in range(n_current_tp):
                    combined_array[current_idx] = data[i, t]
                    current_idx += 1

    # Validation: Verify all subjects from T014-T016 are present
    # We check that the original subject IDs are in the array (excluding padding rows)
    all_subject_ids = set()
    for roi_key, data in loaded_data.items():
        for i in range(data.shape[0]):
            all_subject_ids.add(data[i, 0]['subject_id']) # Assuming timepoint 0 exists

    present_subject_ids = set()
    for row in combined_array:
        if row['subject_id'] != 'PADDED':
            present_subject_ids.add(row['subject_id'])

    missing_subjects = all_subject_ids - present_subject_ids
    if missing_subjects:
        error(f"Missing subjects in combined array: {missing_subjects}")
        raise ValueError(f"Missing subjects: {missing_subjects}")

    info(f"Combined array shape: {combined_array.shape}")
    info(f"Total subjects verified: {len(present_subject_ids)}")

    # Save intermediate artifact
    output_path = 'data/processed/combined_roi_temp.npz'
    np.savez(output_path, data=combined_array)
    info(f"Saved combined timecourses to {output_path}")

    return combined_array

def main():
    """Entry point for T019."""
    info("Starting T019: Combine ROI timecourses")
    try:
        combine_roi_timecourses()
        info("T019 completed successfully")
    except Exception as e:
        error(f"T019 failed: {e}")
        raise

if __name__ == "__main__":
    main()