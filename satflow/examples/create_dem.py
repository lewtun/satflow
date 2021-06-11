import webdataset
import rasterio
from rasterio.merge import merge
from rasterio.plot import show
import glob
import os
from satpy import Scene
from pyresample import create_area_def
from pyresample import load_area


dem_path = "/home/bieker/bda/Bulk Order 20210611_041625/SRTM 1 Arc-Second Global/*.tif"
dem_files = glob.glob(dem_path)
import numpy as np

src_files_to_mosaic = []
for fp in dem_files:
    src = rasterio.open(fp)
    # src.astype(np.int8)
    src_files_to_mosaic.append(src)

areas = load_area("/home/bieker/Development/satflow/satflow/examples/areas.yaml")
for f in dem_files:
    scene = Scene(filenames={"generic_image": [f]})
    scene.load(["image"])
    scene = scene.resample(areas[0])
    fname = f.split("/")[-1]
    scene.save_datasets(
        writer="geotiff",
        base_dir="/run/media/bieker/T7/ResampledElevation/",
        filename=fname,
        enhance=False,
    )

dem_path = "/run/media/bieker/T7/ResampledElevation/*.tif"
dem_files = glob.glob(dem_path)
import numpy as np

src_files_to_mosaic = []
for fp in dem_files:
    src = rasterio.open(fp)
    # src.astype(np.int8)
    src_files_to_mosaic.append(src)
mosaic, out_trans = merge(src_files_to_mosaic, nodata=0, method="max")
print(mosaic.shape)
show(mosaic[0], cmap="terrain")
show(mosaic[0][515:-641, 603:], cmap="terrain")
out_meta = src.meta.copy()

out_meta.update(
    {
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "crs": "+proj=utm +zone=35 +ellps=WGS84 +units=m +no_defs ",
    }
)
out_fp = "europe_all_dem_3km_satproj.tif"
with rasterio.open(out_fp, "w", **out_meta) as dest:
    dest.write(mosaic)

out = rasterio.open(out_fp)
show(out, cmap="terrain")
# Save the numpy array, we don't care about other geotspatial transforms here
np.save("../resources/cutdown_europe_dem.npy", mosaic[0][515:-641, 603:])
np.save("europe_dem.npy", mosaic[0])
exit()

from tempfile import mkdtemp
import rasterio
from rasterio import Affine
from rasterio import windows
from rasterio.enums import Resampling
import math
import numpy as np
import os

INPUT_FILES = dem_files

sources = [rasterio.open(raster) for raster in INPUT_FILES]
print(sources[0].res)

# (left, bottom, right, top)
mosaic, out_trans = merge(src_files_to_mosaic, nodata=0, res=(0.03, 0.03))
print(mosaic.shape)
show(mosaic, cmap="terrain")
out_meta = src.meta.copy()

out_meta.update(
    {
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "crs": "+proj=utm +zone=35 +ellps=GRS80 +units=m +no_defs ",
    }
)
out_fp = "europe_all_dem_3km_cropbounds.tif"
with rasterio.open(out_fp, "w", **out_meta) as dest:
    dest.write(mosaic)

out = rasterio.open(out_fp)
show(out, cmap="terrain")
