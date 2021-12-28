#!/usr/bin/env python3
import subprocess
import os
from typing import Any, Tuple
from glob import glob
from logging import getLogger, StreamHandler, Formatter, INFO

import numpy as np
from nptyping import NDArray
from PIL import Image


# Logging
formatter = Formatter(
    "[%(asctime)s] %(levelname)s (%(process)d) %(name)s\t: %(message)s"
)
handler = StreamHandler()
handler.setFormatter(formatter)
root_logger = getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(INFO)
logger = getLogger(__name__)


# Environment variables
INPUT_DIR = os.getenv("SCAN2STL_INPUT_DIR", "img")
SURFACE_DIR = os.getenv("SCAN2STL_SURFACE_DIR", "surface")
SCAD_DIR = os.getenv("SCAN2STL_SCAD_DIR", "scad")
OUTPUT_DIR = os.getenv("SCAN2STL_OUTPUT_DIR", "model")
DPI = os.getenv("SCAN2STL_IMAGE_DPI", "600")
THRESHOLD = os.getenv("SCAN2STL_BG_THRESHOLD", "240")
HEIGHT = os.getenv("SCAN2STL_MODEL_HEIGHT", "10")


def read_image(path: str) -> Image.Image:
    return Image.open(path)


def get_basename(path: str) -> str:
    filename = os.path.basename(path)
    return os.path.splitext(filename)[0]


def get_image_array(img: Image.Image) -> NDArray[(Any, Any, Any), int]:
    img = np.asarray(img, dtype=np.uint8)

    if img.ndim == 2:
        return img.reshape([*img.shape(), 1])

    return img


def generate_surface_with_threshold(
    arr: NDArray[(Any, Any, Any), int], threshold: int
) -> NDArray[(Any, Any), float]:
    surface = (np.mean(arr[:, :, :3], axis=2) < threshold).astype(np.float32)

    if arr.shape[2] == 4:
        alpha = arr[:, :, 3] / 0xFF
        surface = surface * alpha

    return surface


def save_surface_data(
    filename: str,
    surface: NDArray[(Any, Any), float],
):
    lines = list()
    for row in surface:
        lines.append(["%.3f" % v for v in row])

    with open(filename, "w") as f:
        for row in surface:
            f.write(" ".join(["%.3f" % v for v in row]))
            f.write("\n")


def get_scale(dpi: float) -> float:
    return 25.4 / dpi


def generate_scad_file(
    surface_filename: str,
    scad_filename: str,
    dpi: float,
    size: Tuple[int, int],
    height: float,
):
    template = 'scale([%.5f, %.5f, %.3f]) { surface(file = "%s"); }'
    template = """
    scale([%.5f, %.5f, %.3f]) {
        difference() {
            surface(file = \"%s\", center=true);
            translate([0, 0, -%.3f]) {
                cube([%d, %d, %.3f], center=true);
            }
        }
    }
    """
    scale = get_scale(dpi)
    args = (
        scale,
        scale,
        height,
        surface_filename,
        height * 0.5,
        size[1],
        size[0],
        height,
    )
    with open(scad_filename, "w") as f:
        f.write(template % args)


def build_stl_model(scad_filename: str, stl_filename: str):
    subprocess.run(["openscad", scad_filename, "-o", stl_filename])


if __name__ == "__main__":
    paths = glob(os.path.join(INPUT_DIR, "*"))

    os.makedirs(SURFACE_DIR, exist_ok=True)
    os.makedirs(SCAD_DIR, exist_ok=True)
    # os.makedirs(OUTPUT_DIR, exist_ok=True)

    surface_dir = os.path.abspath(SURFACE_DIR)
    scad_dir = os.path.abspath(SCAD_DIR)
    output_dir = os.path.abspath(OUTPUT_DIR)

    for path in paths:
        name = get_basename(path)
        surface_name = os.path.join(surface_dir, "%s.dat" % name)
        scad_name = os.path.join(scad_dir, "%s.scad" % name)
        stl_name = os.path.join(output_dir, "%s.stl" % name)

        if os.path.exists(stl_name):
            logger.info('"%s" exists... Skip', os.path.basename(stl_name))

        logger.info('Processing "%s"...', os.path.basename(path))

        img = read_image(path)
        arr = get_image_array(img)
        surface = generate_surface_with_threshold(arr, int(THRESHOLD))
        save_surface_data(surface_name, surface)

        generate_scad_file(
            surface_name, scad_name, float(DPI), arr.shape, float(HEIGHT)
        )

        build_stl_model(scad_name, stl_name)
        logger.info('Complete building .stl file. ("%s")', os.path.basename(stl_name))
