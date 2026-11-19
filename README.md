# marine_navigation

Exploring the environmental cues that marine organisms may use for navigation.

## First task: World Ocean Atlas

Analyze the [World Ocean Atlas](https://www.ncei.noaa.gov/products/world-ocean-atlas) (NOAA NCEI) climatologies (temperature, salinity, oxygen, nutrients, etc.) to see how these fields vary in space and with depth, and whether any of them could act as navigational cues.

An overview of the atlas (contents, how to use it, figures) is in
[docs/worldoceanatlas/](docs/worldoceanatlas/index.html). Download and open files with:

```python
from marine_navigation import woa
ds = woa.open_woa("temperature", period="00")   # cached in data/raw/woa23/
```

## Layout

```
data/raw/        downloaded source data (not tracked by git)
data/processed/  derived datasets (not tracked by git)
notebooks/       exploratory Jupyter notebooks
src/marine_navigation/  reusable analysis code
figures/         output plots
scripts/         runnable scripts (e.g. figure generation)
docs/            HTML documentation
```

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync                  # creates .venv and installs dependencies
uv run jupyter lab       # start JupyterLab
uv add <package>         # add a new dependency
```
