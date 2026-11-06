"""
Forest Carbon EO Aggregator for Earth System Models (EUFOR-G3W Pipeline)
Author: Remilekun Eunice Atobatele
Description:
    Processes high-resolution Earth Observation forest metrics (e.g., above-ground biomass,
    canopy height, disturbance) and upscales them to climate model-ready gridded NetCDF format
    (e.g., 0.05° or 0.25° resolution) while preserving sub-grid heterogeneity (mean, standard
    deviation, and forest fraction) in compliance with CF-1.8 metadata conventions.
"""

import os
import numpy as np
import xarray as xr
import rioxarray
from rasterio.enums import Resampling


def generate_synthetic_eo_raster(
    output_path: str = "sample_forest_biomass_10m.tif",
    width: int = 2000,
    height: int = 2000,
) -> str:
    """Generates a synthetic high-resolution GeoTIFF representing forest biomass (Mg C / ha)."""
    print(f"Generating synthetic high-resolution EO biomass dataset: {output_path}...")
    np.random.seed(42)

    x = np.linspace(0, 10, width)
    y = np.linspace(0, 10, height)
    xx, yy = np.meshgrid(x, y)
    
    biomass = (
        50 * np.sin(xx / 2) * np.cos(yy / 2)
        + 80
        + np.random.normal(0, 15, (height, width))
    )
    biomass[biomass < 45] = 0.0
    biomass = np.clip(biomass, 0, 250).astype(np.float32)

    lons = np.linspace(13.0, 13.5, width)
    lats = np.linspace(52.5, 52.0, height)

    da = xr.DataArray(
        biomass[np.newaxis, :, :],
        dims=["band", "y", "x"],
        coords={"band": [1], "y": lats, "x": lons},
        name="biomass_density",
    )
    da.rio.write_crs("EPSG:4326", inplace=True)
    da.rio.to_raster(output_path, driver="GTiff", dtype="float32")
    print(f"Synthetic raster created at {output_path} (CRS: EPSG:4326).")
    return output_path


def upscale_eo_to_model_grid(
    input_geotiff: str,
    target_res_deg: float = 0.05,
    output_netcdf: str = "model_ready_forest_carbon.nc",
) -> xr.Dataset:
    """
    Upscales high-resolution EO raster to coarse climate model grid.
    Computes sub-grid statistics:
      1. Mean biomass density (Mg C / ha)
      2. Sub-grid spatial variability (biomass standard deviation)
      3. Forest area fraction (pixels with biomass > 0)
    """
    print(f"Opening high-resolution raster: {input_geotiff}...")
    da = rioxarray.open_rasterio(input_geotiff, masked=True).squeeze()

    min_x, min_y, max_x, max_y = da.rio.bounds()
    target_lons = np.arange(min_x, max_x, target_res_deg)
    target_lats = np.arange(min_y, max_y, target_res_deg)

    print(f"Upscaling from native resolution to target model grid ({target_res_deg}°)...")

    # 1. Mean Biomass
    mean_biomass = da.rio.reproject(
        dst_crs="EPSG:4326",
        resolution=target_res_deg,
        resampling=Resampling.average,
    )

    # 2. Forest Cover Fraction
    forest_mask = (da > 0).astype(np.float32)
    forest_mask.rio.write_nodata(np.nan, inplace=True)
    forest_fraction = forest_mask.rio.reproject(
        dst_crs="EPSG:4326",
        resolution=target_res_deg,
        resampling=Resampling.average,
    )

    # 3. Sub-grid Standard Deviation
    da_sq = (da ** 2)
    mean_sq = da_sq.rio.reproject(
        dst_crs="EPSG:4326",
        resolution=target_res_deg,
        resampling=Resampling.average,
    )
    variance = np.maximum(mean_sq - (mean_biomass ** 2), 0)
    std_biomass = np.sqrt(variance)

    ds = xr.Dataset(
        data_vars={
            "biomass_carbon_mean": (
                ["lat", "lon"],
                mean_biomass.values,
                {
                    "standard_name": "aboveground_forest_biomass_carbon_density",
                    "long_name": "Grid-cell mean forest aboveground biomass carbon density",
                    "units": "Mg C ha-1",
                    "_FillValue": -9999.0,
                },
            ),
            "biomass_carbon_std": (
                ["lat", "lon"],
                std_biomass.values,
                {
                    "long_name": "Sub-grid standard deviation of biomass carbon density",
                    "units": "Mg C ha-1",
                    "_FillValue": -9999.0,
                },
            ),
            "forest_fraction": (
                ["lat", "lon"],
                forest_fraction.values,
                {
                    "standard_name": "forest_area_fraction",
                    "long_name": "Fraction of grid cell classified as vegetative/forest cover",
                    "units": "1",
                    "valid_range": [0.0, 1.0],
                    "_FillValue": -9999.0,
                },
            ),
        },
        coords={
            "lat": (
                ["lat"],
                mean_biomass.y.values,
                {"standard_name": "latitude", "units": "degrees_north"},
            ),
            "lon": (
                ["lon"],
                mean_biomass.x.values,
                {"standard_name": "longitude", "units": "degrees_east"},
            ),
        },
        attrs={
            "title": "Model-Ready Harmonized Forest Carbon Product (EUFOR-G3W Pipeline)",
            "institution": "GFZ Helmholtz Centre for Geosciences / WUR",
            "creator_name": "Remilekun Eunice Atobatele",
            "Conventions": "CF-1.8",
            "source": "High-resolution Earth Observation upscaling via rioxarray and xarray",
            "comment": "Prepares EO priors for FLUXCOM-X empirical flux upscaling and atmospheric inversions.",
        },
    )

    ds.to_netcdf(output_netcdf, format="NETCDF4")
    print(f"Successfully generated model-ready NetCDF: {output_netcdf}")
    return ds


if __name__ == "__main__":
    test_geotiff = "sample_forest_biomass_10m.tif"
    
    if not os.path.exists(test_geotiff):
        generate_synthetic_eo_raster(test_geotiff)

    out_nc = "model_ready_forest_carbon.nc"
    dataset = upscale_eo_to_model_grid(test_geotiff, target_res_deg=0.05, output_netcdf=out_nc)
    print("\nUpscaled Dataset Summary:")
    print(dataset)

