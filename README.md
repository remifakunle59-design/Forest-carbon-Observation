# Forest-carbon-Observation: EO Harmonization for Terrestrial Carbon Modeling

**Author:** Remilekun Eunice Atobatele  
**Focus:** Earth Observation (EO) Harmonization for Terrestrial Carbon Modeling (EUFOR-G3W / FLUXCOM-X)

## Overview
Atmospheric inversion models and empirical flux upscaling systems (such as FLUXCOM-X) operate at coarse spatial grids (typically 0.05° to 0.25°), while satellite remote sensing sensors observe forest cover, disturbances, and biomass at fine resolutions (10 m to 30 m). A simple pixel downsampling discards crucial sub-grid heterogeneity.

This repository provides a reproducible Python workflow using `xarray` and `rioxarray` to:
1. Ingest high-resolution Earth Observation forest biomass rasters.
2. Calculate spatial sub-grid metrics (mean biomass density, spatial standard deviation, and forest cover fraction).
3. Export standardized, Climate and Forecast (CF-1.8) compliant NetCDF files ready for Earth system model ingestion.

## Pipeline Architecture
- **Input:** High-resolution GeoTIFF satellite raster (Sentinel-2 / biomass proxy).
- **Core Processing:** `rioxarray` reprojection and sub-grid statistical aggregation preserving variance.
- **Output:** CF-1.8 compliant NetCDF-4 (`biomass_carbon_mean`, `biomass_carbon_std`, `forest_fraction`).

## Requirements & Setup
```bash
git clone [https://github.com/remifakunle59-design/Forest-carbon-Observation.git](https://github.com/remifakunle59-design/Forest-carbon-Observation.git)
cd Forest-carbon-Observation
pip install -r requirements.txt
