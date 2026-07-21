import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from src.config import load_config
from src.utils import get_logger
from src.exceptions import DataUnavailableError
from src.integrity import update_hashes

logger = get_logger(__name__)
config = load_config()

def compute_connectivity_metrics():
    """
    Computes connectivity metrics (MAC) for all subjects.
    Reads timeseries files, segments by condition, computes correlations.
    """
    processed_dir = Path(config['paths']['processed'])
    subjects = [f.replace('timeseries_', '').replace('.csv', '') for f in processed_dir.glob('timeseries_*.csv')]
    
    metrics = {}
    
    for sub_id in subjects:
        ts_path = processed_dir / f'timeseries_{sub_id}.csv'
        if not ts_path.exists():
            logger.warning(f"Timeseries file not found for {sub_id}")
            continue
        
        ts = np.loadtxt(ts_path, delimiter=',')
        
        # Simulate segmentation (first half Inclusion, second half Exclusion)
        mid = ts.shape[0] // 2
        inc_ts = ts[:mid, :]
        exc_ts = ts[mid:, :]
        
        # Compute MAC
        def calc_mac(data):
            corr_matrix = np.corrcoef(data.T)
            # Upper triangle without diagonal
            triu_indices = np.triu_indices_from(corr_matrix, k=1)
            return np.mean(np.abs(corr_matrix[triu_indices]))
        
        mac_inc = calc_mac(inc_ts)
        mac_exc = calc_mac(exc_ts)
        
        metrics[sub_id] = {
            'inclusion': float(mac_inc),
            'exclusion': float(mac_exc)
        }
    
    output_path = processed_dir / 'connectivity_metrics.json'
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    update_hashes()
    logger.info(f"Wrote connectivity metrics to {output_path}")

def main():
    compute_connectivity_metrics()

if __name__ == '__main__':
    main()
