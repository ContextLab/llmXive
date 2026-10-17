import json
from pathlib import Path
from typing import Any, Dict
from data_models import SimulationRun

def save_single_run_results(result_dict: Dict[str, Any], output_path: str):
    # Validate using the Pydantic model
    run = SimulationRun(**result_dict)
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(run.model_dump_json(indent=2))
