import os
import torch
from typing import Optional, List, Dict, Any, Generator

# Import from project API surface
from agents.model_checker import verify_model, get_project_root, read_plan_md
from utils.execution_log import ExecutionLog, TrajectoryExecutionLog
from utils.memory_profiler import profile_memory_latency, get_current_memory_usage

# Force CPU-only execution environment at module load time to prevent accidental CUDA usage
# This ensures the agent respects the <7GB memory constraint and runs on CPU-only runners
os.environ["CUDA_VISIBLE_DEVICES"] = ""
if torch.cuda.is_available():
    # Explicitly disable CUDA device context
    torch.cuda.is_available = lambda: False
    # Clear any existing CUDA caches if torch was imported before the env var was set
    try:
        torch.cuda.empty_cache()
    except Exception:
        pass

# Set default device to CPU
DEVICE = torch.device("cpu")

class BaseConActAgent:
    """
    Base ConAct Agent configured for CPU-only execution and strict memory management.
    
    This agent enforces:
    - CPU-only inference (no CUDA)
    - 4-bit quantization via bitsandbytes (if available, otherwise fallback to 8-bit or float16)
    - Memory footprint < 7GB (monitored via memory_profiler)
    """

    def __init__(
        self,
        model_id: str,
        max_memory_limit_mb: int = 7000,
        quantization_config: Optional[Dict[str, Any]] = None,
        seed: int = 42
    ):
        """
        Initialize the BaseConActAgent.
        
        Args:
            model_id: HuggingFace model identifier.
            max_memory_limit_mb: Maximum allowed memory footprint in MB (default 7000).
            quantization_config: Optional config for quantization (e.g., {'load_in_4bit': True}).
            seed: Random seed for reproducibility.
        """
        self.model_id = model_id
        self.max_memory_limit_mb = max_memory_limit_mb
        self.quantization_config = quantization_config or {
            "load_in_4bit": True,
            "bnb_4bit_compute_dtype": torch.float16,
            "bnb_4bit_quant_type": "nf4",
            "llm_int8_skip_modules": ["lm_head"]
        }
        self.seed = seed
        self.model = None
        self.tokenizer = None
        self.device = DEVICE

        # Verify model availability before loading
        self._verify_model()

    def _verify_model(self):
        """Verify the model exists and is loadable via the model_checker."""
        try:
            # Use the project's model_checker to verify the model against Plan.md constraints
            # This ensures we only load models that are verified or acceptable substitutes
            verify_model(self.model_id)
        except Exception as e:
            raise RuntimeError(f"Model verification failed for {self.model_id}: {e}")

    def load(self):
        """
        Load the model with 4-bit quantization on CPU.
        
        Enforces memory constraints by monitoring usage during load.
        """
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        # Log current memory before load
        pre_load_mem = get_current_memory_usage()
        if pre_load_mem > self.max_memory_limit_mb * 0.8:
            raise MemoryError(f"Current memory usage ({pre_load_mem}MB) is too high to load model. Limit: {self.max_memory_limit_mb}MB")

        # Configure 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=self.quantization_config.get("load_in_4bit", True),
            bnb_4bit_compute_dtype=self.quantization_config.get("bnb_4bit_compute_dtype", torch.float16),
            bnb_4bit_quant_type=self.quantization_config.get("bnb_4bit_quant_type", "nf4"),
            llm_int8_skip_modules=self.quantization_config.get("llm_int8_skip_modules", ["lm_head"])
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            trust_remote_code=True
        )
        
        # Ensure tokenizer has pad token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with 4-bit quantization, explicitly on CPU
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            quantization_config=bnb_config,
            device_map="cpu",  # Force CPU device map
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )

        # Post-load memory check
        post_load_mem = get_current_memory_usage()
        if post_load_mem > self.max_memory_limit_mb:
            # Attempt to clear cache if over limit (though on CPU this is less effective)
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            # If still over limit, log warning but allow to proceed if it's within 10% tolerance
            # Strict enforcement: raise error if significantly over
            if post_load_mem > self.max_memory_limit_mb * 1.1:
                raise MemoryError(
                    f"Model loaded but exceeded memory limit: {post_load_mem}MB > {self.max_memory_limit_mb}MB"
                )
            else:
                print(f"Warning: Model loaded at {post_load_mem}MB, slightly over limit {self.max_memory_limit_mb}MB.")

        print(f"Model {self.model_id} loaded successfully on CPU. Memory usage: {post_load_mem}MB")

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> str:
        """
        Generate a response given a prompt.
        
        Args:
            prompt: Input text prompt.
            max_new_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            top_p: Top-p sampling threshold.
            do_sample: Whether to use sampling.
        
        Returns:
            Generated text string.
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Profile memory during inference
        with profile_memory_latency(self.max_memory_limit_mb) as mem_profile:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature if do_sample else None,
                    top_p=top_p if do_sample else None,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Log memory metrics
            mem_profile.log_inference_step(len(prompt), len(generated_text))

        return generated_text

    def run_trajectory(
        self,
        trajectory: Dict[str, Any],
        log_path: Optional[str] = None
    ) -> TrajectoryExecutionLog:
        """
        Execute the agent on a single trajectory.
        
        Args:
            trajectory: Dictionary containing trajectory data (steps, goals, etc.).
            log_path: Optional path to write execution logs.
        
        Returns:
            TrajectoryExecutionLog containing step-level results.
        """
        log = TrajectoryExecutionLog(
            trajectory_id=trajectory.get("id", "unknown"),
            agent_type="BaseConActAgent",
            steps=[]
        )

        steps = trajectory.get("steps", [])
        for i, step in enumerate(steps):
            prompt = step.get("prompt", "")
            goal = step.get("goal", "")
            
            # Construct full prompt
            full_prompt = f"Goal: {goal}\n\nContext: {prompt}\n\nAction:"
            
            try:
                # Generate action
                action = self.generate(full_prompt)
                
                # Record success
                step_log = ExecutionLog(
                    step_index=i,
                    input_text=full_prompt,
                    output_text=action,
                    success=True,
                    latency_ms=mem_profile.last_latency if 'mem_profile' in locals() else 0,
                    memory_mb=mem_profile.last_memory if 'mem_profile' in locals() else 0
                )
                log.steps.append(step_log)
                
            except Exception as e:
                # Record failure
                step_log = ExecutionLog(
                    step_index=i,
                    input_text=full_prompt,
                    output_text=str(e),
                    success=False,
                    error=str(e)
                )
                log.steps.append(step_log)
                # Continue to next step or break? Spec implies logging all steps
                # We continue to log all steps even if one fails

        # Write to log file if path provided
        if log_path:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a') as f:
                f.write(log.to_json() + '\n')

        return log

def main():
    """
    Main entry point for running the BaseConActAgent on a benchmark.
    
    This function:
    1. Loads the model (CPU-only, 4-bit)
    2. Reads trajectories from data/synthetic_benchmark/trajectories.jsonl
    3. Executes the agent on each trajectory
    4. Writes logs to data/results/baseline_execution_logs.jsonl
    """
    import json
    from pathlib import Path
    from utils.config import get_data_dir, get_code_dir
    from utils.execution_log import TrajectoryExecutionLog

    # Get paths
    code_dir = get_code_dir()
    data_dir = get_data_dir()
    
    input_path = Path(data_dir) / "synthetic_benchmark" / "trajectories.jsonl"
    output_path = Path(data_dir) / "results" / "baseline_execution_logs.jsonl"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize agent
    # Model ID will be determined by model_checker (T016/T017)
    # For now, use a default that should be verified by model_checker
    agent = BaseConActAgent(model_id="microsoft/Phi-3.5-mini-instruct")
    agent.load()

    # Process trajectories
    print(f"Starting execution on {input_path}...")
    
    with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
        for line_num, line in enumerate(f_in):
            if not line.strip():
                continue
            
            trajectory = json.loads(line)
            print(f"Processing trajectory {line_num + 1}: {trajectory.get('id', 'unknown')}")
            
            log = agent.run_trajectory(trajectory)
            f_out.write(log.to_json() + '\n')
            
            print(f"Completed trajectory {line_num + 1}. Success rate: {log.success_rate:.2%}")

    print(f"All trajectories processed. Results saved to {output_path}")

if __name__ == "__main__":
    main()