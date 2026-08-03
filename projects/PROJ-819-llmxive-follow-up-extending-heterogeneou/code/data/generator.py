import json
import os
import random
import hashlib
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid

# Domain definitions for synthetic query generation
DOMAINS = [
    "physics",
    "biology",
    "chemistry",
    "computer_science",
    "mathematics",
    "astronomy",
    "ecology",
    "neuroscience"
]

# Templates for generating diverse scientific queries
QUERY_TEMPLATES = [
    "Explain the mechanism of {phenomenon} in the context of {domain}.",
    "What are the implications of {theory} for {application}?",
    "Derive the relationship between {variable_a} and {variable_b} in {domain}.",
    "Analyze the role of {component} in {process} within {domain}.",
    "How does {factor} influence {outcome} in a {domain} system?",
    "Compare and contrast {concept_a} and {concept_b} in {domain}.",
    "Evaluate the effectiveness of {method} for solving {problem} in {domain}.",
    "What is the current understanding of {topic} in {domain} research?",
    "Describe the experimental setup to measure {parameter} in {domain}.",
    "How would you model the interaction between {entity_a} and {entity_b} in {domain}?"
]

# Scientific concepts mapped to domains for realistic query generation
DOMAIN_CONCEPTS = {
    "physics": {
        "phenomenon": ["quantum entanglement", "superconductivity", "wave-particle duality", "time dilation", "black hole evaporation"],
        "theory": ["string theory", "general relativity", "quantum chromodynamics", "standard model"],
        "application": ["quantum computing", "nuclear fusion", "particle accelerators", "gravitational wave detection"],
        "variable_a": ["momentum", "energy", "angular velocity", "magnetic flux"],
        "variable_b": ["force", "power", "torque", "inductance"],
        "component": ["boson", "fermion", "quark", "photon"],
        "process": ["decay", "scattering", "fusion", "fission"],
        "factor": ["temperature", "pressure", "magnetic field strength", "luminosity"],
        "outcome": ["phase transition", "energy release", "particle creation", "radiation emission"],
        "concept_a": ["classical mechanics", "quantum mechanics"],
        "concept_b": ["determinism", "probabilistic behavior"],
        "method": ["Monte Carlo simulation", "perturbation theory", "lattice QCD"],
        "problem": ["many-body problem", "turbulence", "chaos"],
        "topic": ["dark matter", "dark energy", "supersymmetry"],
        "parameter": ["cross-section", "decay rate", "spin polarization"],
        "entity_a": ["electron", "proton"],
        "entity_b": ["neutron", "positron"]
    },
    "biology": {
        "phenomenon": ["protein folding", "gene expression", "cell division", "apoptosis"],
        "theory": ["central dogma", "evolutionary theory", "endosymbiotic theory"],
        "application": ["gene therapy", "synthetic biology", "personalized medicine"],
        "variable_a": ["enzyme concentration", "substrate affinity", "mutation rate"],
        "variable_b": ["reaction velocity", "growth rate", "fitness"],
        "component": ["ribosome", "mitochondrion", "nucleus", "lysosome"],
        "process": ["transcription", "translation", "replication", "metabolism"],
        "factor": ["temperature", "pH", "nutrient availability", "oxygen levels"],
        "outcome": ["cell differentiation", "population growth", "speciation"],
        "concept_a": ["genotype", "phenotype"],
        "concept_b": ["natural selection", "genetic drift"],
        "method": ["CRISPR-Cas9", "RNA-seq", "mass spectrometry"],
        "problem": ["protein misfolding", "antibiotic resistance", "cancer metastasis"],
        "topic": ["epigenetics", "microbiome", "neuroplasticity"],
        "parameter": ["binding affinity", "expression level", "mutation frequency"],
        "entity_a": ["bacteria", "virus"],
        "entity_b": ["host cell", "immune cell"]
    },
    "chemistry": {
        "phenomenon": ["catalysis", "electrochemical reaction", "polymerization"],
        "theory": ["molecular orbital theory", "acid-base theory", "kinetic theory"],
        "application": ["drug design", "material synthesis", "battery technology"],
        "variable_a": ["concentration", "temperature", "pressure"],
        "variable_b": ["reaction rate", "equilibrium constant", "yield"],
        "component": ["catalyst", "solvent", "ligand", "substrate"],
        "process": ["oxidation", "reduction", "hydrolysis", "condensation"],
        "factor": ["catalyst surface area", "solvent polarity", "ionic strength"],
        "outcome": ["product formation", "precipitation", "color change"],
        "concept_a": ["thermodynamics", "kinetics"],
        "concept_b": ["reversibility", "irreversibility"],
        "method": ["NMR spectroscopy", "X-ray crystallography", "chromatography"],
        "problem": ["selectivity", "stability", "toxicity"],
        "topic": ["nanomaterials", "green chemistry", "supramolecular chemistry"],
        "parameter": ["activation energy", "rate constant", "pKa"],
        "entity_a": ["molecule", "ion"],
        "entity_b": ["radical", "complex"]
    },
    "computer_science": {
        "phenomenon": ["concurrency", "distributed consensus", "neural network training"],
        "theory": ["computational complexity", "information theory", "automata theory"],
        "application": ["cloud computing", "machine learning", "cybersecurity"],
        "variable_a": ["input size", "memory usage", "latency"],
        "variable_b": ["execution time", "throughput", "error rate"],
        "component": ["processor", "memory", "network interface", "cache"],
        "process": ["compilation", "optimization", "synchronization"],
        "factor": ["clock speed", "bandwidth", "cache size"],
        "outcome": ["scalability", "fault tolerance", "performance"],
        "concept_a": ["sequential", "parallel"],
        "concept_b": ["deterministic", "non-deterministic"],
        "method": ["dynamic programming", "greedy algorithm", "randomized algorithm"],
        "problem": ["NP-completeness", "deadlock", "race condition"],
        "topic": ["quantum computing", "blockchain", "federated learning"],
        "parameter": ["time complexity", "space complexity", "accuracy"],
        "entity_a": ["node", "process"],
        "entity_b": ["thread", "service"]
    },
    "mathematics": {
        "phenomenon": ["convergence", "symmetry breaking", "topological phase transition"],
        "theory": ["category theory", "set theory", "number theory"],
        "application": ["cryptography", "data analysis", "optimization"],
        "variable_a": ["dimension", "rank", "eigenvalue"],
        "variable_b": ["determinant", "trace", "norm"],
        "component": ["manifold", "group", "field", "ring"],
        "process": ["differentiation", "integration", "transformation"],
        "factor": ["boundary conditions", "initial values", "constraints"],
        "outcome": ["stability", "uniqueness", "existence"],
        "concept_a": ["discrete", "continuous"],
        "concept_b": ["finite", "infinite"],
        "method": ["proof by contradiction", "induction", "constructive proof"],
        "problem": ["Riemann hypothesis", "P vs NP", "Navier-Stokes existence"],
        "topic": ["algebraic geometry", "differential topology", "stochastic processes"],
        "parameter": ["convergence rate", "condition number", "spectral gap"],
        "entity_a": ["vector", "matrix"],
        "entity_b": ["tensor", "operator"]
    },
    "astronomy": {
        "phenomenon": ["stellar nucleosynthesis", "galaxy formation", "cosmic inflation"],
        "theory": ["big bang theory", "dark matter hypothesis", "modified gravity"],
        "application": ["exoplanet detection", "cosmological modeling", "space exploration"],
        "variable_a": ["redshift", "luminosity", "mass"],
        "variable_b": ["distance", "velocity", "age"],
        "component": ["star", "planet", "black hole", "nebula"],
        "process": ["accretion", "supernova", "merger"],
        "factor": ["metallicity", "angular momentum", "magnetic field"],
        "outcome": ["star formation", "planetary system", "gamma-ray burst"],
        "concept_a": ["local universe", "observable universe"],
        "concept_b": ["homogeneous", "anisotropic"],
        "method": ["spectroscopy", "photometry", "interferometry"],
        "problem": ["dark energy nature", "missing baryon problem"],
        "topic": ["multiverse", "primordial black holes", "gravitational lensing"],
        "parameter": ["Hubble constant", "density parameter", "optical depth"],
        "entity_a": ["galaxy", "quasar"],
        "entity_b": ["supernova", "pulsar"]
    },
    "ecology": {
        "phenomenon": ["trophic cascade", "biodiversity loss", "carbon sequestration"],
        "theory": ["niche theory", "island biogeography", "metacommunity theory"],
        "application": ["conservation planning", "restoration ecology", "climate adaptation"],
        "variable_a": ["population density", "species richness", "habitat area"],
        "variable_b": ["growth rate", "extinction risk", "carrying capacity"],
        "component": ["producer", "consumer", "decomposer"],
        "process": ["succession", "migration", "adaptation"],
        "factor": ["temperature", "precipitation", "nutrient availability"],
        "outcome": ["ecosystem stability", "resilience", "function"],
        "concept_a": ["abiotic", "biotic"],
        "concept_b": ["density-dependent", "density-independent"],
        "method": ["mark-recapture", "remote sensing", "stable isotope analysis"],
        "problem": ["invasive species", "habitat fragmentation", "climate change"],
        "topic": ["ecosystem services", "keystone species", "biodiversity hotspots"],
        "parameter": ["diversity index", "productivity", "connectivity"],
        "entity_a": ["species", "community"],
        "entity_b": ["habitat", "landscape"]
    },
    "neuroscience": {
        "phenomenon": ["synaptic plasticity", "neural oscillation", "sensory integration"],
        "theory": ["predictive coding", "neural Darwinism", "global workspace theory"],
        "application": ["brain-computer interface", "neuroprosthetics", "cognitive enhancement"],
        "variable_a": ["firing rate", "synaptic weight", "membrane potential"],
        "variable_b": ["learning rate", "information capacity", "response latency"],
        "component": ["neuron", "glial cell", "synapse", "axon"],
        "process": ["action potential", "neurotransmission", "plasticity"],
        "factor": ["neurotransmitter concentration", "ion channel density", "temperature"],
        "outcome": ["memory formation", "motor control", "perception"],
        "concept_a": ["bottom-up", "top-down"],
        "concept_b": ["local", "global"],
        "method": ["EEG", "fMRI", "patch-clamp", "optogenetics"],
        "problem": ["neurodegeneration", "consciousness", "learning mechanisms"],
        "topic": ["connectome", "neural coding", "brain-computer interface"],
        "parameter": ["signal-to-noise ratio", "firing threshold", "conduction velocity"],
        "entity_a": ["cortex", "hippocampus"],
        "entity_b": ["thalamus", "amygdala"]
    }
}

def generate_random_float(min_val: float = 0.0, max_val: float = 1.0, precision: int = 4) -> float:
    """Generate a random float within a range with specified precision."""
    value = random.uniform(min_val, max_val)
    return round(value, precision)

def generate_random_int(min_val: int = 1, max_val: int = 100) -> int:
    """Generate a random integer within a range."""
    return random.randint(min_val, max_val)

def calculate_ground_truth(prompt: str, domain: str, seed: int) -> str:
    """
    Calculate a deterministic 'ground truth' answer based on the prompt and domain.
    This uses a deterministic hash-based approach to ensure reproducibility.
    """
    # Use the seed to ensure reproducibility
    random.seed(seed)
    
    # Generate a deterministic "answer" structure based on domain
    concepts = DOMAIN_CONCEPTS.get(domain, DOMAIN_CONCEPTS["physics"])
    
    # Create a structured ground truth that looks like a scientific explanation
    steps = [
        f"Step 1: Identify key concepts in the query related to {domain}.",
        f"Step 2: Retrieve relevant theoretical frameworks from {domain} knowledge base.",
        f"Step 3: Apply {random.choice(list(concepts['method']))} to analyze the problem.",
        f"Step 4: Synthesize findings using principles of {random.choice(concepts['theory'])}.",
        f"Step 5: Validate against established {domain} literature and experimental data."
    ]
    
    # Create a deterministic answer string
    answer_parts = [
        f"In the context of {domain}, the query addresses fundamental aspects of {random.choice(concepts['topic'])}.",
        f"Based on {random.choice(concepts['theory'])}, we can explain that {random.choice(concepts['phenomenon'])} plays a critical role.",
        f"The relationship between {random.choice(concepts['variable_a'])} and {random.choice(concepts['variable_b'])} is governed by {random.choice(concepts['theory'])}.",
        f"Experimental evidence from {random.choice(concepts['method'])} supports the hypothesis that {random.choice(concepts['outcome'])} occurs under specific conditions.",
        f"Further research should focus on {random.choice(concepts['problem'])} to advance our understanding of {domain}."
    ]
    
    ground_truth = " ".join(answer_parts)
    return ground_truth, steps

def generate_query(domain: str, seed: int) -> Dict[str, Any]:
    """Generate a single scientific query with metadata."""
    random.seed(seed)
    
    # Select a template
    template = random.choice(QUERY_TEMPLATES)
    
    # Get domain-specific concepts
    concepts = DOMAIN_CONCEPTS.get(domain, DOMAIN_CONCEPTS["physics"])
    
    # Fill in the template with random concepts from the domain
    prompt = template
    replacements = {
        "{phenomenon}": random.choice(concepts.get("phenomenon", ["general phenomenon"])),
        "{domain}": domain,
        "{theory}": random.choice(concepts.get("theory", ["general theory"])),
        "{application}": random.choice(concepts.get("application", ["general application"])),
        "{variable_a}": random.choice(concepts.get("variable_a", ["variable A"])),
        "{variable_b}": random.choice(concepts.get("variable_b", ["variable B"])),
        "{component}": random.choice(concepts.get("component", ["component"])),
        "{process}": random.choice(concepts.get("process", ["process"])),
        "{factor}": random.choice(concepts.get("factor", ["factor"])),
        "{outcome}": random.choice(concepts.get("outcome", ["outcome"])),
        "{concept_a}": random.choice(concepts.get("concept_a", ["concept A"])),
        "{concept_b}": random.choice(concepts.get("concept_b", ["concept B"])),
        "{method}": random.choice(concepts.get("method", ["method"])),
        "{problem}": random.choice(concepts.get("problem", ["problem"])),
        "{topic}": random.choice(concepts.get("topic", ["topic"])),
        "{parameter}": random.choice(concepts.get("parameter", ["parameter"])),
        "{entity_a}": random.choice(concepts.get("entity_a", ["entity A"])),
        "{entity_b}": random.choice(concepts.get("entity_b", ["entity B"]))
    }
    
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)
    
    # Generate ground truth and steps
    ground_truth, steps = calculate_ground_truth(prompt, domain, seed)
    
    # Create a unique ID for this query
    query_id = hashlib.sha256(f"{seed}_{domain}_{prompt}".encode()).hexdigest()[:16]
    
    return {
        "id": query_id,
        "prompt": prompt,
        "ground_truth": ground_truth,
        "steps": steps,
        "seed": seed,
        "domain": domain
    }

def generate_dataset(num_queries: int, output_path: str, dataset_type: str = "test") -> None:
    """
    Generate a dataset of synthetic scientific queries.
    
    Args:
        num_queries: Number of queries to generate
        output_path: Path to save the JSON file
        dataset_type: Type of dataset ("test" or "warmup")
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate queries with deterministic seeds
    queries = []
    
    # Use a base seed for reproducibility
    base_seed = 12345 if dataset_type == "warmup" else 54321
    
    for i in range(num_queries):
        # Calculate a unique seed for each query
        seed = base_seed + i
        
        # Select a domain (cycling through available domains)
        domain = DOMAINS[i % len(DOMAINS)]
        
        # Generate the query
        query = generate_query(domain, seed)
        queries.append(query)
    
    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(queries, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {num_queries} {dataset_type} queries to {output_path}")
    print(f"Domains represented: {set(q['domain'] for q in queries)}")

def main():
    """Main function to generate datasets."""
    # Define output paths
    warmup_path = "data/derived/synthetic_queries_warmup.json"
    
    # Generate warm-up set (100 queries) as per T005a
    print("Generating warm-up set (100 queries)...")
    generate_dataset(
        num_queries=100,
        output_path=warmup_path,
        dataset_type="warmup"
    )
    
    # Verify the file was created
    if Path(warmup_path).exists():
        with open(warmup_path, 'r') as f:
            data = json.load(f)
            print(f"Successfully created {warmup_path} with {len(data)} queries")
    else:
        raise FileNotFoundError(f"Failed to create {warmup_path}")

if __name__ == "__main__":
    main()
