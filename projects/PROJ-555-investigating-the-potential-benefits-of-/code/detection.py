import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import f

# Import logging configuration
from logging_config import setup_logging, get_logger

# Configure logger for this module
logger = get_logger(__name__)

def logistic_growth(t, a, b, c):
    """
    Logistic growth model: f(t) = a / (1 + exp(-b * (t - c)))
    
    Parameters:
    - t: time points
    - a: asymptote (maximum value)
    - b: growth rate
    - c: inflection point (time at half maximum)
    
    Returns:
    - y: predicted values
    """
    return a / (1 + np.exp(-b * (t - c)))

def gompertz_growth(t, a, b, c):
    """
    Gompertz growth model: f(t) = a * exp(-b * exp(-c * t))
    
    Parameters:
    - t: time points
    - a: asymptote (maximum value)
    - b: displacement parameter
    - c: growth rate
    
    Returns:
    - y: predicted values
    """
    return a * np.exp(-b * np.exp(-c * t))

def calculate_r_squared(y_true, y_pred):
    """
    Calculate R-squared (coefficient of determination)
    
    Parameters:
    - y_true: actual values
    - y_pred: predicted values
    
    Returns:
    - r2: R-squared value
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)

def detect_deforestation_events(ndvi_timeseries: pd.DataFrame, 
                                threshold: float = 0.30, 
                                min_duration: int = 24) -> List[Dict[str, Any]]:
    """
    Detect deforestation events based on NDVI drop and duration.
    
    Parameters:
    - ndvi_timeseries: DataFrame with columns ['site_id', 'date', 'ndvi']
    - threshold: Minimum NDVI drop to consider as deforestation (default 0.30)
    - min_duration: Minimum duration in months for the drop to be sustained (default 24)
    
    Returns:
    - List of dictionaries containing event details
    """
    events = []
    sites = ndvi_timeseries['site_id'].unique()
    
    for site_id in sites:
        site_data = ndvi_timeseries[ndvi_timeseries['site_id'] == site_id].sort_values('date')
        ndvi_values = site_data['ndvi'].values
        dates = site_data['date'].values
        
        if len(ndvi_values) < 2:
            continue
        
        # Find local maxima as potential start of deforestation
        for i in range(1, len(ndvi_values) - 1):
            # Check if current point is a local maximum
            if ndvi_values[i] > ndvi_values[i-1] and ndvi_values[i] >= ndvi_values[i+1]:
                start_ndvi = ndvi_values[i]
                start_idx = i
                
                # Look for sustained drop
                for j in range(i + 1, len(ndvi_values)):
                    if start_ndvi - ndvi_values[j] >= threshold:
                        # Found a drop, now check duration
                        duration_months = (pd.Timestamp(dates[j]) - pd.Timestamp(dates[start_idx])).days / 30.44
                        
                        if duration_months >= min_duration:
                            # Check if it's sustained (not just a temporary dip)
                            sustained = True
                            for k in range(start_idx + 1, j + 1):
                                if start_ndvi - ndvi_values[k] < threshold * 0.8:  # Allow some fluctuation
                                    sustained = False
                                    break
                            
                            if sustained:
                                events.append({
                                    'site_id': site_id,
                                    'event_start_date': pd.Timestamp(dates[start_idx]),
                                    'event_end_date': pd.Timestamp(dates[j]),
                                    'start_ndvi': start_ndvi,
                                    'min_ndvi': ndvi_values[j],
                                    'ndvi_drop': start_ndvi - ndvi_values[j],
                                    'duration_months': duration_months
                                })
                                break  # Move to next potential event
    
    return events

def filter_sites_without_deforestation(events: List[Dict[str, Any]]) -> List[str]:
    """
    Filter sites that have clear deforestation events.
    
    Parameters:
    - events: List of deforestation events from detect_deforestation_events
    
    Returns:
    - List of site_ids with clear deforestation events
    """
    site_ids_with_events = list(set([event['site_id'] for event in events]))
    return site_ids_with_events

def fit_recovery_trajectory(ndvi_timeseries: pd.DataFrame, 
                            events: List[Dict[str, Any]], 
                            recovery_threshold: float = 0.95) -> List[Dict[str, Any]]:
    """
    Fit non-linear asymptotic models to recovery phases.
    
    Parameters:
    - ndvi_timeseries: DataFrame with columns ['site_id', 'date', 'ndvi']
    - events: List of deforestation events
    - recovery_threshold: Minimum R-squared for acceptable fit (default 0.95)
    
    Returns:
    - List of dictionaries containing trajectory parameters
    """
    trajectories = []
    
    for event in events:
        site_id = event['site_id']
        event_start = event['event_start_date']
        event_end = event['event_end_date']
        start_ndvi = event['start_ndvi']
        min_ndvi = event['min_ndvi']
        
        # Get recovery phase data (after event end)
        site_data = ndvi_timeseries[ndvi_timeseries['site_id'] == site_id].sort_values('date')
        recovery_data = site_data[site_data['date'] > event_end]
        
        if len(recovery_data) < 3:
            # Not enough data points for recovery analysis
            logger.warning(f"Insufficient recovery data for site {site_id}")
            continue
        
        # Check for incomplete recovery (recovery period < 5 years)
        if recovery_data['date'].max() - event_end < pd.Timedelta(days=5*365):
            logger.info(f"Site {site_id} has incomplete recovery period (<5 years). Flagging for exclusion from primary slope analysis.")
            trajectories.append({
                'site_id': site_id,
                'event_start_date': event_start,
                'event_end_date': event_end,
                'recovery_start_date': event_end,
                'recovery_end_date': recovery_data['date'].max(),
                'recovery_period_years': (recovery_data['date'].max() - event_end).days / 365.25,
                'status': 'incomplete_recovery',
                'excluded_from_primary_analysis': True,
                'start_ndvi': start_ndvi,
                'min_ndvi': min_ndvi
            })
            continue
        
        # Prepare data for fitting
        recovery_ndvi = recovery_data['ndvi'].values
        recovery_dates = recovery_data['date'].values
        
        # Convert dates to years relative to event end
        t = np.array([(pd.Timestamp(d) - event_end).days / 365.25 for d in recovery_dates])
        
        # Try logistic growth model first
        try:
            popt, pcov = curve_fit(
                logistic_growth, 
                t, 
                recovery_ndvi,
                p0=[start_ndvi, 0.5, t[len(t)//2]],  # Initial guesses
                maxfev=5000
            )
            y_pred = logistic_growth(t, *popt)
            r2 = calculate_r_squared(recovery_ndvi, y_pred)
            
            if r2 >= recovery_threshold:
                trajectories.append({
                    'site_id': site_id,
                    'event_start_date': event_start,
                    'event_end_date': event_end,
                    'recovery_start_date': event_end,
                    'recovery_end_date': recovery_data['date'].max(),
                    'recovery_period_years': (recovery_data['date'].max() - event_end).days / 365.25,
                    'status': 'complete_recovery',
                    'excluded_from_primary_analysis': False,
                    'model_type': 'logistic',
                    'asymptote': popt[0],
                    'growth_rate': popt[1],
                    'inflection_point': popt[2],
                    'r_squared': r2,
                    'start_ndvi': start_ndvi,
                    'min_ndvi': min_ndvi
                })
                continue
            
        except Exception as e:
            logger.warning(f"Logistic fit failed for site {site_id}: {str(e)}")
        
        # Try Gompertz model if logistic fails
        try:
            popt, pcov = curve_fit(
                gompertz_growth,
                t,
                recovery_ndvi,
                p0=[start_ndvi, 1.0, 0.5],  # Initial guesses
                maxfev=5000
            )
            y_pred = gompertz_growth(t, *popt)
            r2 = calculate_r_squared(recovery_ndvi, y_pred)
            
            if r2 >= recovery_threshold:
                trajectories.append({
                    'site_id': site_id,
                    'event_start_date': event_start,
                    'event_end_date': event_end,
                    'recovery_start_date': event_end,
                    'recovery_end_date': recovery_data['date'].max(),
                    'recovery_period_years': (recovery_data['date'].max() - event_end).days / 365.25,
                    'status': 'complete_recovery',
                    'excluded_from_primary_analysis': False,
                    'model_type': 'gompertz',
                    'asymptote': popt[0],
                    'displacement': popt[1],
                    'growth_rate': popt[2],
                    'r_squared': r2,
                    'start_ndvi': start_ndvi,
                    'min_ndvi': min_ndvi
                })
                continue
            
        except Exception as e:
            logger.warning(f"Gompertz fit failed for site {site_id}: {str(e)}")
        
        # Fallback to linear slope if both non-linear fits fail
        try:
            # Simple linear regression
            slope, intercept = np.polyfit(t, recovery_ndvi, 1)
            y_pred = slope * t + intercept
            r2 = calculate_r_squared(recovery_ndvi, y_pred)
            
            # Even if R2 < 0.95, linear slope is accepted per spec FR-002
            trajectories.append({
                'site_id': site_id,
                'event_start_date': event_start,
                'event_end_date': event_end,
                'recovery_start_date': event_end,
                'recovery_end_date': recovery_data['date'].max(),
                'recovery_period_years': (recovery_data['date'].max() - event_end).days / 365.25,
                'status': 'linear_fallback',
                'excluded_from_primary_analysis': False,
                'model_type': 'linear',
                'slope': slope,
                'intercept': intercept,
                'r_squared': r2,
                'start_ndvi': start_ndvi,
                'min_ndvi': min_ndvi
            })
            
        except Exception as e:
            logger.error(f"Linear fit failed for site {site_id}: {str(e)}")
            continue
    
    return trajectories

def generate_recovery_trajectories(ndvi_timeseries: pd.DataFrame, 
                                   events: List[Dict[str, Any]], 
                                   output_path: str) -> None:
    """
    Generate and save recovery trajectories to a Parquet file.
    
    Parameters:
    - ndvi_timeseries: DataFrame with columns ['site_id', 'date', 'ndvi']
    - events: List of deforestation events
    - output_path: Path to save the output Parquet file
    """
    trajectories = fit_recovery_trajectory(ndvi_timeseries, events)
    
    if not trajectories:
        logger.warning("No recovery trajectories generated.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(trajectories)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to Parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} recovery trajectories to {output_path}")

def main():
    """
    Main function to run the detection and trajectory analysis pipeline.
    """
    setup_logging()
    
    # Load data (paths would be configured via config.py in a full implementation)
    try:
        # Load NDVI timeseries
        ndvi_path = "data/processed/ndvi_timeseries.parquet"
        if not os.path.exists(ndvi_path):
            logger.error(f"NDVI timeseries file not found: {ndvi_path}")
            return
        
        ndvi_timeseries = pd.read_parquet(ndvi_path)
        logger.info(f"Loaded {len(ndvi_timeseries)} NDVI records from {ndvi_path}")
        
        # Detect deforestation events
        events = detect_deforestation_events(ndvi_timeseries)
        logger.info(f"Detected {len(events)} deforestation events")
        
        # Filter sites with clear events
        site_ids = filter_sites_without_deforestation(events)
        logger.info(f"Filtered to {len(site_ids)} sites with clear deforestation events")
        
        # Generate recovery trajectories
        output_path = "data/processed/recovery_trajectories.parquet"
        generate_recovery_trajectories(ndvi_timeseries, events, output_path)
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()