from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import hashlib

@dataclass
class CandidateList:
    candidates: List[Dict] = field(default_factory=list)

@dataclass
class ComparisonPair:
    doc1_id: str
    doc2_id: str
    similarity: float
    is_wasted: bool
    pair_id: str

@dataclass
class RedundancyCluster:
    cluster_id: str
    members: List[str]
    avg_similarity: float

@dataclass
class DataInjectionError(Exception):
    message: str

@dataclass
class DataInjectionWarning(Exception):
    message: str
