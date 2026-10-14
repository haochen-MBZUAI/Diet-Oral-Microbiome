# Diet–oral microbiome analyses in the Human Phenotype Project

This repository contains the code used for the analyses in the manuscript "Population-scale dietary signatures of the oral microbiome".

## Data access

HPP data are accessible to researchers from universities and other research institutions through the [HPP data-access platform](https://humanphenotypeproject.org/data-access). Interested bona fide researchers should contact info@pheno.ai for access instructions. NHANES data are available from [CDC/NCHS](https://wwwn.cdc.gov/nchs/nhanes/).

## Repository structure

| Directory | Purpose |
| --- | --- |
| [diet_record_cleaning](diet_record_cleaning/) | Clean raw baseline-visit dietary records. |
| [cohort_and_feature_preprocessing](cohort_and_feature_preprocessing/) | Match the study cohort and prepare dietary features, covariates and oral microbial outcomes. |
| [dietary_score_definitions](dietary_score_definitions/) | Dietary score rules, thresholds and food-to-pattern mappings. |
| [alpha_diversity_analysis](alpha_diversity_analysis/) | Predict species richness and Shannon diversity; run permutation and SHAP analyses. |
| [species_abundance_analysis](species_abundance_analysis/) | Predict species abundances; run permutation and SHAP analyses. |
| [diet_microbiome_associations](diet_microbiome_associations/) | Estimate covariate-adjusted associations and compare dietary-pattern association profiles. |
| [functional_pathway_analysis](functional_pathway_analysis/) | Prepare and predict pathway abundances; run permutation and SHAP analyses. |
| [nhanes_external_replication](nhanes_external_replication/) | Construct the NHANES cohort and evaluate external replication. |

## Analysis entry points

### 1. Dietary records, cohort, covariates and oral microbial outcomes

- `diet_record_cleaning/clean_diet_logging_events.py`: cleaning of baseline-visit dietary records.
- `cohort_and_feature_preprocessing/select_lifestyle_oral_diet_mixdata.ipynb`: matching of dietary records and oral samples from the same baseline visit, and exclusion of recent oral antibiotic use.
- `cohort_and_feature_preprocessing/processing_diet_features.ipynb`: dietary features and the 13 dietary pattern scores, using `dietary_score_definitions/diet_score_config.py` and `dietary_score_definitions/supplementary2.csv`.
- `cohort_and_feature_preprocessing/processing_covariates.ipynb`: age, sex, body mass index, smoking status, soft-tissue inflammation level and periodontal damage level.
- `cohort_and_feature_preprocessing/processing_oral_species.ipynb`: baseline species profiles, species richness and Shannon diversity.

### 2. Oral alpha diversity

- `alpha_diversity_analysis/train_test.ipynb`: covariates-only and covariates-plus-diet models.
- `alpha_diversity_analysis/run_alpha_diversity_permutation_test.ipynb`: evaluate prediction significance.
- `alpha_diversity_analysis/run_alpha_diversity_shap.ipynb`: estimate feature contributions.

### 3. Oral species abundance

- `species_abundance_analysis/train_species_abundance.ipynb`: prevalence filtering, transformation and prediction models.
- `species_abundance_analysis/run_diet_oral_species_permutation_test.ipynb`: evaluate prediction significance.
- `species_abundance_analysis/train_species_abundance_shap.ipynb`: estimate feature contributions.

### 4. Dietary-pattern associations

- `diet_microbiome_associations/run_diet_pattern_oral_microbiome_associations.ipynb`: primary and extended covariate-adjusted models for species abundance, species richness and Shannon diversity.
- `diet_microbiome_associations/summarize_dietary_pattern_profiles.py`: association counts, profile similarity and opposing directions within genera.

### 5. Oral functional pathways

- `functional_pathway_analysis/run_diet_oral_pathway_model_input.ipynb`: prepare pathway model inputs.
- `functional_pathway_analysis/train_pathway_abundance.ipynb`: fit pathway prediction models.
- `functional_pathway_analysis/run_functional_pathway_permutation_test.ipynb`: evaluate prediction significance.
- `functional_pathway_analysis/run_functional_pathway_shap_analysis.ipynb`: estimate feature contributions.

### 6. External replication in NHANES

- `nhanes_external_replication/00_hpp_species_to_genus.py`: genera of significantly predicted HPP species.
- `nhanes_external_replication/01_build_nhanes_cohort.py`: harmonized dietary features, covariates and genus abundances.
- `nhanes_external_replication/02_nhanes_replication.py`: `eligibility`, `genus` and `pairwise` replication analyses.
- `nhanes_external_replication/abundance_preprocessing.py`: filter and transform genus abundances and retain raw detection indicators.

NHANES inputs are the public 2009–2010 and 2011–2012 files: demographics (DEMO), body measures (BMX), smoking (SMQ), oral health (OHQ), dietary recall totals and individual foods for both days (DR1TOT, DR2TOT, DR1IFF, DR2IFF), USDA Food Patterns Equivalents Database totals, and the NHANES Oral Microbiome Project DADA2RB and DADA2RSV genus-level relative abundances with taxonomy annotation. 

## License

This project is released under the MIT License; see [LICENSE](LICENSE).
