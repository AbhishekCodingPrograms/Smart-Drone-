"""
Copy a sample of images from downloaded Kaggle dataset folders into the project's
`data/sample_images/` folder so demos and the dashboard can find example images.

Usage:
  py scripts\sample_images_from_kaggle.py --source data/kaggle --dest data/sample_images --count 300

The script searches recursively for common image extensions and copies up to `count`
images into the destination folder.
"""
from pathlib import Path
import shutil
import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def collect_images(src: Path, exts=None):
    if exts is None:
        exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}
    images = []
    for p in src.rglob('*'):
        if p.is_file() and p.suffix.lower() in exts:
            images.append(p)
    return images


def copy_sample_images(src_root: str, dest_folder: str, count: int = 300):
    src = Path(src_root)
    if not src.exists():
        logger.error(f"Source folder does not exist: {src}")
        return 1

    dest = Path(dest_folder)
    dest.mkdir(parents=True, exist_ok=True)

    images = collect_images(src)
    if not images:
        logger.error(f"No image files found under {src}")
        return 1

    logger.info(f"Found {len(images)} images under {src}. Copying up to {count} images to {dest}...")
    copied = 0
    seen_names = set()
    for img in images:
        if copied >= count:
            break
        # avoid duplicate filenames
        target_name = img.name
        if target_name in seen_names:
            # make unique by prefixing parent folder
            target_name = f"{img.parent.name}_{img.name}"
        seen_names.add(target_name)

        target_path = dest / target_name
        try:
            shutil.copy2(img, target_path)
            copied += 1
        except Exception as e:
            logger.warning(f"Failed to copy {img}: {e}")
            continue

    logger.info(f"Copied {copied} images to {dest}")
    return 0


def main():
    parser = argparse.ArgumentParser(description='Copy sample images from downloaded Kaggle datasets')
    parser.add_argument('--source', '-s', default='data/kaggle', help='Root folder where Kaggle datasets were downloaded')
    parser.add_argument('--dest', '-d', default='data/sample_images', help='Destination folder to copy sample images')
    parser.add_argument('--count', '-c', type=int, default=300, help='Number of images to copy')
    args = parser.parse_args()

    rc = copy_sample_images(args.source, args.dest, args.count)
    sys.exit(rc)


if __name__ == '__main__':
    main()
