"""
Pydantic schema definitions for the plant metabolite prediction project.

This module defines the core data models used throughout the pipeline:
  - Species
  - BGCFeature
  - Metabolite
  - ModelOutput

The models are deliberately lightweight and focus on validation of the
fields that are required by the downstream code.  They are re-exported
from the sibling modules (``code/models/species.py`` etc.) so existing
import statements in the code base continue to work.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "Species",
    "BGCFeature",
    "Metabolite",
    "ModelOutput",
]


class Species(BaseModel):
    """
    Representation of a plant species used in the analysis.

    Attributes
    ----------
    name: str
        Human-readable common name (e.g. ``Arabidopsis thaliana``).
    scientific_name: str
        Full binomial name (e.g. ``Arabidopsis thaliana``).  Used as a
        unique identifier throughout the pipeline.
    clade: Optional[str]
        Phylogenetic clade or taxonomic group; may be ``None`` if unknown.
    genome_path: Optional[str]
        Path (relative to the project root) to the downloaded genome FASTA
        file for this species.
    metabolite_path: Optional[str]
        Path (relative to the project root) to the metabolite abundance
        table for this species.
    """

    name: str = Field(..., description="Common name of the species")
    scientific_name: str = Field(..., description="Binomial scientific name")
    clade: Optional[str] = Field(
        None, description="Phylogenetic clade or taxonomic group"
    )
    genome_path: Optional[str] = Field(
        None, description="Path to the genome assembly file"
    )
    metabolite_path: Optional[str] = Field(
        None, description="Path to the metabolite abundance file"
    )

    @field_validator("name", "scientific_name")
    @classmethod
    def non_empty_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non-empty string")
        return v.strip()


class BGCFeature(BaseModel):
    """
    A biosynthetic gene cluster (BGC) feature for a given species.

    Attributes
    ----------
    species: str
        The ``scientific_name`` of the species to which this feature belongs.
    bgc_type: str
        Type/category of the BGC (e.g. ``polyketide``, ``terpene``).
    presence: bool
        Binary presence flag - ``True`` if at least one BGC of this type is
        detected in the genome.
    count: int
        Number of BGCs of this type detected in the genome.  Must be >= 0.
    """

    species: str = Field(..., description="Scientific name of the species")
    bgc_type: str = Field(..., description="Type of the BGC")
    presence: bool = Field(..., description="Binary presence flag")
    count: int = Field(..., ge=0, description="Count of BGCs of this type")

    @field_validator("species", "bgc_type")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non-empty string")
        return v.strip()


class Metabolite(BaseModel):
    """
    Metabolite observation for a given species.

    Attributes
    ----------
    species: str
        The ``scientific_name`` of the species.
    inchikey: str
        InChIKey identifier for the compound.
    abundance: float
        Raw abundance value (e.g. peak intensity).  Must be >= 0.
    log_abundance: Optional[float]
        Log-transformed abundance (log(x + 1)).  Populated by the
        ``harmonize_metabolites`` step; can be omitted when the raw value
        is supplied.
    compound_class: Optional[str]
        High-level chemical class (e.g. ``terpenoid``).  May be ``None``
        when unknown.
    """

    species: str = Field(..., description="Scientific name of the species")
    inchikey: str = Field(..., description="InChIKey of the compound")
    abundance: float = Field(..., ge=0.0, description="Raw abundance")
    log_abundance: Optional[float] = Field(
        None, description="Log-transformed abundance (log(x+1))"
    )
    compound_class: Optional[str] = Field(None, description="Metabolite chemical class")

    @field_validator("species", "inchikey")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non-empty string")
        return v.strip()


class ModelOutput(BaseModel):
    """
    Summary of a trained model's performance and configuration.

    Attributes
    ----------
    algorithm: str
        Name of the algorithm (e.g. ``RandomForest``, ``ElasticNet``,
        ``GradientBoosting``, ``PGLS``).
    hyperparameters: Dict[str, Any]
        Dictionary of hyper-parameter settings used for training.
    r_squared: float
        Coefficient of determination on the hold-out test set.  Must be
        between -1 and 1.
    pearson_r: float
        Pearson correlation coefficient between predictions and true
        values.  Must be between -1 and 1.
    p_value: float
        Two-sided p-value from the permutation baseline; must be in
        ``[0, 1]``.
    cv_method: str
        Cross-validation strategy identifier (e.g. ``LOO`` or ``5Fold``).
    feature_importances: Optional[List[float]]
        Optional list of feature importance scores (order matches the
        training feature matrix).  May be omitted for models that do
        not expose importances.
    """

    algorithm: str = Field(..., description="Algorithm identifier")
    hyperparameters: Dict[str, Any] = Field(
        default_factory=dict, description="Model hyper-parameters"
    )
    r_squared: float = Field(..., ge=-1.0, le=1.0, description="R^2 score")
    pearson_r: float = Field(..., ge=-1.0, le=1.0, description="Pearson r")
    p_value: float = Field(..., ge=0.0, le=1.0, description="Permutation p-value")
    cv_method: str = Field(..., description="Cross-validation method")
    feature_importances: Optional[List[float]] = Field(
        None, description="Feature importance scores"
    )

    @field_validator("algorithm", "cv_method")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non-empty string")
        return v.strip()
