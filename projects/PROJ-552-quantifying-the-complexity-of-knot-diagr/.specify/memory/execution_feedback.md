# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/reproducibility/validation_status.py; 7 command(s) failed: python code/download/knot_atlas_loader.py (rc=1); python code/analysis/exploratory.py (rc=1); python code/reproducibility/tie_breaking_validator.py (rc=1); 1 declared deliverable(s) absent: data/plots/complexity_visualization_examples.png

## Failing / missing run-book commands

- python -c "from code.reproducibility.logs import get_logger; logger = get_logger(); logger.log('test', 'verification')" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
AttributeError: 'ReproducibilityLogger' object has no attribute 'log'
- python code/download/knot_atlas_loader.py -> rc=1
    le "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/download/knot_atlas_loader.py", line 84, in <module>
    main()
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/download/knot_atlas_loader.py", line 78, in main
    df = pd.DataFrame(cleaned)
         ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?
- python code/analysis/exploratory.py -> rc=1
    ying-the-complexity-of-knot-diagr/code/analysis/exploratory.py", line 110, in <module>
    main()
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/exploratory.py", line 102, in main
    logger = get_logger(__name__)  # type: ignore[arg-type]
             ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given
- python code/reproducibility/tie_breaking_validator.py -> rc=1
    ng/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/reproducibility/tie_breaking_validator.py", line 65, in <module>
    main()
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/reproducibility/tie_breaking_validator.py", line 55, in main
    log_operation(
TypeError: log_operation() got an unexpected keyword argument 'operation'
- python code/analysis/regression.py -> rc=1
    gression.py", line 191, in main
    df = load_cleaned_knots()
         ^^^^^^^^^^^^^^^^^^^^
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/_utils.py", line 59, in load_cleaned_knots
    logger.debug("Loading cleaned knot data from %s", str(_CLEANED_PATH))
TypeError: ReproducibilityLogger.debug() takes 2 positional arguments but 3 were given
- python code/analysis/residual_analysis.py -> rc=1
    analysis.py", line 111, in main
    df = load_cleaned_knots()
         ^^^^^^^^^^^^^^^^^^^^
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/_utils.py", line 59, in load_cleaned_knots
    logger.debug("Loading cleaned knot data from %s", str(_CLEANED_PATH))
TypeError: ReproducibilityLogger.debug() takes 2 positional arguments but 3 were given
- python code/analysis/correlation.py -> rc=1
    rrelation.py", line 43, in main
    df = load_cleaned_knots()
         ^^^^^^^^^^^^^^^^^^^^
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/_utils.py", line 59, in load_cleaned_knots
    logger.debug("Loading cleaned knot data from %s", str(_CLEANED_PATH))
TypeError: ReproducibilityLogger.debug() takes 2 positional arguments but 3 were given
- python code/analysis/group_comparison.py -> rc=1
    omparison.py", line 49, in main
    df = load_cleaned_knots()
         ^^^^^^^^^^^^^^^^^^^^
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/_utils.py", line 59, in load_cleaned_knots
    logger.debug("Loading cleaned knot data from %s", str(_CLEANED_PATH))
TypeError: ReproducibilityLogger.debug() takes 2 positional arguments but 3 were given
- python code/reproducibility/validation_status.py -> rc=2 [script missing]
    /opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python: can't open file '/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/reproducibility/validation_status.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/plots/complexity_visualization_examples.png

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real, installable source was discovered AND verified by actually loading data from it:

- **Install**: add `database-knotinfo` to the project's `requirements.txt` and `pip install database-knotinfo`.
- **Verified**: this loads **12967** real records with fields: name, name_anon, category, category_anon, alternating, alternating_anon, name_rank, name_rank_anon, dt_name, dt_name_anon, dt_rank, dt_rank_anon, dt_notation, dt_notation_anon, classical_conway_name, classical_conway_name_anon, conway_notation, conway_notation_anon, two_bridge_notation, two_bridge_notation_anon, fibered, fibered_anon, gauss_notation, gauss_notation_anon, enhanced_gauss_notation, enhanced_gauss_notation_anon, pd_notation, pd_notation_anon, crossing_number, crossing_number_anon, tetrahedral_census_name, tetrahedral_census_name_anon, unknotting_number, unknotting_number_anon, three_genus, three_genus_anon, crosscap_number, crosscap_number_anon, bridge_index, bridge_index_anon, braid_index, braid_index_anon, braid_length, braid_length_anon, braid_notation, braid_notation_anon, signature, signature_anon, nakanishi_index, nakanishi_index_anon, super_bridge_index, super_bridge_index_anon, thurston_bennequin_number, thurston_bennequin_number_anon, arc_index, arc_index_anon, polygon_index, polygon_index_anon, tunnel_number, tunnel_number_anon, morse_novikov_number, morse_novikov_number_anon, alexander_polynomial, alexander_polynomial_anon, alexander_polynomial_vector, alexander_polynomial_vector_anon, jones_polynomial, jones_polynomial_anon, jones_polynomial_vector, jones_polynomial_vector_anon, conway_polynomial, conway_polynomial_anon, conway_polynomial_vector, conway_polynomial_vector_anon, kauffman_polynomial, kauffman_polynomial_anon, kauffman_polynomial_vector, kauffman_polynomial_vector_anon, a_polynomial, a_polynomial_anon, smooth_four_genus, smooth_four_genus_anon, topological_four_genus, topological_four_genus_anon, smooth_4d_crosscap_number, smooth_4d_crosscap_number_anon, topological_4d_crosscap_number, topological_4d_crosscap_number_anon, smooth_concordance_genus, smooth_concordance_genus_anon, topological_concordance_genus, topological_concordance_genus_anon, smooth_concordance_crosscap_number, smooth_concordance_crosscap_number_anon, topological_concordance_crosscap_number, topological_concordance_crosscap_number_anon, algebraic_concordance_order, algebraic_concordance_order_anon, smooth_concordance_order, smooth_concordance_order_anon, topological_concordance_order, topological_concordance_order_anon, ribbon, ribbon_anon, determinant, determinant_anon, seifert_matrix, seifert_matrix_anon, rasmussen_invariant, rasmussen_invariant_anon, ozsvath_szabo_tau_invariant, ozsvath_szabo_tau_invariant_anon, volume, volume_anon, maximum_cusp_volume, maximum_cusp_volume_anon, longitude_translation, longitude_translation_anon, meridian_translation, meridian_translation_anon, longitude_length, longitude_length_anon, meridian_length, meridian_length_anon, other_short_geodesics, other_short_geodesics_anon, symmetry_type, symmetry_type_anon, full_symmetry_group, full_symmetry_group_anon, chern_simons_invariant, chern_simons_invariant_anon, volume_imaginary_part, volume_imaginary_part_anon, arf_invariant, arf_invariant_anon, turaev_genus, turaev_genus_anon, signature_function, signature_function_anon, monodromy, monodromy_anon, small_large, small_large_anon, positive_braid, positive_braid_anon, positive, positive_anon, strongly_quasipositive, strongly_quasipositive_anon, quasipositive, quasipositive_anon, positive_braid_notation, positive_braid_notation_anon, positive_pd_notation, positive_pd_notation_anon, strongly_quasipositive_braid_notation, strongly_quasipositive_braid_notation_anon, quasipositive_braid_notation, quasipositive_braid_notation_anon, fd_clasp_number, fd_clasp_number_anon, width, width_anon, torsion_numbers, torsion_numbers_anon, td_clasp_number, td_clasp_number_anon, l_space, l_space_anon, nu, nu_anon, epsilon, epsilon_anon, quasi_alternating, quasi_alternating_anon, almost_alternating, almost_alternating_anon, adequate, adequate_anon, montesinos_notation, montesinos_notation_anon, boundary_slopes, boundary_slopes_anon, pretzel_notation, pretzel_notation_anon, double_slice_genus, double_slice_genus_anon, unknotting_number_algebraic, unknotting_number_algebraic_anon, khovanov_unreduced_integral_polynomial, khovanov_unreduced_integral_polynomial_anon, khovanov_unreduced_integral_vector, khovanov_unreduced_integral_vector_anon, khovanov_reduced_integral_polynomial, khovanov_reduced_integral_polynomial_anon, khovanov_reduced_integral_vector, khovanov_reduced_integral_vector_anon, khovanov_reduced_rational_polynomial, khovanov_reduced_rational_polynomial_anon, khovanov_reduced_rational_vector, khovanov_reduced_rational_vector_anon, khovanov_reduced_mod2_polynomial, khovanov_reduced_mod2_polynomial_anon, khovanov_reduced_mod2_vector, khovanov_reduced_mod2_vector_anon, khovanov_odd_integral_polynomial, khovanov_odd_integral_polynomial_anon, khovanov_odd_integral_vector, khovanov_odd_integral_vector_anon, khovanov_odd_mod2_polynomial, khovanov_odd_mod2_polynomial_anon, khovanov_odd_mod2_vector, khovanov_odd_mod2_vector_anon, khovanov_odd_rational_polynomial, khovanov_odd_rational_polynomial_anon, khovanov_odd_rational_vector, khovanov_odd_rational_vector_anon, hfk_polynomial, hfk_polynomial_anon, hfk_polynomial_vector, hfk_polynomial_vector_anon, mosaic_tile_number, mosaic_tile_number_anon, ropelength, ropelength_anon, homfly_polynomial, homfly_polynomial_anon, homfly_polynomial_vector, homfly_polynomial_vector_anon, grid_notation, grid_notation_anon, almost_strongly_qp, almost_strongly_qp_anon, almost_strongly_qp_braid, almost_strongly_qp_braid_anon, ribbon_number, ribbon_number_anon, geometric_type, geometric_type_anon, cosmetic_crossing, cosmetic_crossing_anon, q_polynomial, q_polynomial_anon.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import database_knotinfo as dk

records = dk.link_list()
print(f'RECORDS={len(records)}')
if records:
    print('FIELDS=' + ','.join(records[0].keys()))
```

Write the loader to use this package/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a website endpoint.
