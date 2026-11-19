"""Helpers for downloading and opening World Ocean Atlas 2023 (WOA23) files.

WOA23 netCDF files are named ``woa23_[span]_[v][period]_[grid].nc``:

* ``span``   time span, e.g. ``decav`` (1955-2022 average of decades),
             ``decav91C0`` (1991-2020 normal), ``B5C2`` (2015-2022), ``all``
* ``v``      one-letter variable code (see ``VARIABLES``)
* ``period`` ``00`` annual, ``01``-``12`` monthly, ``13``-``16`` seasonal
             (Jan-Mar, Apr-Jun, Jul-Sep, Oct-Dec)
* ``grid``   ``01`` one-degree, ``04`` quarter-degree, ``5d`` five-degree

Example
-------
>>> from marine_navigation import woa
>>> ds = woa.open_woa("temperature", period="00")
>>> ds["t_an"].sel(depth=0).plot()
"""

from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

import xarray as xr

BASE_URL = "https://www.ncei.noaa.gov/data/oceans/woa/WOA23/DATA"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "woa23"

# folder name -> (one-letter file code, default time span, units, long name)
VARIABLES = {
    "temperature": ("t", "decav", "°C", "Sea water temperature"),
    "salinity": ("s", "decav", "PSS-78", "Practical salinity"),
    "oxygen": ("o", "all", "µmol/kg", "Dissolved oxygen"),
    "o2sat": ("O", "all", "%", "Oxygen saturation"),
    "AOU": ("A", "all", "µmol/kg", "Apparent oxygen utilization"),
    "nitrate": ("n", "all", "µmol/kg", "Nitrate"),
    "phosphate": ("p", "all", "µmol/kg", "Phosphate"),
    "silicate": ("i", "all", "µmol/kg", "Silicate"),
}

GRIDS = {"01": "1.00", "04": "0.25", "5d": "5.00"}


def filename(variable: str, period: str = "00", span: str | None = None, grid: str = "01") -> str:
    code, default_span, *_ = VARIABLES[variable]
    return f"woa23_{span or default_span}_{code}{period}_{grid}.nc"


def url(variable: str, period: str = "00", span: str | None = None, grid: str = "01") -> str:
    span = span or VARIABLES[variable][1]
    return f"{BASE_URL}/{variable}/netcdf/{span}/{GRIDS[grid]}/{filename(variable, period, span, grid)}"


def download(variable: str, period: str = "00", span: str | None = None, grid: str = "01",
             data_dir: Path = DATA_DIR, overwrite: bool = False) -> Path:
    """Download one WOA23 netCDF file (if not already present) and return its local path."""
    data_dir.mkdir(parents=True, exist_ok=True)
    target = data_dir / filename(variable, period, span, grid)
    if target.exists() and not overwrite:
        return target
    src = url(variable, period, span, grid)
    print(f"downloading {src}")
    tmp = target.with_suffix(".part")
    with urllib.request.urlopen(src, timeout=300) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)
    tmp.replace(target)
    return target


def open_woa(variable: str, period: str = "00", span: str | None = None, grid: str = "01",
             **kwargs) -> xr.Dataset:
    """Download (if needed) and open a WOA23 file with xarray.

    ``decode_times=False`` is used because WOA time is "months since ..." which
    the standard calendar decoder does not handle.
    """
    path = download(variable, period, span, grid)
    return xr.open_dataset(path, decode_times=False, **kwargs)
