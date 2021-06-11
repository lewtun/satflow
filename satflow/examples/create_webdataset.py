import satpy
import webdataset as wds
import rasterio
import numpy as np
import os
from datetime import datetime
from rasterio.windows import Window, from_bounds
from rasterio.warp import calculate_default_transform, reproject, Resampling
from satpy import Scene
from pyresample import load_area
from rasterio.plot import show

areas = load_area("/home/bieker/Development/satflow/satflow/examples/areas.yaml")
filenames = {"seviri_l1b_native": ["/run/media/bieker/Round1/EUMETSAT/2021/03/14/10/19/MSG3-SEVI-MSG15-0100-NA-20210314101915.098000000Z-NA.nat"]}
scene = Scene(filenames=filenames)
scene.load(('HRV',))
# By default resamples to 3km, as thats the native resolution of all bands other than HRV
scene = scene.resample(areas[0])
hrv_long, hrv_lat = scene['HRV'].attrs['area'].get_lonlats()
hrv_long = hrv_long[515:-641,603:]
hrv_lat = hrv_lat[515:-641,603:]
loc_x = np.cos(hrv_lat) * np.cos(hrv_long)
loc_y = np.cos(hrv_lat) * np.sin(hrv_long)
loc_z = np.sin(hrv_lat)

location_array = np.stack([loc_x, loc_y, loc_z], axis=-1)

# Create WebDataset with each shard being a single day and all the images for that day
eumetsat_dir = "/run/media/bieker/Round1/EUMETSAT/"

shard_num = 0
prev_datetime = datetime.now()
sink = wds.TarWriter(f"satflow-first.tar", compress=True)
topo_data = np.load("/home/bieker/Development/satflow/satflow/examples/cutdown_europe_dem.npy")
for root, dirs, files in os.walk(eumetsat_dir):
    # As its stored in year, month, day, hour, minute, format, once we are at the day level, create a new shard
    # Also cut down everything to only the square of all value data
    if files:
        # At lowest one, so have everything in it
        if len(files) < 11: # Not everything worked
            continue

        date_data = root.split("/")
        date_str = os.path.join(date_data[-5],date_data[-4],date_data[-3],date_data[-2],date_data[-1])
        datetime_object = datetime.strptime(date_str, "%Y/%m/%d/%H/%M")
        if prev_datetime.date() != datetime_object.date():
            # New shard
            sink.close()
            sink = wds.TarWriter(f"/run/media/bieker/data/EUMETSAT/satflow-{shard_num:05d}.tar", compress=True)
            shard_num += 1
            prev_datetime = datetime_object
        sample = {"__key__": datetime_object.strftime("%Y/%m/%d/%H/%M"),
                  "topo.npy": topo_data,
                  "location.npy": location_array,
                  }
        try:
            for f in files:
                if ".tif" in f:
                    # Only need geotiff ones
                    src = rasterio.open(os.path.join(root, f))
                    data = src.read(1)
                    cropped_data = data[515:-641,603:] # Done by handish to exclude all NODATA and invalid masks for clouds and images (clouds have a smaller extant)
                    channel = f.split("_")
                    if channel[0] in ["IR", "WV", "cloud"]:
                        channel = channel[0] + channel[1] # These are split across multiple
                    else:
                        channel = channel[0]
                    sample[channel + ".npy"] = cropped_data
            # Now all channels added to thing, write to shard
            sink.write(sample)
        except Exception as e:
            print(e)



