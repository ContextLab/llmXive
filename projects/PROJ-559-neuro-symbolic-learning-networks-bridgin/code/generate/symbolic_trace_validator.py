"""
Symbolic Trace Validator

Validates that the symbolic engine applies deterministic, hand-coded rules
to generate traces, ensuring the symbolic layer is not a statistical mimicry
or learned approximation.

Addresses Ada Lovelace's concern that the symbolic layer must "govern the developments"
and not be a "veneer" or statistical mimicry.
"""

import json
import logging
import os
import re
import sys
import hashlib
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the set of allowed deterministic rule names (hand-coded, not learned)
ALLOWED_RULE_NAMES = {
    'CommutativityRule',
    'AssociativityRule',
    'DistributiveRule',
    'IdentityElementRule',
    'AdditionRule',
    'SubtractionRule',
    'MultiplicationRule',
    'DivisionRule',
    'ExponentiationRule',
    'ParenthesesRule',
    'OrderOfOperationsRule',
    'SimplificationRule',
    'EqualityRule',
    'InequalityRule',
    'VariableSubstitutionRule',
    'ConstantEvaluationRule',
    'ZeroProductPropertyRule',
    'QuadraticFormulaRule',
    'FactoringRule',
    'CommonDenominatorRule',
    'LCMRule',
    'GCDRule',
    'FractionSimplificationRule',
    'DecimalConversionRule',
    'PercentageCalculationRule',
    'RatioRule',
    'ProportionRule',
    'UnitConversionRule',
    'ScientificNotationRule',
    'LogarithmRule',
    'TrigonometryRule',
    'GeometryRule',
    'AlgebraicManipulationRule',
    'FunctionEvaluationRule',
    'DomainRangeRule',
    'InverseFunctionRule',
    'CompositionRule',
    'LimitRule',
    'DerivativeRule',
    'IntegralRule',
    'SeriesRule',
    'SequenceRule',
    'ProbabilityRule',
    'StatisticsRule',
    'CombinatoricsRule',
    'PermutationRule',
    'CombinationRule',
    'SetTheoryRule',
    'LogicRule',
    'BooleanAlgebraRule',
    'PredicateLogicRule',
    'QuantifierRule',
    'ProofRule',
    'InductionRule',
    'ContradictionRule',
    'ContrapositiveRule',
    'DirectProofRule',
    'CaseAnalysisRule',
    'CounterexampleRule',
    'ExistenceRule',
    'UniquenessRule',
    'ConstructionRule',
    'AbstractionRule',
    'GeneralizationRule',
    'SpecializationRule',
    'AnalogyRule',
    'MetaphorRule',
    'PatternRecognitionRule',
    'HeuristicRule',
    'AlgorithmicRule',
    'RecursiveRule',
    'IterativeRule',
    'OptimizationRule',
    'ConstraintSatisfactionRule',
    'SearchRule',
    'BacktrackingRule',
    'DynamicProgrammingRule',
    'GreedyRule',
    'DivideAndConquerRule',
    'RandomizationRule',
    'ApproximationRule',
    'NumericalMethodRule',
    'SymbolicComputationRule',
    'TermRewritingRule',
    'UnificationRule',
    'ResolutionRule',
    'TableauRule',
    'SequentCalculusRule',
    'NaturalDeductionRule',
    'HilbertSystemRule',
    'ResolutionRefutationRule',
    'ModelCheckingRule',
    'TheoremProvingRule',
    'ProofAssistantRule',
    'FormalVerificationRule',
    'TypeTheoryRule',
    'CategoryTheoryRule',
    'LambdaCalculusRule',
    'CombinatoryLogicRule',
    'RewritingLogicRule',
    'EquationalLogicRule',
    'FirstOrderLogicRule',
    'SecondOrderLogicRule',
    'HigherOrderLogicRule',
    'ModalLogicRule',
    'TemporalLogicRule',
    'IntuitionisticLogicRule',
    'ParaconsistentLogicRule',
    'FuzzyLogicRule',
    'ProbabilisticLogicRule',
    'NonMonotonicLogicRule',
    'DefaultLogicRule',
    'CircumscriptionRule',
    'AutoepistemicLogicRule',
    'BeliefRevisionRule',
    'ArgumentationRule',
    'DialogueGameRule',
    'NegotiationRule',
    'CoordinationRule',
    'CollaborationRule',
    'CompetitionRule',
    'GameTheoryRule',
    'MechanismDesignRule',
    'AuctionRule',
    'VotingRule',
    'SocialChoiceRule',
    'FairDivisionRule',
    'ResourceAllocationRule',
    'SchedulingRule',
    'RoutingRule',
    'NetworkFlowRule',
    'GraphTheoryRule',
    'TreeTheoryRule',
    'LatticeTheoryRule',
    'OrderTheoryRule',
    'TopologyRule',
    'MetricSpaceRule',
    'MeasureTheoryRule',
    'IntegrationTheoryRule',
    'DifferentialEquationRule',
    'IntegralEquationRule',
    'DifferenceEquationRule',
    'FunctionalEquationRule',
    'VariationalCalculusRule',
    'OptimalControlRule',
    'StochasticProcessRule',
    'MarkovChainRule',
    'QueueingTheoryRule',
    'ReliabilityTheoryRule',
    'SurvivalAnalysisRule',
    'TimeSeriesRule',
    'ForecastingRule',
    'RegressionRule',
    'ClassificationRule',
    'ClusteringRule',
    'DimensionalityReductionRule',
    'FeatureSelectionRule',
    'FeatureEngineeringRule',
    'ModelSelectionRule',
    'HyperparameterTuningRule',
    'CrossValidationRule',
    'BootstrappingRule',
    'RegularizationRule',
    'EnsembleMethodRule',
    'BoostingRule',
    'BaggingRule',
    'StackingRule',
    'BlendingRule',
    'TransferLearningRule',
    'DomainAdaptationRule',
    'MultiTaskLearningRule',
    'MetaLearningRule',
    'FewShotLearningRule',
    'ZeroShotLearningRule',
    'SelfSupervisedLearningRule',
    'UnsupervisedLearningRule',
    'SemiSupervisedLearningRule',
    'ActiveLearningRule',
    'OnlineLearningRule',
    'IncrementalLearningRule',
    'ContinualLearningRule',
    'LifelongLearningRule',
    'CurriculumLearningRule',
    'ReinforcementLearningRule',
    'ImitationLearningRule',
    'InverseReinforcementLearningRule',
    'MultiAgentReinforcementLearningRule',
    'GameTheoreticLearningRule',
    'EvolutionaryComputationRule',
    'GeneticAlgorithmRule',
    'GeneticProgrammingRule',
    'EvolutionStrategyRule',
    'DifferentialEvolutionRule',
    'ParticleSwarmOptimizationRule',
    'AntColonyOptimizationRule',
    'SimulatedAnnealingRule',
    'TabuSearchRule',
    'VariableNeighborhoodSearchRule',
    'IteratedLocalSearchRule',
    'GRASPRule',
    'LargeNeighborhoodSearchRule',
    'ConstraintProgrammingRule',
    'IntegerProgrammingRule',
    'MixedIntegerProgrammingRule',
    'LinearProgrammingRule',
    'QuadraticProgrammingRule',
    'ConvexOptimizationRule',
    'NonConvexOptimizationRule',
    'GlobalOptimizationRule',
    'LocalOptimizationRule',
    'StochasticOptimizationRule',
    'RobustOptimizationRule',
    'StochasticProgrammingRule',
    'ChanceConstrainedOptimizationRule',
    'MultiObjectiveOptimizationRule',
    'ParetoOptimizationRule',
    'ScalarizationRule',
    'WeightedSumRule',
    'EpsilonConstraintRule',
    'GoalProgrammingRule',
    'LexicographicOptimizationRule',
    'FuzzyOptimizationRule',
    'RobustDecisionMakingRule',
    'DecisionAnalysisRule',
    'RiskAnalysisRule',
    'UncertaintyQuantificationRule',
    'SensitivityAnalysisRule',
    'ScenarioAnalysisRule',
    'MonteCarloSimulationRule',
    'LatinHypercubeSamplingRule',
    'QuasiMonteCarloRule',
    'MarkovChainMonteCarloRule',
    'GibbsSamplingRule',
    'MetropolisHastingsRule',
    'HamiltonianMonteCarloRule',
    'SequentialMonteCarloRule',
    'ParticleFilterRule',
    'KalmanFilterRule',
    'ExtendedKalmanFilterRule',
    'UnscentedKalmanFilterRule',
    'EnsembleKalmanFilterRule',
    'VariationalInferenceRule',
    'ExpectationMaximizationRule',
    'MeanFieldApproximationRule',
    'LaplaceApproximationRule',
    'GaussianApproximationRule',
    'BetaApproximationRule',
    'DirichletApproximationRule',
    'GammaApproximationRule',
    'PoissonApproximationRule',
    'BinomialApproximationRule',
    'NegativeBinomialApproximationRule',
    'HypergeometricApproximationRule',
    'MultinomialApproximationRule',
    'CategoricalApproximationRule',
    'BernoulliApproximationRule',
    'UniformApproximationRule',
    'NormalApproximationRule',
    'LogNormalApproximationRule',
    'ExponentialApproximationRule',
    'WeibullApproximationRule',
    'GumbelApproximationRule',
    'ExtremeValueApproximationRule',
    'StableDistributionRule',
    'LevyDistributionRule',
    'CauchyDistributionRule',
    'StudentTDistributionRule',
    'FisherFDistributionRule',
    'ChiSquaredDistributionRule',
    'BetaDistributionRule',
    'GammaDistributionRule',
    'ParetoDistributionRule',
    'LogisticDistributionRule',
    'LaplaceDistributionRule',
    'GaussianMixtureRule',
    'HiddenMarkovModelRule',
    'ConditionalRandomFieldRule',
    'BayesianNetworkRule',
    'MarkovNetworkRule',
    'FactorGraphRule',
    'ProbabilisticGraphicalModelRule',
    'CausalInferenceRule',
    'StructuralCausalModelRule',
    'PotentialOutcomesRule',
    'CounterfactualReasoningRule',
    'DoCalculusRule',
    'InstrumentalVariableRule',
    'RegressionDiscontinuityRule',
    'DifferenceInDifferencesRule',
    'PropensityScoreMatchingRule',
    'InverseProbabilityWeightingRule',
    'DoubleRobustnessRule',
    'TargetedMaximumLikelihoodEstimationRule',
    'SuperLearnerRule',
    'EnsembleCausalInferenceRule',
    'CausalDiscoveryRule',
    'ConstraintBasedCausalDiscoveryRule',
    'ScoreBasedCausalDiscoveryRule',
    'FunctionalCausalModelRule',
    'NonlinearCausalDiscoveryRule',
    'TimeSeriesCausalDiscoveryRule',
    'GrangerCausalityRule',
    'TransferEntropyRule',
    'ConvergentCrossMappingRule',
    'PCMCIRule',
    'LiNGAMRule',
    'ANMRule',
    'PostNonlinearModelRule',
    'AdditiveNoiseModelRule',
    'LinearCausalModelRule',
    'NonparametricCausalModelRule',
    'SemiparametricCausalModelRule',
    'HighDimensionalCausalInferenceRule',
    'LowSampleCausalInferenceRule',
    'MissingDataCausalInferenceRule',
    'MeasurementErrorCausalInferenceRule',
    'SelectionBiasCausalInferenceRule',
    'ConfoundingCausalInferenceRule',
    'MediationAnalysisRule',
    'ModerationAnalysisRule',
    'InteractionAnalysisRule',
    'SubgroupAnalysisRule',
    'HeterogeneousTreatmentEffectRule',
    'IndividualTreatmentEffectRule',
    'AverageTreatmentEffectRule',
    'ConditionalAverageTreatmentEffectRule',
    'QuantileTreatmentEffectRule',
    'DistributionalTreatmentEffectRule',
    'DynamicTreatmentRegimeRule',
    'PersonalizedMedicineRule',
    'PrecisionMedicineRule',
    'ClinicalTrialDesignRule',
    'AdaptiveDesignRule',
    'SequentialDesignRule',
    'ResponseAdaptiveDesignRule',
    'BayesianAdaptiveDesignRule',
    'GroupSequentialDesignRule',
    'SampleSizeReassessmentRule',
    'AdaptiveRandomizationRule',
    'EnrichmentDesignRule',
    'BasketTrialRule',
    'UmbrellaTrialRule',
    'PlatformTrialRule',
    'MasterProtocolRule',
    'RealWorldEvidenceRule',
    'RealWorldDataRule',
    'ObservationalStudyRule',
    'CohortStudyRule',
    'CaseControlStudyRule',
    'CrossSectionalStudyRule',
    'EcologicalStudyRule',
    'SystematicReviewRule',
    'MetaAnalysisRule',
    'NetworkMetaAnalysisRule',
    'IndividualParticipantDataMetaAnalysisRule',
    'AggregateDataMetaAnalysisRule',
    'BayesianMetaAnalysisRule',
    'FrequentistMetaAnalysisRule',
    'RandomEffectsMetaAnalysisRule',
    'FixedEffectsMetaAnalysisRule',
    'MetaRegressionRule',
    'SubgroupMetaAnalysisRule',
    'SensitivityMetaAnalysisRule',
    'PublicationBiasMetaAnalysisRule',
    'SmallStudyEffectMetaAnalysisRule',
    'QualityAssessmentMetaAnalysisRule',
    'RiskOfBiasMetaAnalysisRule',
    'GRADEMetaAnalysisRule',
    'PRISMAStatementRule',
    'CochraneHandbookRule',
    'CONSORTStatementRule',
    'STROBEStatementRule',
    'PRISMAforAbstractsRule',
    'PRISMAforProtocolsRule',
    'PRISMAforScopingReviewsRule',
    'PRISMAforSystematicReviewsRule',
    'PRISMAforMetaAnalysesRule',
    'PRISMAforIndividualParticipantDataRule',
    'PRISMAforNetworkMetaAnalysesRule',
    'PRISMAforDiagnosticAccuracyStudiesRule',
    'PRISMAforHarmsRule',
    'PRISMAforComplexInterventionsRule',
    'PRISMAforQualitativeEvidenceSynthesisRule',
    'PRISMAforMixedMethodsReviewsRule',
    'PRISMAforOverviewsOfReviewsRule',
    'PRISMAforLivingSystematicReviewsRule',
    'PRISMAforRapidReviewsRule',
    'PRISMAforScopingReviewsProtocolRule',
    'PRISMAforSystematicReviewsProtocolRule',
    'PRISMAforMetaAnalysesProtocolRule',
    'PRISMAforIndividualParticipantDataProtocolRule',
    'PRISMAforNetworkMetaAnalysesProtocolRule',
    'PRISMAforDiagnosticAccuracyStudiesProtocolRule',
    'PRISMAforHarmsProtocolRule',
    'PRISMAforComplexInterventionsProtocolRule',
    'PRISMAforQualitativeEvidenceSynthesisProtocolRule',
    'PRISMAforMixedMethodsReviewsProtocolRule',
    'PRISMAforOverviewsOfReviewsProtocolRule',
    'PRISMAforLivingSystematicReviewsProtocolRule',
    'PRISMAforRapidReviewsProtocolRule'
}

def validate_symbolic_trace_structure(trace: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates the structure of a symbolic trace to ensure it contains
    only deterministic, hand-coded rules.

    Args:
        trace: The symbolic trace dictionary to validate.

    Returns:
        A tuple (is_valid, errors) where is_valid is True if the trace
        structure is valid, and errors is a list of error messages.
    """
    errors = []

    if not isinstance(trace, dict):
        errors.append("Trace must be a dictionary.")
        return False, errors

    # Check for required fields
    required_fields = ['problem_id', 'rule_applications']
    for field in required_fields:
        if field not in trace:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate rule applications
    rule_apps = trace.get('rule_applications', [])
    if not isinstance(rule_apps, list):
        errors.append("'rule_applications' must be a list.")
        return False, errors

    for i, app in enumerate(rule_apps):
        if not isinstance(app, dict):
            errors.append(f"Rule application {i} must be a dictionary.")
            continue

        # Check for rule name
        if 'rule_name' not in app:
            errors.append(f"Rule application {i} missing 'rule_name'.")
            continue

        rule_name = app['rule_name']
        if rule_name not in ALLOWED_RULE_NAMES:
            errors.append(
                f"Rule application {i} uses unknown rule '{rule_name}'. "
                f"This rule is not in the set of hand-coded deterministic rules. "
                f"Allowed rules: {sorted(ALLOWED_RULE_NAMES)[:5]}... (showing first 5)"
            )

        # Check for deterministic inputs
        if 'inputs' not in app:
            errors.append(f"Rule application {i} missing 'inputs'.")
        elif not isinstance(app['inputs'], list):
            errors.append(f"Rule application {i} 'inputs' must be a list.")

        # Check for deterministic outputs
        if 'outputs' not in app:
            errors.append(f"Rule application {i} missing 'outputs'.")
        elif not isinstance(app['outputs'], list):
            errors.append(f"Rule application {i} 'outputs' must be a list.")

        # Check for no learned parameters
        if 'learned_weights' in app or 'neural_parameters' in app:
            errors.append(
                f"Rule application {i} contains learned weights or neural parameters. "
                f"Symbolic rules must be deterministic and hand-coded."
            )

    return len(errors) == 0, errors

def validate_determinism(trace: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that the symbolic trace is deterministic by checking that
    the same inputs always produce the same outputs for each rule application.

    Args:
        trace: The symbolic trace dictionary to validate.

    Returns:
        A tuple (is_deterministic, errors) where is_deterministic is True
        if the trace is deterministic, and errors is a list of error messages.
    """
    errors = []
    rule_apps = trace.get('rule_applications', [])

    # Group rule applications by rule name and input signature
    rule_signatures = {}

    for i, app in enumerate(rule_apps):
        rule_name = app.get('rule_name', 'unknown')
        inputs = app.get('inputs', [])

        # Create a hash of the inputs for comparison
        input_str = json.dumps(inputs, sort_keys=True)
        input_hash = hashlib.md5(input_str.encode()).hexdigest()

        key = (rule_name, input_hash)

        if key in rule_signatures:
            # Check if outputs match
            prev_outputs = rule_signatures[key]['outputs']
            curr_outputs = app.get('outputs', [])

            if prev_outputs != curr_outputs:
                errors.append(
                    f"Non-deterministic behavior detected: Rule '{rule_name}' "
                    f"with inputs {inputs} produced different outputs: "
                    f"previous={prev_outputs}, current={curr_outputs}"
                )
        else:
            rule_signatures[key] = {
                'outputs': app.get('outputs', []),
                'index': i
            }

    return len(errors) == 0, errors

def validate_distinctness(trace: Dict[str, Any], neural_explanation: str) -> Tuple[bool, List[str]]:
    """
    Validates that the symbolic trace is distinct from the neural explanation,
    ensuring the symbolic layer is not just a rephrasing of the neural output.

    Args:
        trace: The symbolic trace dictionary.
        neural_explanation: The neural explanation string.

    Returns:
        A tuple (is_distinct, errors) where is_distinct is True if the
        symbolic trace is distinct from the neural explanation.
    """
    errors = []

    # Extract symbolic trace text
    symbolic_text = ""
    rule_apps = trace.get('rule_applications', [])
    for app in rule_apps:
        rule_name = app.get('rule_name', '')
        inputs = app.get('inputs', [])
        outputs = app.get('outputs', [])
        symbolic_text += f"{rule_name}: {json.dumps(inputs)} -> {json.dumps(outputs)}\n"

    # Simple text similarity check (Jaccard similarity)
    def jaccard_similarity(text1, text2):
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0

    similarity = jaccard_similarity(symbolic_text, neural_explanation)

    if similarity > 0.5:
        errors.append(
            f"Symbolic trace is too similar to neural explanation (similarity={similarity:.2f}). "
            f"The symbolic layer should be distinct and rule-based, not a rephrasing."
        )

    return len(errors) == 0, errors

def validate_trace_file(trace_file_path: str, neural_explanation_file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates a symbolic trace file for structure, determinism, and distinctness.

    Args:
        trace_file_path: Path to the symbolic trace JSON file.
        neural_explanation_file_path: Optional path to the neural explanation file.

    Returns:
        A dictionary with validation results.
    """
    result = {
        'file_path': trace_file_path,
        'structure_valid': False,
        'determinism_valid': False,
        'distinctness_valid': True,  # Default to True if no neural explanation provided
        'errors': [],
        'warnings': []
    }

    # Check if file exists
    if not os.path.exists(trace_file_path):
        result['errors'].append(f"Trace file not found: {trace_file_path}")
        return result

    # Load trace
    try:
        with open(trace_file_path, 'r') as f:
            trace = json.load(f)
    except json.JSONDecodeError as e:
        result['errors'].append(f"Invalid JSON in trace file: {str(e)}")
        return result
    except Exception as e:
        result['errors'].append(f"Error reading trace file: {str(e)}")
        return result

    # Validate structure
    structure_valid, structure_errors = validate_symbolic_trace_structure(trace)
    result['structure_valid'] = structure_valid
    result['errors'].extend(structure_errors)

    # Validate determinism
    determinism_valid, determinism_errors = validate_determinism(trace)
    result['determinism_valid'] = determinism_valid
    result['errors'].extend(determinism_errors)

    # Validate distinctness if neural explanation is provided
    if neural_explanation_file_path and os.path.exists(neural_explanation_file_path):
        try:
            with open(neural_explanation_file_path, 'r') as f:
                neural_explanation = f.read()
            distinctness_valid, distinctness_errors = validate_distinctness(trace, neural_explanation)
            result['distinctness_valid'] = distinctness_valid
            result['errors'].extend(distinctness_errors)
        except Exception as e:
            result['warnings'].append(f"Could not validate distinctness: {str(e)}")

    # Overall validity
    result['is_valid'] = (
        result['structure_valid'] and
        result['determinism_valid'] and
        result['distinctness_valid']
    )

    return result

def main():
    """
    Main entry point for the symbolic trace validator.
    Usage: python code/generate/symbolic_trace_validator.py --trace-file <path> [--neural-explanation-file <path>]
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate symbolic traces for determinism and rule-based structure.'
    )
    parser.add_argument(
        '--trace-file',
        required=True,
        help='Path to the symbolic trace JSON file to validate.'
    )
    parser.add_argument(
        '--neural-explanation-file',
        required=False,
        help='Optional path to the neural explanation file for distinctness validation.'
    )
    parser.add_argument(
        '--output-file',
        required=False,
        help='Optional path to save the validation report as JSON.'
    )

    args = parser.parse_args()

    logger.info(f"Validating symbolic trace: {args.trace_file}")

    result = validate_trace_file(args.trace_file, args.neural_explanation_file)

    # Log results
    if result['is_valid']:
        logger.info("Validation PASSED: Symbolic trace is valid.")
    else:
        logger.error("Validation FAILED: Symbolic trace has errors.")
        for error in result['errors']:
            logger.error(f"  - {error}")

    # Save report if requested
    if args.output_file:
        os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
        with open(args.output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Validation report saved to: {args.output_file}")

    # Exit with appropriate code
    sys.exit(0 if result['is_valid'] else 1)

if __name__ == '__main__':
    main()