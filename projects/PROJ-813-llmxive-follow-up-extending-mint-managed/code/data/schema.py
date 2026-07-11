import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator

# Schema Definitions for Data Validation

class AdapterSchema(BaseModel):
    adapter_id: str
    rank: int
    base_model: str
    weights: Union[List[float], str] # Can be list or serialized string
    
    @field_validator('weights')
    @classmethod
    def validate_weights(cls, v):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if not isinstance(parsed, list):
                    raise ValueError("Weights string must be a JSON list")
                return parsed
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string for weights")
        elif isinstance(v, list):
            return v
        else:
            raise ValueError("Weights must be a list or JSON string")
    
    class Config:
        json_schema_extra = {
            "example": {
                "adapter_id": "adapter_001",
                "rank": 64,
                "base_model": "llama-2-7b",
                "weights": [0.1, 0.2, 0.3]
            }
        }

class TraceRequestSchema(BaseModel):
    request_id: str
    adapter_id: str
    timestamp: float
    priority: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_001",
                "adapter_id": "adapter_001",
                "timestamp": 1678886400.0,
                "priority": 1
            }
        }

class OverlapMatrixSchema(BaseModel):
    # The schema is implicitly defined by the CSV structure:
    # Rows/Cols are adapter IDs, values are floats in [0, 1]
    pass

class TopologyGraphSchema(BaseModel):
    # The schema is implicitly defined by the JSON structure (node_link_data format)
    # {
    #   "directed": false,
    #   "multigraph": false,
    #   "graph": {},
    #   "nodes": [{"id": "adapter_001", ...}, ...],
    #   "links": [{"source": "adapter_001", "target": "adapter_002", "weight": 0.8}, ...]
    # }
    pass

def validate_adapter_dataframe(df: pd.DataFrame) -> bool:
    required_columns = {'adapter_id', 'rank', 'base_model', 'weights'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_columns - set(df.columns)}")
    return True

def validate_trace_dataframe(df: pd.DataFrame) -> bool:
    required_columns = {'request_id', 'adapter_id', 'timestamp'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_columns - set(df.columns)}")
    return True

def validate_overlap_matrix_file(file_path: Path) -> bool:
    if not file_path.exists():
        raise FileNotFoundError(f"Overlap matrix file not found: {file_path}")
    
    df = pd.read_csv(file_path, index_col=0)
    # Check if it's square
    if df.shape[0] != df.shape[1]:
        raise ValueError("Overlap matrix must be square")
    
    # Check values are numeric
    if not np.issubdtype(df.values.dtype, np.number):
        raise ValueError("Overlap matrix values must be numeric")
    
    return True

def validate_topology_graph_file(file_path: Path) -> bool:
    if not file_path.exists():
        raise FileNotFoundError(f"Topology graph file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if 'nodes' not in data or 'links' not in data:
        raise ValueError("Invalid topology graph format: missing 'nodes' or 'links'")
    
    return True
