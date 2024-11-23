# CarbonSet README
This repo contains all the python scripts we used to generate processed plots and CSVs.

## Folder format

**dataset/**: Contains the base dataset we used.

**src/**: Python notebooks to process the dataset

**plots/**: Contains generated plots.

**flagships_analysis/**: Our analysis on the CFP trend of selected flagship processors every year.


## Probabilistic Sequence Generation

All probability distributions are based on referenced tech reports. The `sample_size` is tunable, but the resultant CFP values will not be significantly changed.

### Reminder

We recommend using a larger sample size when generating the parameter sequences for your CFP calculation. However, for later probabilistic parameter sweeps, we will sweep the parameters of Defective Density, GAP, EPA, and Carbon Intensity, each with `sample_size`.

To model N processors, we will have a problem size of N x `sample_size`^4 in total.

## Contributing

Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

