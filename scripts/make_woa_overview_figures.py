"""Generate the figures used in docs/worldoceanatlas/.

Run from the project root:

    uv run python scripts/make_woa_overview_figures.py

Data files are downloaded on first use into data/raw/woa23/.
"""

from __future__ import annotations

from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmocean
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.colors import LogNorm

from marine_navigation import woa

OUT = Path(__file__).resolve().parents[1] / "docs" / "worldoceanatlas" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ---- style: recessive axes, text in neutral inks -------------------------------
TEXT = "#0b0b0b"
TEXT2 = "#52514e"
GRID = "#d9d8d3"
LAND = "#d4d3cf"
NODATA = "#a9a8a3"  # ocean cells without a value (below seafloor, no observations)
STATION_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]  # categorical slots 1-3

mpl.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.titlecolor": TEXT,
    "axes.labelcolor": TEXT2,
    "axes.edgecolor": GRID,
    "xtick.color": TEXT2,
    "ytick.color": TEXT2,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 2,
})

PROJ = ccrs.Robinson(central_longitude=-160)
PC = ccrs.PlateCarree()


def load(variable, period="00", span=None):
    return woa.open_woa(variable, period=period, span=span).isel(time=0)


def map_axes(fig, pos):
    ax = fig.add_subplot(*pos, projection=PROJ)
    ax.set_global()
    ax.add_feature(cfeature.OCEAN, facecolor=NODATA, edgecolor="none", zorder=0)
    ax.add_feature(cfeature.LAND, facecolor=LAND, edgecolor="none", zorder=2)
    ax.coastlines(linewidth=0.3, color="#9a9994", zorder=3)
    ax.spines["geo"].set_edgecolor(GRID)
    return ax


def draw_map(ax, da, cmap, title, units, vmin=None, vmax=None, norm=None, extend="both"):
    m = ax.pcolormesh(da.lon, da.lat, da, transform=PC, cmap=cmap, shading="auto",
                      vmin=None if norm else vmin, vmax=None if norm else vmax, norm=norm,
                      rasterized=True)
    ax.set_title(title, loc="left")
    cb = plt.colorbar(m, ax=ax, orientation="horizontal", pad=0.04, fraction=0.05,
                      aspect=35, extend=extend)
    cb.set_label(units, color=TEXT2)
    cb.outline.set_edgecolor(GRID)
    return m


def save(fig, name):
    fig.savefig(OUT / name)
    plt.close(fig)
    print("wrote", OUT / name)


# ---- 1. the six measured variables at the surface ---------------------------
def fig_surface_variables():
    specs = [
        ("temperature", "t_an", cmocean.cm.thermal, "Temperature", "°C", -2, 30),
        ("salinity", "s_an", cmocean.cm.haline, "Salinity", "PSS-78", 32, 38),
        ("oxygen", "o_an", cmocean.cm.tempo, "Dissolved oxygen", "µmol/kg", 180, 380),
        ("nitrate", "n_an", cmocean.cm.matter, "Nitrate", "µmol/kg", 0, 30),
        ("phosphate", "p_an", cmocean.cm.amp, "Phosphate", "µmol/kg", 0, 2),
        ("silicate", "i_an", cmocean.cm.turbid, "Silicate", "µmol/kg", 0, 60),
    ]
    fig = plt.figure(figsize=(11, 10))
    fig.subplots_adjust(hspace=0.32)
    for i, (var, field, cmap, title, units, lo, hi) in enumerate(specs):
        ds = load(var)
        ax = map_axes(fig, (3, 2, i + 1))
        draw_map(ax, ds[field].sel(depth=0), cmap, f"{title} · surface", units, lo, hi)
    fig.suptitle("WOA23 annual climatology at the sea surface (1° grid)", x=0.02, ha="left",
                 fontsize=12, fontweight="bold", color=TEXT)
    save(fig, "surface_variables.png")


# ---- 2. temperature at four depths --------------------------------------------
def fig_temperature_depths():
    ds = load("temperature")
    depths = [(0, -2, 30), (200, -2, 25), (1000, -1, 12), (4000, -1, 4)]
    fig = plt.figure(figsize=(11, 7))
    fig.subplots_adjust(hspace=0.32)
    for i, (d, lo, hi) in enumerate(depths):
        ax = map_axes(fig, (2, 2, i + 1))
        draw_map(ax, ds.t_an.sel(depth=d), cmocean.cm.thermal, f"Temperature · {d} m", "°C", lo, hi)
    fig.suptitle("The same variable looks very different with depth (note each panel's own scale)",
                 x=0.02, ha="left", fontsize=12, fontweight="bold", color=TEXT)
    save(fig, "temperature_depths.png")


# ---- 3. vertical profiles at three contrasting locations ----------------------
STATIONS = [
    ("Sargasso Sea (31.5°N, 64.5°W)", 31.5, -64.5),
    ("Eastern tropical Pacific (12.5°N, 110.5°W)", 12.5, -110.5),
    ("Southern Ocean (60.5°S, 0.5°E)", -60.5, 0.5),
]


def fig_profiles():
    specs = [("temperature", "t_an", "Temperature (°C)"), ("salinity", "s_an", "Salinity"),
             ("oxygen", "o_an", "Oxygen (µmol/kg)"), ("nitrate", "n_an", "Nitrate (µmol/kg)")]
    fig, axes = plt.subplots(1, 4, figsize=(11, 5), sharey=True)
    for ax, (var, field, label) in zip(axes, specs):
        ds = load(var)
        for (name, lat, lon), c in zip(STATIONS, STATION_COLORS):
            prof = ds[field].sel(lat=lat, lon=lon, method="nearest")
            ax.plot(prof, prof.depth, color=c, label=name)
        ax.set_xlabel(label)
    axes[0].set_ylabel("Depth (m)")
    axes[0].set_ylim(5500, 0)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("Vertical profiles at three contrasting locations (annual climatology)",
                 x=0.02, ha="left", fontsize=12, fontweight="bold", color=TEXT)
    save(fig, "profiles.png")


# ---- 4. a north-south section through the Atlantic ----------------------------
def fig_atlantic_section():
    lon = -25.5
    specs = [("temperature", "t_an", cmocean.cm.thermal, "Temperature", "°C", -1, 28),
             ("salinity", "s_an", cmocean.cm.haline, "Salinity", "PSS-78", 34, 37.2),
             ("oxygen", "o_an", cmocean.cm.tempo, "Dissolved oxygen", "µmol/kg", 50, 350)]
    fig, axes = plt.subplots(3, 1, figsize=(11, 8.5), sharex=True)
    for ax, (var, field, cmap, title, units, lo, hi) in zip(axes, specs):
        sec = load(var)[field].sel(lon=lon, method="nearest").sel(lat=slice(-75, 65))
        m = ax.pcolormesh(sec.lat, sec.depth, sec, cmap=cmap, vmin=lo, vmax=hi, shading="auto",
                          rasterized=True)
        ax.set_facecolor(NODATA)
        ax.set_ylim(5500, 0)
        ax.set_ylabel("Depth (m)")
        ax.set_title(f"{title} along 25.5°W", loc="left")
        ax.grid(False)
        cb = plt.colorbar(m, ax=ax, pad=0.01, extend="both")
        cb.set_label(units, color=TEXT2)
        cb.outline.set_edgecolor(GRID)
    axes[-1].set_xlabel("Latitude (°N)")
    fig.suptitle("A north–south section of the Atlantic: water masses are visible as tongues",
                 x=0.02, ha="left", fontsize=12, fontweight="bold", color=TEXT)
    save(fig, "atlantic_section.png")


# ---- 5. seasonal cycle: summer minus winter -----------------------------------
def fig_seasonal():
    jfm = load("temperature", "13").t_an.sel(depth=0)
    jas = load("temperature", "15").t_an.sel(depth=0)
    fig = plt.figure(figsize=(9, 5))
    ax = map_axes(fig, (1, 1, 1))
    draw_map(ax, jas - jfm, cmocean.cm.balance, "Sea surface temperature: Jul–Sep minus Jan–Mar",
             "°C (red = warmer in Jul–Sep)", -10, 10)
    save(fig, "seasonal_sst_difference.png")


# ---- 6. decadal change -----------------------------------------------------------
def fig_decadal():
    early = load("temperature", span="5564").t_an.sel(depth=0)
    late = load("temperature", span="B5C2").t_an.sel(depth=0)
    fig = plt.figure(figsize=(9, 5))
    ax = map_axes(fig, (1, 1, 1))
    draw_map(ax, late - early, cmocean.cm.balance,
             "Sea surface temperature: 2015–2022 minus 1955–1964", "°C", -2, 2)
    save(fig, "decadal_sst_change.png")


# ---- 7. data coverage ------------------------------------------------------------
def fig_coverage():
    t = load("temperature")
    o = load("oxygen")
    fig = plt.figure(figsize=(11, 3.4))
    for i, (da, title) in enumerate([(t.t_dd.sel(depth=0), "Temperature observations · surface"),
                                     (o.o_dd.sel(depth=0), "Oxygen observations · surface")]):
        ax = map_axes(fig, (1, 2, i + 1))
        da = da.where(da > 0)
        draw_map(ax, da, cmocean.cm.dense, title, "number of observations per 1° cell (log)",
                 norm=LogNorm(1, 1e4), extend="max")
    fig.suptitle("How many measurements stand behind each grid cell (the *_dd field)",
                 x=0.02, ha="left", fontsize=12, fontweight="bold", color=TEXT)
    save(fig, "coverage.png")


# ---- 8. preview of navigation-relevant analysis: horizontal gradients --------
def horizontal_gradient(da):
    """Magnitude of the horizontal gradient in units per 100 km on a regular lat/lon grid."""
    r = 6371.0
    lat = np.deg2rad(da.lat.values)
    dy = np.deg2rad(1.0) * r  # km per 1° lat
    dx = dy * np.cos(lat)[:, None]
    gy, gx = np.gradient(da.values, axis=(0, 1))
    g = np.hypot(gx / dx, gy / dy) * 100
    return xr.DataArray(g, coords=da.coords, dims=da.dims)


def fig_gradients():
    t = load("temperature").t_an.sel(depth=0)
    s = load("salinity").s_an.sel(depth=0)
    fig = plt.figure(figsize=(11, 3.6))
    ax = map_axes(fig, (1, 2, 1))
    draw_map(ax, horizontal_gradient(t), cmocean.cm.amp, "Temperature gradient · surface",
             "°C per 100 km", 0, 1.5, extend="max")
    ax = map_axes(fig, (1, 2, 2))
    draw_map(ax, horizontal_gradient(s), cmocean.cm.amp, "Salinity gradient · surface",
             "PSS-78 per 100 km", 0, 0.3, extend="max")
    fig.suptitle("Where do properties change fastest? Fronts as potential navigation cues",
                 x=0.02, ha="left", fontsize=12, fontweight="bold", color=TEXT)
    save(fig, "surface_gradients.png")


if __name__ == "__main__":
    fig_surface_variables()
    fig_temperature_depths()
    fig_profiles()
    fig_atlantic_section()
    fig_seasonal()
    fig_decadal()
    fig_coverage()
    fig_gradients()
