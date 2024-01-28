from datetime import datetime
from fractions import Fraction
from PIL import Image, ImageOps
import os
import logging


logger = logging.getLogger(__name__)


REFERENCE_ASPECT_RATIO = Fraction(4, 3)
OUTPUT_DIR = f"Output - {datetime.now()}"
BASE_DIR = os.getcwd()
INPUT_EXTENSIONS = ("jpeg", "jpg", "cr2")
OUTPUT_EXTENSIONS = ("jpeg", "jpg")
ALLOWED_CROP_POINTS: dict = {
        "top_left": (0.0, 0.0),
        "left": (0.0, 0.5),
        "bottom_left": (0.0, 1.0),
        "bottom": (0.5, 1.0),
        "bottom_right": (1.0, 1.0),
        "right": (1.0, 0.5),
        "top_right": (1.0, 0.0),
        "top": (0.5, 0.0),
        "center": (0.5, 0.5),
    }


def main() -> None:
    os.mkdir(OUTPUT_DIR)
    logger.info(f"Processing pictures in {os.getcwd()}")

    images_list: list = sorted(os.listdir())
    if not images_list:
        logger.info(f"There is no one image to process in '{os.getcwd()}'")
        return

    _process_folder(images_list=images_list)


def _process_folder(images_list: list) -> None:
    for picture_name in images_list:
        os.chdir(BASE_DIR)
        extension = picture_name.split(".")[-1].lower()

        if extension not in INPUT_EXTENSIONS:
            continue

        with Image.open(picture_name) as image:
            os.chdir(OUTPUT_DIR)
            aspect_ratio: Fraction = Fraction(
                image.size[0] / image.size[1]
            ).limit_denominator(100)
            logger.info(f"Picture {image.filename} has aspect ratio: {aspect_ratio}")
            if aspect_ratio in (REFERENCE_ASPECT_RATIO, 1 / REFERENCE_ASPECT_RATIO):
                _save_original(image)
                continue

            elif aspect_ratio > 1:  # landscape
                if aspect_ratio > REFERENCE_ASPECT_RATIO:
                    _manage_large_width(image=image, orientation="landscape")

                else:  # aspect_ratio < REFERENCE_ASPECT_RATIO
                    _manage_large_height(image=image, orientation="landscape")

            elif aspect_ratio <= 1:  # portrait
                if aspect_ratio > 1 / REFERENCE_ASPECT_RATIO:
                    _manage_large_width(image=image, orientation="portrait")

                else:  # aspect_ratio < REFERENCE_ASPECT_RATIO
                    _manage_large_height(image=image, orientation="portrait")


def _mkdir_and_chdir(path: str) -> None:
    os.mkdir(path=path)
    os.chdir(path=path)


def _manage_large_width(image: Image, orientation: str) -> None:
    folder_name: str = ".".join(image.filename.split(".")[:-1])
    _mkdir_and_chdir(path=folder_name)

    _save_original(image)
    _extend_height(image=image, orientation=orientation)
    _crop_left(image=image, orientation=orientation)
    _crop_width_center(image=image, orientation=orientation)
    _crop_right(image=image, orientation=orientation)


def _manage_large_height(image: Image, orientation: str) -> None:
    folder_name: str = ".".join(image.filename.split(".")[:-1])
    _mkdir_and_chdir(path=folder_name)

    _save_original(image)
    _extend_width(image=image, orientation=orientation)
    _crop_up(image=image, orientation=orientation)
    _crop_height_center(image=image, orientation=orientation)
    _crop_down(image=image, orientation=orientation)


def _extend_height(image: Image, orientation: str) -> None:
    image_width: int = image.size[0]
    expected_height: int = int(image_width / _get_desired_aspect_ratio(orientation))
    base_img_name: str = ".".join(image.filename.split(".")[:-1])
    ImageOps.pad(image=image, size=(image_width, expected_height), color="#000").save(
        f"{base_img_name}_extended_heigh.jpg"
    )


def _extend_width(image: Image, orientation: str) -> None:
    image_height: int = image.size[1]
    expected_width: int = int(image_height * _get_desired_aspect_ratio(orientation))
    base_img_name: str = ".".join(image.filename.split(".")[:-1])
    ImageOps.pad(image=image, size=(expected_width, image_height), color="#000").save(
        f"{base_img_name}_extended_width.jpg"
    )


def _crop_left(image: Image, orientation: str) -> None:
    image_height: int = image.size[1]
    expected_width: int = int(image_height * _get_desired_aspect_ratio(orientation))
    size: tuple = (expected_width, image_height)
    _crop_image(image=image, position="left", size=size)


def _crop_right(image: Image, orientation: str) -> None:
    image_height: int = image.size[1]
    expected_width: int = int(image_height * _get_desired_aspect_ratio(orientation))
    size: tuple = (expected_width, image_height)
    _crop_image(image=image, position="right", size=size)


def _crop_height_center(image: Image, orientation: str) -> None:
    image_width: int = image.size[0]
    expected_height: int = int(image_width / _get_desired_aspect_ratio(orientation))
    size: tuple = (image_width, expected_height)
    _crop_image(image=image, position="center", size=size)


def _crop_width_center(image: Image, orientation: str) -> None:
    image_height: int = image.size[1]
    expected_width: int = int(image_height * _get_desired_aspect_ratio(orientation))
    size: tuple = (expected_width, image_height)
    _crop_image(image=image, position="center", size=size)


def _crop_up(image: Image, orientation: str) -> None:
    image_width: int = image.size[0]
    expected_height: int = int(image_width / _get_desired_aspect_ratio(orientation))
    size: tuple = (image_width, expected_height)
    _crop_image(image=image, position="top", size=size)


def _crop_down(image: Image, orientation: str) -> None:
    image_width: int = image.size[0]
    expected_height: int = int(image_width / _get_desired_aspect_ratio(orientation))
    size: tuple = (image_width, expected_height)
    _crop_image(image=image, position="bottom", size=size)


def _get_desired_aspect_ratio(orientation: str) -> Fraction:
    return (
        REFERENCE_ASPECT_RATIO
        if orientation == "landscape"
        else 1 / REFERENCE_ASPECT_RATIO
    )


def _save_original(image: Image) -> None:
    filename = image.filename
    if filename.split(".")[-1].lower() not in OUTPUT_EXTENSIONS:
        filename = f"{image.filename.split(".")[:-1]}.jpg"
    
    image.save(f"Original_{filename}")


def _crop_image(image: Image, position: str, size: tuple) -> None:
    base_img_name: str = ".".join(image.filename.split(".")[:-1])

    if position not in ALLOWED_CROP_POINTS.keys():
        logger.warning(
            f"{position} is not a valid position ({list(ALLOWED_CROP_POINTS.keys())})"
        )

    ImageOps.fit(image=image, size=size, centering=ALLOWED_CROP_POINTS.get(position)).save(
        f"{base_img_name}_cropped_to_{position}.jpg"
    )


if __name__ == "__main__":
    main()
