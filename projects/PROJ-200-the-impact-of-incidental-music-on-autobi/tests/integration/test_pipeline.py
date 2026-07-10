"""
Integration test for the full pipeline on synthetic data.

This test verifies the end-to-end flow:
1. Data Ingestion (with synthetic data generation)
2. Cue Matching
3. Aggregation to User-Track Pairs
4. Statistical Modeling
5. Sensitivity Analysis

It ensures that all components work together without errors and produce
expected output structures.
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_project_root, get_config_dict, ensure_directories
from data_ingestion import (
    filter_cohort,
    handle_fallback,
    apply_frequency_threshold,
    calculate_ratio_score,
    calculate_residualized_score
)
from cue_matching import normalize_cues, match_cues, resolve_collisions
from aggregation import (
    join_exposure_data,
    aggregate_to_user_track,
    filter_zero_variance,
    enforce_match_rate
)
from modeling import (
    fit_mixed_model,
    check_collinearity,
    extract_model_summary,
    run_sensitivity_analysis
)
from state_manager import load_state, save_state, register_file


def create_synthetic_datasets(tmp_path: Path):
    """Create synthetic MSD and AMT datasets for testing."""
    # Create raw data directory
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Synthetic MSD dataset (simplified)
    n_users = 100
    n_tracks = 50
    
    # Generate user data with birth years
    user_ids = [f"user_{i}" for i in range(n_users)]
    birth_years = np.random.randint(1980, 2000, size=n_users)
    
    # Generate track data
    track_ids = [f"track_{i}" for i in range(n_tracks)]
    track_titles = [f"Song Title {i}" for i in range(n_tracks)]
    artists = [f"Artist {i % 10}" for i in range(n_tracks)]
    popularity = np.random.uniform(0, 100, size=n_tracks)
    
    # Create listen logs (user-track interactions)
    listen_data = []
    for user_idx, user_id in enumerate(user_ids):
        # Each user listens to a subset of tracks
        user_tracks = np.random.choice(n_tracks, size=np.random.randint(5, 20), replace=False)
        for track_idx in user_tracks:
            track_id = track_ids[track_idx]
            # Simulate listen counts (some tracks more popular)
            listen_count = np.random.randint(1, 100)
            # Some listens in adolescence (birth_year + 10 to birth_year + 19)
            adolescent_listens = int(listen_count * np.random.uniform(0.1, 0.8))
            
            listen_data.append({
                'user_id': user_id,
                'track_id': track_id,
                'listen_count': listen_count,
                'adolescent_listens': adolescent_listens,
                'birth_year': birth_years[user_idx]
            })
    
    msd_df = pd.DataFrame(listen_data)
    msd_df.to_parquet(raw_dir / "msd_listen_logs.parquet")
    
    # Generate track metadata
    track_metadata = pd.DataFrame({
        'track_id': track_ids,
        'title': track_titles,
        'artist': artists,
        'overall_popularity_score': popularity
    })
    track_metadata.to_parquet(raw_dir / "msd_track_metadata.parquet")
    
    # Synthetic AMT dataset (memory cues)
    amt_data = []
    for user_idx, user_id in enumerate(user_ids):
        # Each user has some memory cues
        n_cues = np.random.randint(2, 10)
        for _ in range(n_cues):
            # Randomly select a track the user listened to
            listened_tracks = listen_data[
                [d['user_id'] == user_id for d in listen_data]
            ]
            if len(listened_tracks) > 0:
                chosen_track = np.random.choice(listened_tracks)
                track_idx = track_ids.index(chosen_track['track_id'])
                
                # Create cue text (sometimes exact match, sometimes fuzzy)
                original_title = track_titles[track_idx]
                if np.random.random() > 0.3:
                    cue_text = original_title  # Exact match
                else:
                    # Introduce some noise for fuzzy matching
                    cue_text = original_title + " " + str(np.random.randint(1000))
                    cue_text = cue_text.lower()
                
                amt_data.append({
                    'user_id': user_id,
                    'cue_text': cue_text,
                    'vividness': np.random.uniform(1, 5),
                    'valence': np.random.uniform(1, 5),
                    'match_status': 'pending'
                })
    
    amt_df = pd.DataFrame(amt_data)
    amt_df.to_parquet(raw_dir / "amt_memory_cues.parquet")
    
    return raw_dir


def test_full_pipeline_synthetic_data():
    """Test the full pipeline with synthetic data."""
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Override project root for this test
        original_get_project_root = get_project_root
        
        def mock_get_project_root():
            return tmp_path
        
        # Patch the function
        import config
        config.get_project_root = mock_get_project_root
        
        try:
            # Setup directories
            ensure_directories()
            
            # Create synthetic data
            raw_dir = create_synthetic_datasets(tmp_path)
            
            # Step 1: Data Ingestion
            print("Running data ingestion...")
            
            # Load raw data
            msd_logs = pd.read_parquet(raw_dir / "msd_listen_logs.parquet")
            track_metadata = pd.read_parquet(raw_dir / "msd_track_metadata.parquet")
            
            # Filter cohort (birth year filtering)
            filtered_logs = filter_cohort(msd_logs)
            assert len(filtered_logs) > 0, "No records after birth year filtering"
            
            # Handle fallback if needed
            if handle_fallback(filtered_logs, track_metadata):
                print("Fallback triggered")
            
            # Apply frequency threshold
            filtered_logs = apply_frequency_threshold(filtered_logs, min_listens=5)
            
            # Calculate exposure scores
            msd_with_exposure = calculate_ratio_score(filtered_logs)
            msd_with_exposure = calculate_residualized_score(
                msd_with_exposure, 
                track_metadata,
                'overall_popularity_score'
            )
            
            # Save processed data
            processed_dir = tmp_path / "data" / "processed"
            processed_dir.mkdir(parents=True, exist_ok=True)
            msd_with_exposure.to_parquet(processed_dir / "ingested_cohort.parquet")
            
            # Step 2: Cue Matching
            print("Running cue matching...")
            amt_cues = pd.read_parquet(raw_dir / "amt_memory_cues.parquet")
            
            # Normalize cues
            normalized_cues = normalize_cues(amt_cues)
            
            # Build index from track metadata
            track_titles = track_metadata['title'].tolist()
            track_ids = track_metadata['track_id'].tolist()
            
            # Match cues
            matched_cues = match_cues(
                normalized_cues,
                track_titles,
                track_ids,
                max_distance=4
            )
            
            # Resolve collisions
            final_matches = resolve_collisions(matched_cues)
            
            # Save matched cues
            final_matches.to_parquet(processed_dir / "matched_cues.parquet")
            
            # Step 3: Aggregation
            print("Running aggregation...")
            
            # Join exposure data
            joined_data = join_exposure_data(
                final_matches,
                msd_with_exposure
            )
            
            # Aggregate to user-track pairs
            user_track_pairs = aggregate_to_user_track(joined_data)
            
            # Filter zero variance
            user_track_pairs = filter_zero_variance(user_track_pairs)
            
            # Enforce match rate
            match_rate = enforce_match_rate(amt_cues, final_matches)
            print(f"Match rate: {match_rate:.2%}")
            
            # Save user-track pairs
            user_track_pairs.to_parquet(processed_dir / "user_track_pairs.parquet")
            
            # Step 4: Statistical Modeling
            print("Running statistical modeling...")
            
            # Check collinearity
            vif_results = check_collinearity(user_track_pairs)
            assert 'vif' in vif_results, "VIF calculation failed"
            
            # Fit mixed model
            model_results = fit_mixed_model(
                user_track_pairs,
                'mean_vividness',
                'residualized_exposure_score',
                'overall_popularity_score',
                'user_id'
            )
            
            # Extract summary
            summary = extract_model_summary(model_results)
            
            # Save regression results
            final_dir = tmp_path / "data" / "final"
            final_dir.mkdir(parents=True, exist_ok=True)
            summary.to_csv(final_dir / "regression_summary.csv")
            
            # Step 5: Sensitivity Analysis
            print("Running sensitivity analysis...")
            
            sensitivity_results = run_sensitivity_analysis(
                user_track_pairs,
                thresholds=[2, 4, 6],
                threshold_column='levenshtein_distance'
            )
            
            # Verify sensitivity results
            assert len(sensitivity_results) > 0, "Sensitivity analysis produced no results"
            assert 'threshold' in sensitivity_results.columns, "Missing threshold column"
            
            sensitivity_results.to_csv(final_dir / "sensitivity_analysis.csv")
            
            # Verify outputs exist
            assert (final_dir / "regression_summary.csv").exists()
            assert (final_dir / "sensitivity_analysis.csv").exists()
            assert (processed_dir / "user_track_pairs.parquet").exists()
            
            print("All pipeline steps completed successfully!")
            
        finally:
            # Restore original function
            config.get_project_root = original_get_project_root


def test_sensitivity_analysis_integration():
    """Test sensitivity analysis with different Levenshtein thresholds."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Setup
        original_get_project_root = get_project_root
        def mock_get_project_root():
            return tmp_path
        
        import config
        config.get_project_root = mock_get_project_root
        
        try:
            ensure_directories()
            raw_dir = create_synthetic_datasets(tmp_path)
            
            # Load data
            msd_logs = pd.read_parquet(raw_dir / "msd_listen_logs.parquet")
            track_metadata = pd.read_parquet(raw_dir / "msd_track_metadata.parquet")
            amt_cues = pd.read_parquet(raw_dir / "amt_memory_cues.parquet")
            
            # Process
            filtered_logs = filter_cohort(msd_logs)
            msd_with_exposure = calculate_ratio_score(filtered_logs)
            msd_with_exposure = calculate_residualized_score(
                msd_with_exposure,
                track_metadata,
                'overall_popularity_score'
            )
            
            normalized_cues = normalize_cues(amt_cues)
            matched_cues = match_cues(
                normalized_cues,
                track_metadata['title'].tolist(),
                track_metadata['track_id'].tolist(),
                max_distance=6
            )
            
            final_matches = resolve_collisions(matched_cues)
            joined_data = join_exposure_data(final_matches, msd_with_exposure)
            user_track_pairs = aggregate_to_user_track(joined_data)
            
            # Run sensitivity analysis
            sensitivity_results = run_sensitivity_analysis(
                user_track_pairs,
                thresholds=[2, 4, 6],
                threshold_column='levenshtein_distance'
            )
            
            # Verify results structure
            assert 'threshold' in sensitivity_results.columns
            assert 'mean_vividness' in sensitivity_results.columns
            assert 'residualized_exposure_score' in sensitivity_results.columns
            
            # Verify we have results for each threshold
            thresholds_found = sorted(sensitivity_results['threshold'].unique())
            expected_thresholds = [2, 4, 6]
            assert thresholds_found == expected_thresholds, f"Expected {expected_thresholds}, got {thresholds_found}"
            
            print("Sensitivity analysis integration test passed!")
            
        finally:
            config.get_project_root = original_get_project_root


if __name__ == "__main__":
    test_full_pipeline_synthetic_data()
    test_sensitivity_analysis_integration()
    print("All integration tests passed!")
