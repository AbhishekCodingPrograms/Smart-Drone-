"""
Download a dataset from Kaggle into the project `data/` folder.

Usage:
  - Place your Kaggle API token (kaggle.json) under %USERPROFILE%/.kaggle/kaggle.json
    (Windows) or ~/.kaggle/kaggle.json (Linux/Mac), or set KAGGLE_USERNAME and
    KAGGLE_KEY environment variables.

  - Example command (PowerShell):
      py scripts\kaggle_download.py --dataset plantvillage/plantvillage

  - Default dataset is PlantVillage (plantvillage/plantvillage). You can pass
    the Kaggle dataset slug (owner/dataset-name) via --dataset.

Notes:
  - This script requires the `kaggle` Python package (pip install kaggle).
  - The Kaggle API requires authentication. See https://www.kaggle.com/docs/api

"""
import os
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_kaggle_credentials():
    """Return True if Kaggle credentials appear to be configured."""
    # Kaggle uses ~/.kaggle/kaggle.json or env variables KAGGLE_USERNAME/KAGGLE_KEY
    home = Path.home()
    kaggle_json = home / '.kaggle' / 'kaggle.json'
    if kaggle_json.exists():
        return True
    # Check env vars
    if os.getenv('KAGGLE_USERNAME') and os.getenv('KAGGLE_KEY'):
        return True
    return False


def download_dataset(dataset: str, dest: Path):
    """Download and extract a Kaggle dataset using the Kaggle API."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except Exception as e:
        logger.error("The 'kaggle' package is not installed. Install it with: py -m pip install kaggle")
        return False

    if not check_kaggle_credentials():
        logger.error("Kaggle credentials not found. Please place kaggle.json under ~/.kaggle/ or set KAGGLE_USERNAME/KAGGLE_KEY environment variables.")
        logger.info("See: https://www.kaggle.com/docs/api for instructions")
        return False

    api = KaggleApi()
    try:
        api.authenticate()
    except Exception as e:
        logger.error(f"Failed to authenticate with Kaggle API: {e}")
        return False

    dest.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Downloading dataset '{dataset}' into {dest.resolve()} (this may take a while)...")
        api.dataset_download_files(dataset, path=str(dest), unzip=True, quiet=False)
        logger.info("Download complete and files extracted.")

        # Count files
        files = [p for p in dest.rglob('*') if p.is_file()]
        logger.info(f"Files downloaded/extracted: {len(files)}")
        return True

    except Exception as e:
        logger.error(f"Error downloading dataset: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Download a Kaggle dataset into the project data folder')
    parser.add_argument('--dataset', '-d', default='plantvillage/plantvillage',
                        help='Kaggle dataset slug (owner/dataset-name). Default: plantvillage/plantvillage')
    parser.add_argument('--dest', default='data/kaggle', help='Destination folder (default: data/kaggle)')
    args = parser.parse_args()

    dataset = args.dataset
    dest = Path(args.dest)

    logger.info(f"Requested dataset: {dataset}")

    ok = download_dataset(dataset, dest)
    if not ok:
        logger.error("Dataset download failed. Follow the printed instructions to configure Kaggle and try again.")
        sys.exit(1)

    logger.info("Dataset downloaded successfully.")


if __name__ == '__main__':
    main()
