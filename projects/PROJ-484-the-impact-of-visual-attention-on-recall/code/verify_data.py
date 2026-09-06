import os
import sys
import json
import logging
import argparse
from pathlib import Path

def load_json_file(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def load_yaml_file(filepath):
    with open(filepath, 'r') as f:
        import yaml
        return yaml.safe_load(f)

def find_bids_sidecars(directory):
    sidecars = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.json', '.yaml')):
                sidecars.append(os.path.join(root, file))
    return sidecars

def extract_columns_from_sidecar(filepath):
    data = load_json_file(filepath)
    return data

def extract_geometry_metadata(sidecar_data):
    try:
        screen_width_px = sidecar_data.get("screen_width_px")
        viewing_distance_mm = sidecar_data.get("viewing_distance_mm")
        sampling_rate_hz = sidecar_data.get("sampling_rate_hz")
        return screen_width_px, viewing_distance_mm, sampling_rate_hz
    except:
        return None, None, None

def calculate_ivt_threshold(screen_width_px, viewing_distance_mm, sampling_rate_hz, deg=0.5):
    if screen_width_px is None or viewing_distance_mm is None or sampling_rate_hz is None:
        return None
    pixels_per_degree = screen_width_px / (viewing_distance_mm / 10)
    threshold_pixels_per_frame = (deg / 1) * pixels_per_degree / sampling_rate_hz
    return threshold_pixels_per_frame

def verify_temporal_load(events_data, stimulus_duration_ms):
    if events_data is None:
        return False
    for event in events_data:
        if event.get("duration") != stimulus_duration_ms:
            return False
    return True

def main():
    parser = argparse.ArgumentParser(description='Verify data metadata and calibration.')
    parser.add_argument('--config', type=str, default='config.json', help='Path to the configuration file.')
    parser.add_argument('--hypothetical', action='store_true', help='Enable hypothetical mode with default values.')
    args = parser.parse_args()

    config = load_json_file(args.config)

    bids_directory = config.get('bids_directory')
    
    if bids_directory is None:
      print("ERROR: bids_directory not found in config.")
      sys.exit(1)

    sidecars = find_bids_sidecars(bids_directory)
    if not sidecars:
        print("ERROR: No BIDS sidecar files found in directory.")
        sys.exit(1)

    sidecar_data = extract_columns_from_sidecar(sidecars[0])

    screen_width_px, viewing_distance_mm, sampling_rate_hz = extract_geometry_metadata(sidecar_data)
    
    # T071b: Implement "Hypothetical Geometry Fallback"
    # If verified_sources_hypothetical.json marks dataset as hypothetical, 
    # load defaults from config.yaml even if BIDS metadata is missing
    hypothetical_mode = args.hypothetical or config.get('hypothetical_mode', False)
    
    if screen_width_px is None or viewing_distance_mm is None or sampling_rate_hz is None:
        if hypothetical_mode:
            print("WARNING: Missing geometry metadata. Using hypothetical defaults from config.")
            screen_width_px = config.get('default_screen_width_px')
            viewing_distance_mm = config.get('default_viewing_distance_mm')
            sampling_rate_hz = config.get('default_sampling_rate_hz')
            
            if screen_width_px is None or viewing_distance_mm is None or sampling_rate_hz is None:
                print("ERROR: Hypothetical mode enabled but default values missing from config.")
                sys.exit(1)
        else:
            print("ERROR: Cannot calibrate I-VT threshold without screen geometry.")
            sys.exit(1)
    
    ivt_threshold = calculate_ivt_threshold(screen_width_px, viewing_distance_mm, sampling_rate_hz)
    if ivt_threshold is None:
      print("ERROR: Could not calculate I-VT threshold")
      sys.exit(1)

    print(f"I-VT Threshold: {ivt_threshold}")

    events_data = sidecar_data.get("events")
    stimulus_duration_ms = config.get("stimulus_duration_ms")
    
    if not verify_temporal_load(events_data, stimulus_duration_ms):
        print("ERROR: Temporal load verification failed.")
        sys.exit(1)

    print("Data verification successful!")

if __name__ == "__main__":
    main()