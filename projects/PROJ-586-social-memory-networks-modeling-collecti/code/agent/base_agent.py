import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from dataclasses import dataclass

@dataclass
class AgentConfig:
    model_name: str = "opt-125m"
    agent_id: int = 0
    device: str = "cpu"
    max_tokens: int = 512
    temperature: float = 0.7

class BaseAgent:
    """
    Base agent abstraction using CPU-only transformers.
    Implements the core agent interface for multi-agent simulations.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = config.agent_id
        self.device = config.device
        
        # Initialize model and tokenizer
        # Using small model for CPU compatibility
        self.tokenizer = AutoTokenizer.from_pretrained(config.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            config.model_name,
            torch_dtype=torch.float32,
            device_map="cpu"
        )
        
        self.memory_history: List[Dict[str, Any]] = []
    
    def generate_response(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate a response to the given prompt."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        if max_tokens is None:
            max_tokens = self.config.max_tokens
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=self.config.temperature,
                do_sample=True
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
    
    def add_to_memory(self, entry: Dict[str, Any]):
        """Add an entry to the agent's memory history."""
        self.memory_history.append(entry)
    
    def get_memory_context(self, limit: int = 10) -> str:
        """Get the recent memory context as a string."""
        recent = self.memory_history[-limit:]
        context = "\n".join([f"{k}: {v}" for item in recent for k, v in item.items()])
        return context
    
    def reset_memory(self):
        """Clear the agent's memory history."""
        self.memory_history.clear()
    
    def process_memory_action(self, action_type: str, content: str):
        """Process a memory action (store, retrieve, forget)."""
        if action_type == "store":
            self.add_to_memory({"type": "store", "content": content, "agent_id": self.agent_id})
            return f"<MEMORY_ACTION type=\"store\" content=\"{content}\">"
        elif action_type == "retrieve":
            context = self.get_memory_context()
            return f"<MEMORY_ACTION type=\"retrieve\" content=\"{content}\"> Retrieved: {context}"
        elif action_type == "forget":
            # Remove matching entries
            self.memory_history = [
                e for e in self.memory_history 
                if content not in str(e)
            ]
            return f"<MEMORY_ACTION type=\"forget\" content=\"{content}\">"
        else:
            return f"<MEMORY_ACTION type=\"unknown\" content=\"{content}\">"
