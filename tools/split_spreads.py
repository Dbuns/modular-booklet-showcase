"""Convert the booklet's A4 spreads into printer-ready A5 single pages."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject


def half_page(page, side: str):
    result = copy.copy(page)
    left = float(page.mediabox.left)
    right = float(page.mediabox.right)
    bottom = float(page.mediabox.bottom)
    top = float(page.mediabox.top)
    middle = (left + right) / 2
    box = RectangleObject([left, bottom, middle, top] if side == "left" else [middle, bottom, right, top])
    result.mediabox = box
    result.cropbox = box
    result.trimbox = box
    return result


def split_spreads(source: Path, destination: Path) -> None:
    reader = PdfReader(source)
    if not reader.pages:
        raise ValueError("The spread PDF contains no pages.")

    writer = PdfWriter()
    writer.add_metadata(reader.metadata or {})

    # The cover spread is back cover | front cover. The print PDF starts with
    # the front cover, follows normal left-to-right reading order, and ends
    # with the back cover.
    cover = reader.pages[0]
    writer.add_page(half_page(cover, "right"))
    for spread in reader.pages[1:]:
        writer.add_page(half_page(spread, "left"))
        writer.add_page(half_page(spread, "right"))
    writer.add_page(half_page(cover, "left"))

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as stream:
        writer.write(stream)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: split_spreads.py INPUT.pdf OUTPUT.pdf")
    split_spreads(Path(sys.argv[1]), Path(sys.argv[2]))
