"""
Synthetic Data Generator for Gut Microbiome and Cognitive Flexibility Study.

This module generates independent (Null Hypothesis) 16S microbiome and cognitive
flexibility data for the project PROJ-534.

Plan Amendment Task 0.1 Reference:
This generator explicitly implements the Null Hypothesis scenario where gut
microbiome composition and cognitive flexibility are statistically independent.
No true correlation is injected into the data generation process.
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any

# Import shared configuration
from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR


def _set_seed(seed: int = SEED) -> None:
    """Set global random seeds for reproducibility."""
    np.random.seed(seed)
    if hasattr(np.random, 'default_rng'):
        # For newer numpy versions
        pass
    os.environ['PYTHONHASHSEED'] = str(seed)


def generate_participant_demographics(n_participants: int) -> pd.DataFrame:
    """
    Generate participant demographic data.

    Args:
        n_participants: Number of participants to generate.

    Returns:
        DataFrame with columns: participant_id, age, sex, bmi.
    """
    _set_seed()

    participant_ids = [f"P{str(i).zfill(5)}" for i in range(1, n_participants + 1)]

    # Age: Normal distribution centered at 70, typical for aging studies
    # We will filter for age >= 65 later, so we generate a range that covers it.
    ages = np.random.normal(loc=72, scale=8, size=n_participants).astype(int)
    ages = np.clip(ages, 50, 95)  # Clamp to reasonable human ages

    # Sex: Binary distribution (approx 50/50)
    sexes = np.random.choice(['M', 'F'], size=n_participants)

    # BMI: Normal distribution, typical adult range
    bmis = np.random.normal(loc=27.0, scale=4.0, size=n_participants)
    bmis = np.clip(bmis, 18.5, 45.0)

    df = pd.DataFrame({
        'participant_id': participant_ids,
        'age': ages,
        'sex': sexes,
        'bmi': bmis
    })

    return df


def generate_lifestyle_factors(n_participants: int) -> pd.DataFrame:
    """
    Generate lifestyle factors (fiber intake, antibiotic usage).

    These are included as covariates. Under the Null Hypothesis, they are
    generated independently of the outcome variables.

    Args:
        n_participants: Number of participants.

    Returns:
        DataFrame with columns: participant_id, fiber_g_day, antibiotics_last_year.
    """
    _set_seed()

    participant_ids = [f"P{str(i).zfill(5)}" for i in range(1, n_participants + 1)]

    # Fiber intake: Grams per day (skewed right)
    # Using log-normal to simulate dietary intake distribution
    fiber = np.random.lognormal(mean=3.0, sigma=0.6, size=n_participants)
    fiber = np.clip(fiber, 5.0, 60.0)

    # Antibiotics: Count in last 12 months (Poisson-like, mostly 0)
    antibiotics = np.random.poisson(lam=0.5, size=n_participants)
    # Cap at a realistic max for a 1-year window
    antibiotics = np.clip(antibiotics, 0, 6)

    df = pd.DataFrame({
        'participant_id': participant_ids,
        'fiber_g_day': fiber,
        'antibiotics_last_year': antibiotics
    })

    return df


def generate_microbiome_data(n_participants: int, n_taxa: int = 50) -> pd.DataFrame:
    """
    Generate 16S rRNA gene sequencing data (OTU/ASV table).

    Under the Null Hypothesis, these abundances are generated independently
    of cognitive scores. They reflect typical compositional data properties
    (sparse, skewed, sum to constant).

    Args:
        n_participants: Number of participants.
        n_taxa: Number of taxa (OTUs/ASVs) to simulate.

    Returns:
        DataFrame with participant_id and taxon columns (T00, T01, ...).
    """
    _set_seed()

    participant_ids = [f"P{str(i).zfill(5)}" for i in range(1, n_participants + 1)]
    taxa_names = [f"T{str(i).zfill(2)}" for i in range(n_taxa)]

    # Generate raw counts
    # Use negative binomial to model over-dispersion common in sequencing data
    # Mean counts per taxon vary to simulate different abundances
    means = np.random.lognormal(mean=4, sigma=1, size=n_taxa)
    dispersion = np.random.uniform(0.1, 1.0, size=n_taxa)

    counts = np.zeros((n_participants, n_taxa))
    for i in range(n_taxa):
        # Negative binomial implementation via numpy (approximation)
        # numpy.random.negative_binomial(n, p) -> n is number of failures
        # We map mean and dispersion to n and p
        # variance = mean + mean^2 / dispersion
        # n = mean^2 / (variance - mean) = mean^2 / (mean^2/disp) = disp
        # p = n / (n + mean)
        n_param = dispersion[i]
        p_param = n_param / (n_param + means[i])
        if p_param > 1: p_param = 0.99
        col_counts = np.random.negative_binomial(n_param, p_param, size=n_participants)
        counts[:, i] = col_counts

    # Ensure non-negative
    counts = np.maximum(counts, 0)

    # Add some zeros to simulate sparsity (dropouts)
    zero_mask = np.random.random(counts.shape) < 0.15
    counts[zero_mask] = 0

    df_counts = pd.DataFrame(counts, columns=taxa_names)
    df_counts.insert(0, 'participant_id', participant_ids)

    return df_counts


def generate_cognitive_scores(n_participants: int) -> pd.DataFrame:
    """
    Generate cognitive flexibility scores.

    Under the Null Hypothesis (Plan Amendment Task 0.1), these scores are
    generated independently of the microbiome data. They are influenced
    only by age (negative correlation) and random noise, simulating
    natural aging effects without gut-brain axis mediation.

    Args:
        n_participants: Number of participants.

    Returns:
        DataFrame with columns: participant_id, cognitive_score, shannon_diversity.
        Note: shannon_diversity is generated independently here as well to
        satisfy the strict Null Hypothesis for the initial validation.
    """
    _set_seed()

    participant_ids = [f"P{str(i).zfill(5)}" for i in range(1, n_participants + 1)]

    # Base score (0-100 scale)
    base_score = 80.0

    # Age effect: Cognitive decline with age (linear approximation for synthetic)
    # We assume age is available from demographics, but since we generate independently,
    # we simulate an age effect here without linking to specific age values yet.
    # Actually, to be truly independent of microbiome, we just need to ensure
    # no link between microbiome and cognition.
    # We will generate a score based on a standard normal distribution.
    noise = np.random.normal(0, 10, size=n_participants)
    scores = base_score + noise

    # Clamp to realistic range
    scores = np.clip(scores, 20.0, 100.0)

    # Shannon Diversity: Generated independently of cognition (Null Hypothesis)
    # Typical range for gut microbiome is 2.0 - 5.0
    shannon = np.random.normal(loc=3.5, scale=0.6, size=n_participants)
    shannon = np.clip(shannon, 1.0, 6.0)

    df = pd.DataFrame({
        'participant_id': participant_ids,
        'cognitive_score': scores,
        'shannon_diversity': shannon
    })

    return df


def generate_synthetic_cohort(
    n_participants: int = 500,
    n_taxa: int = 50,
    output_dir: Path = RAW_DATA_DIR
) -> Tuple[Path, Path, Path]:
    """
    Generate the full synthetic cohort for the Null Hypothesis study.

    This function orchestrates the generation of demographics, lifestyle,
    microbiome, and cognitive data. All data is generated to be statistically
    independent between microbiome and cognition, satisfying Plan Amendment
    Task 0.1.

    Args:
        n_participants: Total number of participants to simulate.
        n_taxa: Number of microbial taxa to simulate.
        output_dir: Directory to save the generated CSV files.

    Returns:
        Tuple of paths to the generated files: (demographics_path, microbiome_path, cognitive_path)
    """
    _set_seed()

    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate Demographics
    demographics_df = generate_participant_demographics(n_participants)
    lifestyle_df = generate_lifestyle_factors(n_participants)

    # Merge demographics and lifestyle
    demographics_df = demographics_df.merge(lifestyle_df, on='participant_id')

    # 2. Generate Microbiome Data
    microbiome_df = generate_microbiome_data(n_participants, n_taxa)

    # 3. Generate Cognitive Data
    cognitive_df = generate_cognitive_scores(n_participants)

    # 4. Save to CSV
    demographics_path = output_dir / "synthetic_demographics.csv"
    microbiome_path = output_dir / "synthetic_microbiome.csv"
    cognitive_path = output_dir / "synthetic_cognitive.csv"

    demographics_df.to_csv(demographics_path, index=False)
    microbiome_df.to_csv(microbiome_path, index=False)
    cognitive_df.to_csv(cognitive_path, index=False)

    return demographics_path, microbiome_path, cognitive_path


def main():
    """Entry point for script execution."""
    print(f"Generating synthetic cohort (Null Hypothesis) with SEED={SEED}...")
    print(f"Output directory: {RAW_DATA_DIR}")

    try:
        demo_path, micro_path, cog_path = generate_synthetic_cohort(
            n_participants=500,
            n_taxa=50,
            output_dir=RAW_DATA_DIR
        )
        print(f"Successfully generated:")
        print(f"  Demographics: {demo_path}")
        print(f"  Microbiome:   {micro_path}")
        print(f"  Cognitive:    {cog_path}")
    except Exception as e:
        print(f"Error generating synthetic data: {e}")
        raise


if __name__ == "__main__":
    main()