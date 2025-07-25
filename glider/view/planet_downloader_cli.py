import sys
import time
import logging
import argparse

from glider.pipelines.planet_downloader import PlanetDownloader


def main():
    # CLI argument parsing
    desc = 'Search, order, and download Planet data using the Python SDK.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument(
        '-a', '--aoi',
        type=str,
        required=True,
        dest='aoi',
        help='AOI file path (GeoJSON/Shapefile) or raw GeoJSON string.')

    parser.add_argument(
        '-sd', '--start-date',
        type=str,
        required=True,
        dest='start_date',
        help='Start date (YYYY-MM-DD).')

    parser.add_argument(
        '-ed', '--end-date',
        type=str,
        required=True,
        dest='end_date',
        help='End date (YYYY-MM-DD).')

    parser.add_argument(
        '-it', '--item-types',
        type=str,
        nargs='+',
        required=False,
        default=['PSScene'],
        dest='item_types',
        help='Item types to search/order (e.g., PSScene, REScene).')

    parser.add_argument(
        '-b', '--bundles',
        type=str,
        nargs='+',
        required=False,
        default=['analytic_udm2'],
        dest='bundles',
        help='Product bundles (e.g., analytic_udm2, analytic_sr_udm2).')

    parser.add_argument(
        '-cc', '--cloud-cover',
        type=float,
        required=False,
        default=0.2,
        dest='cloud_cover',
        help='Max cloud cover (0–1).')

    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        required=False,
        default='./planet_downloads',
        dest='output_dir',
        help='Directory to save downloaded imagery and metadata.')

    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing downloads.')

    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar.')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level='INFO',
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Timer
    timer = time.time()

    # Run downloader
    downloader = PlanetDownloader(download_dir=args.output_dir)
    downloader.download(
        geometry_info=args.aoi,
        start_date=args.start_date,
        end_date=args.end_date,
        item_types=args.item_types,
        bundles=args.bundles,
        cloud_cover=args.cloud_cover,
        overwrite=args.overwrite,
        progress_bar=not args.no_progress
    )

    logging.info(
        f"Process completed in {(time.time() - timer)/60:.2f} minutes.")


if __name__ == "__main__":

    sys.exit(main())
