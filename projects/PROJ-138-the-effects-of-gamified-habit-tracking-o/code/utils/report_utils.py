import os
import json
import logging
from code.utils.logging import pipeline_logger

def report_cronbach_alpha(alpha_value: float):
    """
    Write Cronbach's Alpha value to psychometrics.json.
    
    Args:
        alpha_value: The calculated Cronbach's Alpha
    """
    output_path = "data/processed/psychometrics.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    data = {
        "cronbach_alpha": alpha_value,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    pipeline_logger.info(f"Written Cronbach's Alpha ({alpha_value:.4f}) to {output_path}")

def format_limitations(sample_size: int, synthetic: bool = True, underpowered: bool = False) -> str:
    """
    Format the limitations section for the report.
    
    Args:
        sample_size: Actual sample size N
        synthetic: Whether data is synthetic
        underpowered: Whether power analysis indicated low power
        
    Returns:
        Formatted limitations text
    """
    limitations = []
    
    limitations.append(f"**Sample Size**: N={sample_size}.")
    
    if synthetic:
        limitations.append("**Synthetic Nature**: Data is synthetically generated with known ground truth, limiting external validity.")
    
    if underpowered:
        limitations.append("**Power**: Study may be underpowered for detecting interaction effects.")
    
    limitations.append("**External Validation**: No external validation performed.")
    
    return " ".join(limitations)

if __name__ == "__main__":
  # Test
  report_cronbach_alpha(0.85)
  print(format_limitations(500))
