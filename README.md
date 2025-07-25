# Global Landslide Detection for Rapid response (GLiDEr)

## Container

```bash
module load singularity
singularity build --sandbox /lscratch/jacaraba/container/glider docker://nasanccs/glider:v100
```

## Science Workflow

### Downloading Planet Data Workflow

```bash
TBD
```

### Training Workflow

```bash
TBD
```

### Validation Workflow

```bash
TBD
```

## Rapid Response Workflow

### Downloading Planet Data Workflow

```bash
TBD
```

### Inference Workflow

```bash
TBD
```

## Additional Workflows


### PlanetDownloader

This workflow is a **Python utility for searching, ordering, and downloading Planet imagery** (PlanetScope, RapidEye, etc.) using the official [Planet Python SDK](https://developers.planet.com/docs/apis/quickstart/). It is designed for batch downloading of large numbers of scenes and storing the search results as **GeoJSON** or **GPKG** metadata files.

---

#### How It Works

1. **Authentication**:  
   The class reads your Planet API key from the `PL_API_KEY` environment variable (or accepts it as an argument).

2. **Search**:  
   Uses `Planet.data.search()` with:
   - Geometry (from a shapefile or GeoJSON-like dictionary)
   - Date range
   - Cloud cover filter  
   Returns a list of matching scenes.

3. **Metadata Export**:  
   Saves all search results to a **GeoJSON** or **GPKG** file with all scene properties and geometry.

4. **Ordering**:  
   Automatically creates one or more **orders** using `order_request.build_request()` with the specified item type and product bundle. Orders are split into chunks of up to 500 scenes.

5. **Waiting**:  
   Blocks until each order finishes processing using `Planet.orders.wait()`.

6. **Download**:  
   Downloads each completed order as a single archive (zip/tar) to the configured directory.

---

#### Usage

We will replace the workflow with a CLI view of the module. In the meantime:

```bash
export PL_API_KEY="your_planet_api_key"
python planet_downloader.py
````

You will need to find this API from the Planet Explorer website using your
institutional email.

The `__main__` block includes an example that:

* Defines an AOI in **Utuado, Puerto Rico**
* Searches for **PlanetScope (PSScene)** imagery
* Downloads **analytic\_udm2** bundles for January 2020
* Saves metadata to `planet_downloads/metadata-<timestamp>.geojson`

#### Parameters

##### **PlanetDownloader**

```python
downloader = PlanetDownloader(
    api_key=None,                      # Defaults to PL_API_KEY env var
    download_dir="./planet_downloads"  # Where to save orders & metadata
)
```

#### **search()**

```python
features = downloader.search(
    geometry_info,         # Shapefile path OR GeoJSON-like dict
    start_date,            # "YYYY-MM-DD"
    end_date,              # "YYYY-MM-DD"
    item_type=["PSScene"], # List of item types
    cloud_cover=0.2        # Max cloud cover (0–1)
)
```

#### **download()**

```python
downloader.download(
    geometry_info,                 # Shapefile path or GeoJSON-like dict
    start_date,                    # "YYYY-MM-DD"
    end_date,                      # "YYYY-MM-DD"
    item_types=["PSScene"],        # Valid types: see below
    bundles=["analytic_udm2"],     # Valid bundles: see below
    cloud_cover=0.2,               # Max allowed cloud cover
    threads=4,                     # Parallel download threads
    overwrite=False,               # Overwrite existing files
    progress_bar=True              # Show download progress
)
```

---

#### Supported Item Types

When **ordering**, the `item_type` must be one of:

* `PSScene` – PlanetScope scenes
* `REScene` – RapidEye scenes
* `REOrthoTile` – RapidEye orthorectified tiles
* `SkySatScene` – SkySat scenes
* `SkySatCollect` – SkySat image strips
* `SkySatVideo` – SkySat videos
* `PelicanScene` – Pelican imagery
* `TanagerScene` – Tanager hyperspectral
* `TanagerMethane` – Tanager methane sensing

> **Note:**
> For **searching**, you can also use more specific types like `PSScene4Band`, but they must be normalized to these values when ordering.

---

#### Supported Bundles

The `bundle` defines which asset combination you get. Examples for PlanetScope (`PSScene`):

* `analytic_udm2` – 4-band analytic surface reflectance + usable data mask
* `analytic_3b_udm2` – 3-band (RGB) + UDM2
* `analytic_8b_udm2` – 8-band reflectance + UDM2
* `analytic_sr_udm2` – 4-band **surface reflectance** + UDM2
* `analytic_8b_sr_udm2` – 8-band **surface reflectance** + UDM2
* `visual` – Visual RGB only
* `basic_analytic_udm2` – Non-orthorectified 4-band + UDM2
* `basic_analytic_8b_udm2` – Non-orthorectified 8-band + UDM2

> **If you pass an invalid combination**, the SDK will raise:
> `planet.specs.SpecificationException: bundle`

---

### Outputs

* **Imagery orders**: Downloaded as zip/tar archives to the `download_dir`.
* **Metadata**: Written as timestamped **GeoJSON** or **GPKG** files with all scene properties and footprints.

---

### Next Steps

* **Add CLI view of the request**:
  Support CLI view in a pipeline file.
* **Add more filters**:
  Support for `view_angle`, `gsd`, `sun_elevation`, etc.
* **Pre/Post-event mode**:
  Auto-fetch imagery relative to a disaster/event date.
* **Async pipeline**:
  Use `StateBar` and async APIs for non-blocking order creation and progress visualization.
* **Automatic item\_type mapping**:
  Map search-specific types (e.g., `PSScene4Band`) to canonical order types (`PSScene`).
* **Auto-retry on failed orders**:
  Re-submit or adjust orders if they fail.
