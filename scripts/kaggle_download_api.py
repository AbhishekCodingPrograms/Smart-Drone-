"""
Kaggle dataset downloader helper

Usage:
  py scripts\kaggle_download_api.py owner/dataset [dest_folder]

Example:
  py scripts\kaggle_download_api.py emmarex/plantdisease data/kaggle

This script uses the official Kaggle API (kaggle Python package).
Ensure you have your Kaggle API credentials configured (kaggle.json in ~/.kaggle or
environment variables KAGGLE_USERNAME and KAGGLE_KEY).
"""
from pathlib import Path
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def download_kaggle_dataset(dataset_slug: str, dest: str = "data/kaggle", unzip: bool = True) -> str:
    """
    Download a Kaggle dataset using the official Kaggle API and return the destination path.
    dataset_slug example: "emmarex/plantdisease" or "plantvillage/plantvillage".
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except Exception:
        logger.error("The 'kaggle' package is not installed. Install it with: py -m pip install kaggle")
        raise

    api = KaggleApi()
    try:
        api.authenticate()
    except Exception as e:
        logger.error("Kaggle authentication failed. Ensure ~/.kaggle/kaggle.json exists or set KAGGLE_USERNAME/KAGGLE_KEY env vars.")
        raise

    dest_path = Path(dest) / Path(dataset_slug.replace('/', '_'))
    dest_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading dataset '{dataset_slug}' into {dest_path.resolve()} ...")
    try:
        api.dataset_download_files(dataset_slug, path=str(dest_path), unzip=unzip, quiet=False)
    except Exception as e:
        logger.error(f"Error downloading dataset '{dataset_slug}': {e}")
        raise

    logger.info(f"Dataset downloaded to {dest_path.resolve()}")
    return str(dest_path.resolve())


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: py scripts\\kaggle_download_api.py <owner/dataset> [dest_folder]")
        sys.exit(1)

    dataset = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else "data/kaggle"

    try:
        path = download_kaggle_dataset(dataset, dest)
        print("Path to dataset files:", path)
    except Exception as e:
        print("Download failed:", e)
        sys.exit(1)
