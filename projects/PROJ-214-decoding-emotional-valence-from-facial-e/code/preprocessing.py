import os
import logging
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, iirnotch

# Existing functions (omitted for brevity - see provided content)
def butter_bandpass(cutoff, fs, order=5):
    """Butterworth band-pass filter."""
    nyq = 0.5 * fs
    low = cutoff / nyq
    high = 1.0  # No high cut-off for EMG
    b, a = butter(order, [low, high], btype='band')
    return b, a

def apply_bandpass_filter(data, fs, cutoff):
    """Applies Butterworth band-pass filter."""
    b, a = butter_bandpass(cutoff, fs)
    y = filtfilt(b, a, data)
    return y

def apply_notch_filter(data, fs, freq=50.0):
    """Applies notch filter to remove 50Hz noise."""
    Q = 30.0
    w0 = freq / (fs / 2)
    b, a = iirnotch(w0, Q)
    y = filtfilt(b, a, data)
    return y

def baseline_correct(data):
    """Corrects EMG signal to zero mean."""
    return data - np.mean(data)

def extract_rms(data):
    """Calculates Root Mean Square (RMS) feature."""
    return np.sqrt(np.mean(data**2))

def extract_zcr(data):
    """Calculates Zero Crossing Rate (ZCR) feature."""
    crossings = np.diff(np.sign(data))
    return np.sum(crossings != 0) / len(data)

def extract_wamp(data):
    """Calculates Wavelet Amplitude Mean (WAMP) feature."""
    return np.mean(np.abs(data))

def extract_mav(data):
    """Calculates Mean Absolute Value (MAV) feature."""
    return np.mean(np.abs(data))

def create_windows(data, window_size, stride):
  """Creates overlapping windows from the data."""
  num_windows = (len(data) - window_size) // stride + 1
  windows = []
  for i in range(num_windows):
      start = i * stride
      end = start + window_size
      windows.append(data[start:end])
  return np.array(windows)

def extract_features(window, rms=True, zcr=True, wamp=True, mav=True):
    """Extracts features from a single window."""
    features = []
    if rms:
        features.append(extract_rms(window))
    if zcr:
        features.append(extract_zcr(window))
    if wamp:
        features.append(extract_wamp(window))
    if mav:
        features.append(extract_mav(window))
    return np.array(features)

def check_skewed_valence(valence_scores):
  """Checks if all valence scores are above or below a threshold."""
  return np.all(valence_scores > 5) or np.all(valence_scores < 5)
    
def process_subject_signals(emg_data, valence_scores, fs=128, cutoff=30.0):
    """Processes EMG signals for a single subject."""
    # Apply filters
    filtered_emg = apply_bandpass_filter(emg_data, fs, cutoff)
    filtered_emg = apply_notch_filter(filtered_emg, fs)

    # Baseline correct
    baseline_corrected_emg = baseline_correct(filtered_emg)
    
    return baseline_corrected_emg  # Return processed EMG data 

def preprocess_all_subjects(data_dir):
  """Processes all subjects in the dataset."""
  processed_data = {}
  exclusions = []

  for subject_id in os.listdir(data_dir):
      subject_path = os.path.join(data_dir, subject_id)
      if not os.path.isdir(subject_path):
          continue

      try:
          # Load EMG data and valence scores (replace with actual loading logic)
          emg_data = np.load(os.path.join(subject_path, 'emg_data.npy'))  # Assuming EMG data is stored as numpy array
          valence_scores = np.load(os.path.join(subject_path, 'valence_scores.npy')) # Replace with actual loading

          # Check for skewed valence scores
          if check_skewed_valence(valence_scores):
              logging.warning(f"Subject {subject_id} has skewed valence scores. Excluding from analysis.")
              exclusions.append(subject_id)
              continue

          # Process the signals
          processed_emg = process_subject_signals(emg_data, valence_scores)

          # Store processed data
          processed_data[subject_id] = processed_emg
      except Exception as e:
          logging.error(f"Error processing subject {subject_id}: {e}")
          exclusions.append(subject_id)

  return processed_data, exclusions
    
def impute_missing_channels(emg_data):
    """Imputes missing EMG channels using the median value."""
    num_channels = emg_data.shape[1]
    imputed_data = np.copy(emg_data)
    for channel in range(num_channels):
        if np.any(np.isnan(emg_data[:, channel])):
            median_value = np.nanmedian(emg_data[:, channel])
            imputed_data[:, channel] = np.nan_to_num(emg_data[:, channel], nan=median_value)
    return imputed_data

def main():
  """Main function to run preprocessing and handle missing channels."""
  logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

  data_dir = "data/raw"  # Replace with actual path to raw data
  processed_data, exclusions = preprocess_all_subjects(data_dir)
    
  # Write excluded subjects to log file
  exclusions_file = "data/processed/exclusions.log"
  with open(exclusions_file, "w") as f:
      for subject_id in exclusions:
          f.write(subject_id + "\n")

  logging.info(f"Excluded subjects: {exclusions}")

if __name__ == "__main__":
    main()