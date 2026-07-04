"""Base agent abstraction using CPU-only transformers."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_id: int
    model_name: str = "gpt2"
    max_tokens: int = 100
    temperature: float = 0.7
    seed: int = 42


class BaseAgent:
    """Base agent that uses simple heuristic reasoning instead of transformers."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.memory: List[str] = []
        self.knowledge_domains: Dict[str, float] = {}
        random.seed(config.seed + config.agent_id)
    
    def initialize_knowledge(self, domains: List[str]) -> None:
        """Initialize agent's knowledge in specific domains."""
        for domain in domains:
            self.knowledge_domains[domain] = random.random()
    
    def query(self, question: str, context: str = "") -> str:
        """Generate a response to a question using heuristic reasoning."""
        # Simple heuristic: return a response based on knowledge domains
        response = f"Agent {self.config.agent_id}: "
        
        # Find the domain with highest knowledge
        if self.knowledge_domains:
            best_domain = max(self.knowledge_domains, key=self.knowledge_domains.get)
            confidence = self.knowledge_domains[best_domain]
            response += f"Based on {best_domain} expertise (confidence: {confidence:.2f}), "
        
        response += question
        return response
    
    def add_to_memory(self, item: str) -> None:
        """Add an item to the agent's memory."""
        self.memory.append(item)
    
    def recall(self, query: str) -> List[str]:
        """Recall items from memory matching the query."""
        return [m for m in self.memory if query.lower() in m.lower()]
    
    def get_specialization_score(self) -> float:
        """Compute how specialized this agent is (0=generalist, 1=specialist)."""
        if not self.knowledge_domains:
            return 0.0
        values = list(self.knowledge_domains.values())
        if len(values) <= 1:
            return 0.0
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        # Higher variance = more specialized
        return min(variance, 1.0)