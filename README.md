# combine_ttX_analysis

Utilities to run statistical inference for the BSM tt+X analysis with Combine and CombineHarvester.

## Requirements

- CMSSW_14_1_0_pre4
- Combine v10.0.2 and CombineHarvester
- Python 3
- ROOT with PyROOT

Setup instructions are available in the Combine docs:  
https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/#standalone-compilation-with-conda

## Data inputs

By default, shape templates are read from `/afs/desy.de/user/g/gmilella/public/combine_inputs`

## Quick start

Create datacards, produce workspaces, then run the desired statistical tests.

### 1) Datacard creation

Per year:
```
python3 data_cards_creation.py --year YEAR --output_dir OUTPUT_DIR
```

This creates OUTPUT_DIR/YEAR/ with datacards. Use labels "all_years_Run2" or "all_years_Run3" for direct combinations.
In case the combination of Run 2 and 3 is needed: 
```
python3 data_cards_combine_years_template.py --input_dir INPUT_DIR
```

To create the workspaces:
```
python3 workspace_creation.py --input_dir INPUT_DIR
```

INPUT_DIR must contain the datacards from step 1 or 2

### 2) Running analyses

Mass and width grids, and analysis parameters, are defined inside each script.

- Impacts and pulls

`python3 pulls_plot_creation.py --input_dir INPUT_DIR`

- Goodness of fit

`python3 goodness_of_fit_test.py --input_dir INPUT_DIR`

- Limits

`python3 combine_limit_calculation.py --input_dir INPUT_DIR`

- Prefit and postfit distributions

`python3 prefit_postfit_plot.py --input_dir INPUT_DIR`
