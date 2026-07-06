import numpy as np
import pandas as pd
from typing import Optional, Tuple
from sklearn.preprocessing import MinMaxScaler

def compute_gaze_variance(
    gaze_data: pd.DataFrame,
    window_size: float = 1.0,
    sfreq: float = 1000.0
) -> pd.DataFrame:
    """
    Compute gaze variance per epoch from gaze data.
    
    Args:
        gaze_data: DataFrame with gaze coordinates (x, y) and timestamps.
        window_size: Window size in seconds for variance calculation.
        sfreq: Sampling frequency of the gaze data.
        
    Returns:
        DataFrame with gaze variance per epoch.
    """
    if 'timestamp' not in gaze_data.columns or 'x' not in gaze_data.columns or 'y' not in gaze_data.columns:
        raise ValueError("Gaze data must contain 'timestamp', 'x', and 'y' columns.")
    
    # Sort by timestamp
    gaze_data = gaze_data.sort_values('timestamp').reset_index(drop=True)
    
    # Calculate variance in sliding windows
    window_points = int(window_size * sfreq)
    if window_points < 2:
        window_points = 2
    
    # Compute variance for x and y
    x_var = gaze_data['x'].rolling(window=window_points).var()
    y_var = gaze_data['y'].rolling(window=window_points).var()
    
    # Combine into a single variance metric
    gaze_variance = np.sqrt(x_var**2 + y_var**2)
    
    # Align with epochs (assuming epochs are time-aligned)
    # This is a simplified version; real implementation would align with epoch timestamps
    result = pd.DataFrame({
        'timestamp': gaze_data['timestamp'],
        'gaze_variance': gaze_variance
    })
    
    return result

def generate_cognitive_load_labels(
    epochs_metadata: pd.DataFrame,
    gaze_variance: pd.DataFrame,
    window_size: float = 1.0,
    sfreq: float = 1000.0
) -> pd.DataFrame:
    """
    Generate continuous cognitive load labels from gaze variance.
    
    Args:
        epochs_metadata: DataFrame with epoch information (start time, duration, etc.).
        gaze_variance: DataFrame with gaze variance over time.
        window_size: Window size for variance calculation.
        sfreq: Sampling frequency.
        
    Returns:
        DataFrame with cognitive load labels per epoch.
    """
    # Merge epochs with gaze variance
    # Assuming epochs_metadata has 'start_time' and 'end_time' columns
    if 'start_time' not in epochs_metadata.columns:
        raise ValueError("epochs_metadata must contain 'start_time' column.")
    
    labels = []
    for _, epoch in epochs_metadata.iterrows():
        start = epoch['start_time']
        end = epoch.get('end_time', start + 2.0)  # Default 2s epoch
        
        # Get gaze variance in this epoch
        mask = (gaze_variance['timestamp'] >= start) & (gaze_variance['timestamp'] <= end)
        epoch_variance = gaze_variance.loc[mask, 'gaze_variance'].mean()
        
        if np.isnan(epoch_variance):
            epoch_variance = 0.0
        
        labels.append({
            'epoch_id': epoch.get('epoch_id', f"epoch_{start}"),
            'cognitive_load': epoch_variance
        })
    
    return pd.DataFrame(labels)

def normalize_labels(
    labels_df: pd.DataFrame,
    subject_id: Optional[str] = None,
    method: str = 'minmax'
) -> pd.DataFrame:
    """
    Normalize cognitive load labels per subject.
    
    Args:
        labels_df: DataFrame with cognitive load labels.
        subject_id: Subject ID for grouping (optional).
        method: Normalization method ('minmax').
        
    Returns:
        DataFrame with normalized labels.
    """
    if method != 'minmax':
        raise ValueError("Only 'minmax' normalization is supported.")
    
    df = labels_df.copy()
    
    if subject_id and 'subject_id' in df.columns:
        groups = df.groupby('subject_id')
    else:
        groups = [df]  # Treat as single group
    
    normalized = []
    for group in groups:
        if isinstance(group, tuple):
            group_df = group[1]
        else:
            group_df = group
        
        scaler = MinMaxScaler()
        group_df['cognitive_load_normalized'] = scaler.fit_transform(
            group_df[['cognitive_load']]
        ).flatten()
        normalized.append(group_df)
    
    return pd.concat(normalized, ignore_index=True)

if __name__ == "__main__":
    print("Labels module loaded successfully.")
