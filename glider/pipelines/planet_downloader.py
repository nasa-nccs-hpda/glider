import os
import sys
import logging
import geopandas as gpd

from datetime import datetime
from shapely.geometry import shape
from shapely.geometry import mapping

from planet import Planet
from planet import data_filter
from planet import order_request


class PlanetDownloader:

    MAX_ITEMS_PER_ORDER = 500
    POLL_INTERVAL = 30

    def __init__(
                self,
                api_key: str = None,
                download_dir: str = "./planet_downloads"
            ):

        # Prefer environment variable if api_key not provided
        self.api_key = api_key or os.getenv("PL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Planet API key not provided. Set PL_API_KEY" +
                "env var or pass api_key to PlanetDownloader()."
            )
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        logging.info(f'Created {self.download_dir} directory.')

        self.pl_session = Planet()  # automatically detects PL_API_KEY
        logging.info("Initialized PlanetDownloader using official SDK.")

    def _create_order(
                self,
                item_ids,
                item_type="PSScene",
                bundle="analytic_sr"
            ):
        """
        Create an order using the Planet SDK (synchronous high-level API).
        """
        order_req = order_request.build_request(
            name="planet_download_order",
            products=[
                order_request.product(
                    item_ids=item_ids,
                    item_type=item_type,
                    product_bundle=bundle
                )
            ],
            delivery=order_request.delivery(single_archive=True)
        )
        order = self.pl_session.orders.create_order(order_req)
        logging.info(f"Created order: {order['id']}")
        return order['id']

    def _load_aoi(self, geometry_info: str):
        if isinstance(geometry_info, str):
            gdf = gpd.read_file(geometry_info)
            return mapping(gdf.unary_union)
        else:
            return geometry_info

    def _write_metadata(self, metadata, driver="GeoJSON"):
        """
        Writes Planet metadata to a geospatial file (GeoJSON or GPKG).
        - metadata: list of Planet API feature dicts
        - bundle: product bundle name
        - driver: "GeoJSON" or "GPKG"
        """
        # Build output path with timestamp
        ext = "geojson" if driver == "GeoJSON" else "gpkg"
        out_path = os.path.join(
            self.download_dir,
            f'metadata-{datetime.now().strftime("%Y%m%d_%H%M%S")}.{ext}'
        )

        # Convert features to GeoDataFrame
        records = []
        for item in metadata:
            props = item.get("properties", {})
            props["id"] = item.get("id")
            geom = shape(item.get("geometry"))
            records.append({**props, "geometry": geom})

        gdf = gpd.GeoDataFrame(
            records, geometry="geometry", crs="EPSG:4326")

        # Write to GeoJSON or GPKG
        gdf.to_file(out_path, driver=driver)
        logging.info(f"Metadata written to {out_path}")
        return

    def search(
                self,
                geometry_info: str,
                start_date: str,
                end_date: str,
                item_type: list = ["PSScene"],
                cloud_cover: float = 0.2
            ):

        # setup aoi
        aoi = self._load_aoi(geometry_info)

        # convert string to datetime
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # produce filter attribute
        # TODO: we can add a lot more filters here
        # angles, additional metadata, etc.
        sfilter = data_filter.and_filter([
            data_filter.permission_filter(),
            data_filter.date_range_filter(
                'acquired',
                gte=start_date,
                lte=end_date
            ),
            data_filter.range_filter(
                'cloud_cover',
                lte=cloud_cover
            ),
        ])

        # search features from request
        features = list(
            self.pl_session.data.search(
                item_type,
                geometry=aoi,
                search_filter=sfilter,
            )
        )
        logging.info(f"Found {len(features)} images.")
        return features

    def _chunk_list(self, lst: list, chunk_size: int):
        for i in range(0, len(lst), chunk_size):
            yield lst[i: i + chunk_size]

    def download(
                self,
                geometry_info: str,
                start_date: str,
                end_date: str,
                item_types: list = ["PSScene"],
                bundles: list = ["analytic_sr"],
                cloud_cover: float = 0.2,
                threads: int = 4,
                overwrite: bool = False,
                progress_bar: bool = True
            ):

        logging.info('Starting download process...')

        # search for possible id's based on request
        items = self.search(
            geometry_info,
            start_date,
            end_date,
            item_types,
            cloud_cover
        )

        # make sure we have hits of data
        if not items:
            sys.exit("No images found. Make filters more flexible.")
            return

        # get the imagery id's
        item_ids = [i["id"] for i in items]

        # write metadata and store with search
        self._write_metadata(items)

        # iterate over each request
        for chunk in self._chunk_list(item_ids, self.MAX_ITEMS_PER_ORDER):

            for item_type in item_types:

                for bundle in bundles:

                    # create order
                    order_id = self._create_order(
                        chunk, item_type, bundle)

                    # wait for the order to be ready
                    # note: this may take several minutes.
                    self.pl_session.orders.wait(order_id)

                    # download the scenes
                    self.pl_session.orders.download_order(
                        order_id,
                        directory=self.download_dir,
                        overwrite=overwrite,
                        progress_bar=progress_bar
                    )
        return


if __name__ == '__main__':

    # Setup logging
    logging.basicConfig(
        level='INFO',
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # define downloader class
    downloader = PlanetDownloader(
        download_dir=(
            '/explore/nobackup/projects/ilab/projects'
            '/GLiDEr/data/planet'
        )
    )

    # setting up dummy geometry
    # located in Utuado, Puerto Rico
    geom = {
        "coordinates": [
            [
                [
                    -66.7300,
                    18.3000
                ],
                [
                    -66.7300,
                    18.2500
                ],
                [
                    -66.6500,
                    18.2500
                ],
                [
                    -66.6500,
                    18.3000
                ],
                [
                    -66.7300,
                    18.3000
                ]
            ]
        ],
        "type": "Polygon"
    }

    # planet.specs.SpecificationException: item_type
    # 'SkySatScene', 'PelicanScene', 'TanagerMethane', 'SkySatVideo',
    # 'TanagerScene', 'REScene', 'SkySatCollect', 'PSScene', 'REOrthoTile'.

    # planet.specs.SpecificationException: bundle
    # 'analytic_udm2', 'analytic_3b_udm2', 'analytic_8b_udm2', 'visual',
    # 'basic_analytic_udm2', 'basic_analytic_8b_udm2',
    # 'analytic_sr_udm2', 'analytic_8b_sr_udm2'.

    # Download PlanetScope images (3m SR)
    downloader.download(
        geometry_info=geom,
        start_date="2020-01-01",
        end_date="2020-02-01",
        item_types=["PSScene"],
        bundles=["analytic_udm2"],
        cloud_cover=0.2,
        threads=6
    )
