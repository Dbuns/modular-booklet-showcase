"""Validate modular booklet metadata and create a deterministic page plan."""

from __future__ import annotations

import json
import math
import sys
import tomllib
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
OUTPUT = ROOT / "generated" / "book.json"
SUPPORTED_TYPES = {"text", "people", "qr", "teams", "bullets", "routing", "image", "highlight", "profile_template"}
RELATIONSHIP_SPACING_KEYS = {
    "attached": "attached_before_mm",
    "continuation": "continuation_before_mm",
    "related": "related_before_mm",
    "relaxed": "relaxed_before_mm",
    "spacious": "spacious_before_mm",
}
SUPPORTED_RELATIONSHIPS = {"standard", *RELATIONSHIP_SPACING_KEYS}

# Adobe Helvetica AFM widths in thousandths of an em. Bullet-row planning uses
# these proportional widths instead of character counts so the reserved height
# follows the same wrapping that appears in Typst.
HELVETICA_WIDTHS = {
    " ": 278,
    **{char: 556 for char in "0123456789"},
    **dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", (667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611))),
    **dict(zip("abcdefghijklmnopqrstuvwxyz", (556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500))),
    ".": 278, ",": 278, ":": 278, ";": 278, "-": 333, "'": 191,
    "(": 333, ")": 333, "/": 278, "&": 667, "?": 556, "!": 278,
}


def load_toml(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def load_metadata() -> dict:
    book = load_toml(CONTENT / "book.toml")["book"]
    theme = load_toml(CONTENT / "theme.toml")
    chapters = []
    for path in sorted((CONTENT / "chapters").glob("*.toml")):
        source = load_toml(path)
        chapter = source["chapter"] | {"sections": source.get("sections", [])}
        chapter["source_file"] = path.name
        chapters.append(chapter)
    return {"book": book, "theme": theme, "chapters": chapters}


def wrapped_line_count(text: str, width_chars: int) -> int:
    """Conservative line estimate that also honours explicit metadata line breaks."""
    return sum(max(1, math.ceil(len(line) / width_chars)) for line in text.split("\n"))


def estimated_lines(paragraphs: list[str], width_chars: int = 56) -> int:
    return sum(wrapped_line_count(paragraph, width_chars) for paragraph in paragraphs)


def stack_height(paragraphs: list[str], theme: dict, line_count) -> float:
    """Convert measured paragraph line counts into the configured text height."""
    point_mm = 25.4 / 72.0
    first_line = float(theme["typography"]["body_size_pt"]) * point_mm
    line_pitch = float(theme["typography"]["body_leading_pt"]) * point_mm
    paragraph_gap = float(theme["typography"]["paragraph_after_pt"]) * point_mm
    heights = [first_line + max(0, line_count(paragraph) - 1) * line_pitch for paragraph in paragraphs]
    return sum(heights) + max(0, len(heights) - 1) * paragraph_gap + (0.8 if heights else 0.0)


def text_stack_height(paragraphs: list[str], theme: dict, width_chars: int = 56) -> float:
    """Estimate text using a conservative fixed-width line count."""
    return stack_height(paragraphs, theme, lambda text: wrapped_line_count(text, width_chars))


def proportional_line_count(text: str, width_mm: float, font_size_pt: float) -> int:
    """Greedy word wrapping using Helvetica's real proportional glyph widths."""
    max_width_pt = width_mm * 72.0 / 25.4

    def width_pt(value: str) -> float:
        return sum(HELVETICA_WIDTHS.get(char, 556) for char in value) * font_size_pt / 1000.0

    total = 0
    for explicit_line in text.split("\n"):
        words = explicit_line.split()
        if not words:
            total += 1
            continue
        lines = 1
        current = words[0]
        for word in words[1:]:
            candidate = current + " " + word
            if width_pt(candidate) <= max_width_pt:
                current = candidate
            else:
                lines += 1
                current = word
        total += lines
    return total


def proportional_text_stack_height(paragraphs: list[str], theme: dict, width_mm: float) -> float:
    font_size = float(theme["typography"]["body_size_pt"])
    return stack_height(paragraphs, theme, lambda text: proportional_line_count(text, width_mm, font_size))


def section_title_height(section: dict, theme: dict, before: float) -> float:
    if not section.get("title"):
        return before
    subtitle_mm = float(theme["typography"]["subtitle_size_pt"]) * 25.4 / 72.0
    return before + subtitle_mm + float(theme["spacing"]["subtitle_after_mm"]) + 0.8


def chapter_title_height(title: str, theme: dict, forced_lines: int | None = None) -> float:
    lines = forced_lines if forced_lines is not None else max(1, math.ceil(len(title) / 22))
    point_mm = 25.4 / 72.0
    first_line = float(theme["typography"]["title_size_pt"]) * point_mm
    line_pitch = float(theme["typography"]["title_leading_pt"]) * point_mm
    text_height = first_line + max(0, lines - 1) * line_pitch
    return text_height + float(theme["spacing"]["title_after_mm"])


def text_height(section: dict, theme: dict, before: float) -> float:
    title = section_title_height(section, theme, before)
    paragraphs = list(section["body"])
    if section.get("link_text"):
        paragraphs.append(section.get("link_prefix", "") + section["link_text"] + section.get("link_suffix", ""))
    return title + text_stack_height(paragraphs, theme)


def resolved_qr_layout(section: dict) -> str:
    """Resolve the convenient auto layout into a concrete rendering choice."""
    layout = section.get("layout", "stacked")
    if layout == "auto":
        return "side" if estimated_lines(section["body"], 56) <= 2 else "stacked"
    return layout


def resolved_section_before(section: dict, section_index: int, theme: dict) -> float:
    """Translate a semantic relationship into deterministic spacing."""
    if "before_mm" in section:
        return float(section["before_mm"])
    if section_index == 0:
        return 0.0
    adaptive = theme.get("adaptive_layout", {})
    relationship = section.get("relationship", "standard")
    if relationship == "standard":
        return float(theme["spacing"]["section_before_mm"])
    spacing_key = RELATIONSHIP_SPACING_KEYS[relationship]
    return float(adaptive[spacing_key])


def qr_height(section: dict, theme: dict, before: float) -> float:
    qr_box = float(section.get("qr_size_mm", theme["images"]["qr_box_mm"]))
    spacing = theme["spacing"]
    title = section_title_height(section, theme, before)
    side = resolved_qr_layout(section) == "side"
    body = text_stack_height(section["body"], theme, 28 if side else 56)
    figure = qr_box + spacing["qr_caption_height_mm"] - spacing["qr_caption_overlap_mm"]
    adaptive = theme.get("adaptive_layout", {})
    qr_before = float(section.get(
        "qr_before_mm",
        adaptive.get("attached_qr_gap_mm", spacing["qr_before_mm"])
        if section.get("relationship") == "attached" else spacing["qr_before_mm"],
    ))
    return title + (max(body, figure) + spacing["qr_after_mm"] if side else
                    body + qr_before + figure + spacing["qr_after_mm"])


def teams_height(section: dict, theme: dict, before: float) -> float:
    spacing = theme["spacing"]
    icon_size = theme["images"]["teams_icon_mm"]
    title = section_title_height(section, theme, before)
    body = text_stack_height(section["body"], theme)
    path_text = " → ".join(section["path"]) + " →"
    path_height = text_stack_height([path_text], theme)
    file_height = text_stack_height([section["filename"]], theme)
    team_block = icon_size + spacing["teams_title_to_path_mm"] + path_height + spacing["teams_path_to_file_mm"] + file_height
    after = text_stack_height(section.get("body_after", []), theme) if section.get("body_after") else 0.0
    # Typst's icon/text row has a slightly taller natural line box than the
    # nominal icon height. Reserve that real footprint so the following
    # module never starts on top of the filename link.
    return title + body + spacing["teams_before_mm"] + team_block + spacing["teams_after_mm"] + after + 8.0


def bullet_item_height(item, theme: dict, pitch: float, width_mm: float) -> float:
    if isinstance(item, str):
        return max(pitch, proportional_text_stack_height([item], theme, width_mm))
    body = proportional_text_stack_height(item.get("body", []), theme, width_mm) if item.get("body") else 0.0
    heading = item["title"] + item.get("title_tail", "")
    correction = float(theme["spacing"].get("grouped_bullet_height_correction_mm", 0.0))
    centered_gap = float(item.get(
        "center_last_before_mm",
        theme.get("adaptive_layout", {}).get("centered_detail_before_mm", 0.0)
        if item.get("detail_style") == "centered" else 0.0,
    ))
    content = proportional_text_stack_height([heading], theme, width_mm) + body
    return max(pitch, content + (3.0 if body else 0.0) + centered_gap - correction)


def bullets_height(section: dict, theme: dict, before: float) -> float:
    title = section_title_height(section, theme, before)
    intro = text_stack_height(section.get("body", []), theme) if section.get("body") else 0.0
    pitch = float(section.get("row_pitch_mm", theme["bullets"]["row_pitch_mm"]))
    width_mm = float(section.get("text_width_mm", theme["bullets"].get("text_width_mm", 99.9)))
    items = sum(bullet_item_height(item, theme, pitch, width_mm) for item in section["items"])
    bullets_after = float(section.get("bullets_after_mm", theme["spacing"].get("bullets_after_mm", 0.0)))
    return title + intro + (3.0 if intro else 0.0) + items + bullets_after


def highlight_height(section: dict, theme: dict, before: float) -> float:
    return before + text_stack_height(section["body"], theme, 52) + 4.0


def routing_height(section: dict, theme: dict, before: float) -> float:
    spacing = theme["spacing"]
    title = section_title_height(section, theme, before)
    body = text_stack_height(section.get("body", []), theme) if section.get("body") else 0.0
    subtitle = (
        spacing["section_before_mm"]
        + float(theme["typography"]["subtitle_size_pt"]) * 25.4 / 72.0
        + spacing["subtitle_after_mm"]
    )
    pitch = theme["bullets"]["row_pitch_mm"]
    rows = sum(max(
        pitch,
        text_stack_height([row["label"]], theme, 30),
        text_stack_height([row["destination"]], theme, 18),
    ) for row in section["rows"])
    return title + body + subtitle + rows


def image_caption_height(section: dict, theme: dict) -> float:
    caption = section.get("caption", "")
    if not caption:
        return 0.0
    minimum = float(theme["spacing"]["qr_caption_height_mm"])
    width = float(section.get("width_mm", 100.0))
    measured = proportional_text_stack_height([caption], theme, width)
    return max(minimum, measured)


def image_title_height(section: dict, theme: dict, before: float) -> float:
    title = section_title_height(section, theme, before)
    if section.get("title"):
        gap = float(section.get(
            "title_to_image_mm",
            theme["spacing"].get("image_title_to_media_mm", 1.5),
        ))
        title += gap - float(theme["spacing"]["subtitle_after_mm"])
    return title


def image_height(section: dict, theme: dict, before: float) -> float:
    """Estimate a flow image; page-coordinate images are overlays."""
    coordinates = ("x0", "x1", "y0", "y1")
    if all(key in section for key in coordinates):
        return 0.0
    title = image_title_height(section, theme, before)
    height = float(section.get("height_mm", 70.0))
    caption = image_caption_height(section, theme)
    caption_gap = 2.0 if caption else 0.0
    return title + height + caption_gap + caption + float(
        theme["spacing"].get("image_after_mm", theme["spacing"]["qr_after_mm"])
    )


def profile_template_height(section: dict, theme: dict, before: float) -> float:
    title = section_title_height(section, theme, before)
    intro = text_stack_height(section.get("body", []), theme, 56)
    picture = float(section.get("image_height_mm", section.get("image_mm", 31.0)))
    rows = sum(max(float(theme["bullets"]["row_pitch_mm"]), text_stack_height([item], theme, 40))
               for item in section["items"])
    gaps = max(0, len(section["items"]) - 1) * float(theme["spacing"].get("profile_bullet_gap_mm", 0.0))
    return title + intro + 4.0 + max(picture, rows + gaps)


def require_asset(path: str, context: str) -> None:
    if not (ROOT / path).exists():
        raise FileNotFoundError(f"Missing asset for {context}: {path}")


def validate(data: dict) -> None:
    if not data["chapters"]:
        raise ValueError("At least one chapter is required")
    chapter_ids: set[str] = set()
    section_ids: set[str] = set()
    for chapter in data["chapters"]:
        if chapter["id"] in chapter_ids:
            raise ValueError(f"Duplicate chapter id: {chapter['id']}")
        chapter_ids.add(chapter["id"])
        for section in chapter.get("sections", []):
            if section["id"] in section_ids:
                raise ValueError(f"Duplicate section id: {section['id']}")
            section_ids.add(section["id"])
            kind = section["type"]
            if kind not in SUPPORTED_TYPES:
                raise ValueError(f"Unsupported section type: {kind}")
            relationship = section.get("relationship", "standard")
            if relationship not in SUPPORTED_RELATIONSHIPS:
                raise ValueError(
                    f"Unsupported relationship in {section['id']}: {relationship}"
                )
            for flag in ("keep_with_next", "new_page"):
                if flag in section and not isinstance(section[flag], bool):
                    raise ValueError(f"{flag} in {section['id']} must be true or false")
            if "preferred_page" in section:
                preferred = section["preferred_page"]
                if not isinstance(preferred, int) or isinstance(preferred, bool) or preferred < 1:
                    raise ValueError(f"preferred_page in {section['id']} must be a positive integer")
            if kind == "people":
                for person in section.get("people", []):
                    missing = {"first_name", "last_name", "room", "photo"} - person.keys()
                    if missing:
                        raise ValueError(f"Person in {section['id']} is missing {sorted(missing)}")
                    require_asset(person["photo"], section["id"])
            elif kind == "qr":
                missing = {"body", "image", "caption", "link"} - section.keys()
                if missing:
                    raise ValueError(f"QR section {section['id']} is missing {sorted(missing)}")
                if section.get("layout", "stacked") not in {"stacked", "side", "auto"}:
                    raise ValueError(f"Invalid QR layout in {section['id']}")
                require_asset(section["image"], section["id"])
            elif kind == "teams":
                missing = {"body", "icon", "path", "filename", "link"} - section.keys()
                if missing:
                    raise ValueError(f"Teams section {section['id']} is missing {sorted(missing)}")
                require_asset(section["icon"], section["id"])
            elif kind == "bullets":
                if not section.get("items"):
                    raise ValueError(f"Bullet section {section['id']} has no items")
                for item in section["items"]:
                    if not isinstance(item, (str, dict)):
                        raise ValueError(f"Bullet item in {section['id']} must be text or a record")
                    if isinstance(item, dict) and "title" not in item:
                        raise ValueError(f"Grouped bullet in {section['id']} is missing title")
            elif kind == "highlight":
                if not section.get("body"):
                    raise ValueError(f"Highlight section {section['id']} has no body")
            elif kind == "routing":
                if not section.get("rows"):
                    raise ValueError(f"Routing section {section['id']} has no rows")
                for row in section["rows"]:
                    missing = {"label", "destination"} - row.keys()
                    if missing:
                        raise ValueError(f"Routing row in {section['id']} is missing {sorted(missing)}")
                if section.get("icon"):
                    require_asset(section["icon"], section["id"])
            elif kind == "image":
                if "image" not in section:
                    raise ValueError(f"Image section {section['id']} is missing image")
                require_asset(section["image"], section["id"])
                fit = section.get("fit", "contain")
                if fit not in {"contain", "cover", "stretch"}:
                    raise ValueError(f"Invalid image fit in {section['id']}: {fit}")
                coordinate_keys = ("x0", "x1", "y0", "y1")
                coordinate_count = sum(key in section for key in coordinate_keys)
                if coordinate_count not in {0, 4}:
                    raise ValueError(
                        f"Image section {section['id']} must define all of x0, x1, y0, y1 or none"
                    )
                if coordinate_count == 4:
                    x0, x1 = float(section["x0"]), float(section["x1"])
                    y0, y1 = float(section["y0"]), float(section["y1"])
                    if not (0 <= x0 < x1 <= 148.5 and 0 <= y0 < y1 <= 210):
                        raise ValueError(
                            f"Image coordinates in {section['id']} must fit the 148.5 x 210 mm page"
                        )
            elif kind == "profile_template":
                if not section.get("items"):
                    raise ValueError(f"Profile template {section['id']} has no bullet items")
                require_asset(section["image"], section["id"])


def chapter_blocks(chapter: dict, theme: dict) -> list[dict]:
    images = theme["images"]
    spacing = theme["spacing"]
    title_height = chapter_title_height(chapter["title"], theme, chapter.get("title_lines"))
    blocks: list[dict] = [{
        "kind": "chapter_title", "title": chapter["title"],
        "height_mm": round(title_height, 2), "chapter_color": chapter["color"],
        "marked": chapter.get("marked", False), "title_box_mm": round(title_height - spacing["title_after_mm"], 2),
        "title_after_mm": spacing["title_after_mm"],
        "title_align": chapter.get("title_align", "left"),
    }]
    person_index = 0
    side_qr_index = 0
    sections = chapter.get("sections", [])
    for section_index, section in enumerate(sections):
        kind = section["type"]
        before = resolved_section_before(section, section_index, theme)
        adaptive = theme.get("adaptive_layout", {})
        default_marmot_offset = 0.0
        if section.get("marked", False):
            if kind == "qr":
                default_marmot_offset = float(adaptive.get("marked_qr_marmot_offset_mm", 0.0))
            elif kind == "routing":
                default_marmot_offset = float(adaptive.get("marked_routing_marmot_offset_mm", 0.0))
        common = {
            "chapter_color": chapter["color"], "before_mm": before,
            "marked": section.get("marked", False),
            "keep_with_next": section.get("keep_with_next", False),
            "new_page": section.get("new_page", False),
            "title_align": section.get("title_align", chapter.get("title_align", "left")),
            "marmot_offset_mm": float(section.get("marmot_offset_mm", default_marmot_offset)),
        }
        if "preferred_page" in section:
            common["preferred_page"] = section["preferred_page"]
        if kind == "text":
            item = deepcopy(section)
            item |= common | {"kind": "text_section", "height_mm": round(text_height(section, theme, before), 2)}
            blocks.append(item)
        elif kind == "qr":
            item = deepcopy(section)
            if item.get("relationship") == "attached" and "qr_before_mm" not in item:
                item["qr_before_mm"] = float(theme.get("adaptive_layout", {}).get("attached_qr_gap_mm", spacing["qr_before_mm"]))
            item["layout"] = resolved_qr_layout(section)
            if item["layout"] == "side":
                item["qr_side"] = section.get("qr_side", "right" if side_qr_index % 2 == 0 else "left")
                if "side_text_align" not in item:
                    item["side_text_align"] = "center"
                side_qr_index += 1
            else:
                side_qr_index = 0
            item |= common | {"kind": "qr_section", "height_mm": round(qr_height(section, theme, before), 2)}
            blocks.append(item)
        elif kind == "teams":
            item = deepcopy(section)
            item |= common | {"kind": "teams_section", "height_mm": round(teams_height(section, theme, before), 2)}
            blocks.append(item)
        elif kind == "bullets":
            item = deepcopy(section)
            item["render_items"] = []
            row_pitch = float(section.get("row_pitch_mm", theme["bullets"]["row_pitch_mm"]))
            width_mm = float(section.get("text_width_mm", theme["bullets"].get("text_width_mm", 99.9)))
            for value in section["items"]:
                height = bullet_item_height(value, theme, row_pitch, width_mm)
                if isinstance(value, str):
                    item["render_items"].append({"text": value, "height_mm": round(height, 2), "grouped": False})
                else:
                    item["render_items"].append(value | {"height_mm": round(height, 2), "grouped": True})
            item |= common | {"kind": "bullets_section", "height_mm": round(bullets_height(item, theme, before), 2)}
            blocks.append(item)
        elif kind == "highlight":
            item = deepcopy(section)
            item |= common | {"kind": "highlight_section", "height_mm": round(highlight_height(section, theme, before), 2)}
            blocks.append(item)
        elif kind == "routing":
            item = deepcopy(section)
            item["render_rows"] = [
                row | {
                    "height_mm": round(max(
                        theme["bullets"]["row_pitch_mm"],
                        text_stack_height([row["label"]], theme, 30),
                        text_stack_height([row["destination"]], theme, 18),
                    ), 2),
                }
                for row in section["rows"]
            ]
            item |= common | {"kind": "routing_section", "height_mm": round(routing_height(section, theme, before), 2)}
            blocks.append(item)
        elif kind == "image":
            item = deepcopy(section)
            absolute = all(key in section for key in ("x0", "x1", "y0", "y1"))
            # Preserve the requested media height separately. `height_mm`
            # below is the complete section height used by the page planner.
            item["image_height_mm"] = float(section.get("height_mm", 70.0))
            item["caption_height_mm"] = round(image_caption_height(section, theme), 2)
            item["image_title_height_mm"] = round(image_title_height(section, theme, before), 2)
            item["image_title_gap_mm"] = float(section.get(
                "title_to_image_mm",
                theme["spacing"].get("image_title_to_media_mm", 1.5),
            ))
            item |= common | {
                "kind": "absolute_image" if absolute else "image_section",
                "height_mm": round(image_height(section, theme, before), 2),
                "absolute": absolute,
                "exclusive": bool(section.get("exclusive", absolute)),
            }
            blocks.append(item)
        elif kind == "profile_template":
            item = deepcopy(section)
            item["render_items"] = [
                {"text": value, "height_mm": round(max(theme["bullets"]["row_pitch_mm"], text_stack_height([value], theme, 40)), 2)}
                for value in section["items"]
            ]
            item |= common | {"kind": "profile_template", "height_mm": round(profile_template_height(section, theme, before), 2)}
            blocks.append(item)
        else:
            people = section.get("people", [])
            blocks.append({
                "kind": "section_heading", "title": section["title"],
                "height_mm": round(section_title_height(section, theme, before), 2),
                **common,
                "keep_with_next": bool(people) or common["keep_with_next"],
            })
            for person in people:
                blocks.append({
                    "kind": "person", "person": deepcopy(person),
                    "side": "left" if person_index % 2 == 0 else "right",
                    "height_mm": images["person_mm"] + theme["people"]["card_gap_mm"] + 1.0,
                    "section_id": section["id"], "chapter_color": chapter["color"],
                })
                person_index += 1
        if kind != "qr":
            side_qr_index = 0
    return blocks


def new_page(number: int, chapter: dict) -> dict:
    return {
        "number": number, "blank": False, "chapter_id": chapter["id"],
        "chapter_color": chapter["color"], "blocks": [], "used_mm": 0.0,
    }


def pack_chapter(chapter: dict, theme: dict, capacity: float, first_page: int) -> tuple[list[dict], int]:
    page_number = first_page
    pages: list[dict] = []
    if chapter.get("start_on_odd", True) and page_number % 2 == 0:
        pages.append({
            "number": page_number, "blank": True, "chapter_id": chapter["id"],
            "chapter_color": chapter["color"], "blocks": [], "used_mm": 0.0,
        })
        page_number += 1

    current = new_page(page_number, chapter)
    blocks = chapter_blocks(chapter, theme)

    def trim_leading_space(block: dict) -> dict:
        """Remove inter-section spacing when a block becomes first on a page."""
        before = float(block.get("before_mm", 0.0))
        if before <= 0:
            return block
        block = deepcopy(block)
        block["height_mm"] = round(float(block["height_mm"]) - before, 2)
        block["before_mm"] = 0.0
        if block.get("kind") == "image_section":
            block["image_title_height_mm"] = round(
                float(block["image_title_height_mm"]) - before, 2
            )
        return block

    for index, block in enumerate(blocks):
        preferred_page = block.get("preferred_page")
        if preferred_page is not None:
            if preferred_page < page_number:
                raise ValueError(
                    f"Section {block.get('id', block['kind'])} prefers page {preferred_page}, "
                    f"but planning has already reached page {page_number}"
                )
            if preferred_page > page_number:
                if current["blocks"]:
                    pages.append(current)
                    page_number += 1
                while page_number < preferred_page:
                    blank = new_page(page_number, chapter)
                    blank["blank"] = True
                    pages.append(blank)
                    page_number += 1
                current = new_page(page_number, chapter)
                block = trim_leading_space(block)
        if block.get("new_page") and current["blocks"]:
            pages.append(current)
            page_number += 1
            current = new_page(page_number, chapter)
            block = trim_leading_space(block)
        required = float(block["height_mm"])
        if block.get("keep_with_next") and index + 1 < len(blocks):
            required += float(blocks[index + 1]["height_mm"])
        if current["blocks"] and current["used_mm"] + required > capacity:
            pages.append(current)
            page_number += 1
            current = new_page(page_number, chapter)
            block = trim_leading_space(block)
        current["blocks"].append(block)
        if block.get("exclusive"):
            current["used_mm"] = capacity
        else:
            current["used_mm"] = round(current["used_mm"] + float(block["height_mm"]), 2)
    pages.append(current)
    return pages, page_number + 1


def make_spreads(pages: list[dict]) -> list[dict]:
    by_number = {page["number"]: page for page in pages}
    highest = max(by_number)
    return [{"left": by_number.get(odd - 1), "right": by_number.get(odd)}
            for odd in range(1, highest + 2, 2)]


def main() -> None:
    data = load_metadata()
    validate(data)
    capacity = float(data["theme"]["geometry"]["page_capacity_mm"])
    next_page = int(data["book"].get("start_page", 1))
    pages: list[dict] = []
    front_matter = data["book"].get("front_matter")
    if front_matter:
        pages.append({
            "number": 0, "blank": False, "chapter_id": "front-matter",
            "chapter_color": data["theme"]["colors"]["link"],
            "show_marker": False, "used_mm": capacity,
            "blocks": [{
                "kind": "front_matter", "height_mm": capacity,
                **front_matter,
            }],
        })
    contents_page = None
    if data["book"].get("contents", True):
        contents_title_height = data["theme"]["typography"]["title_size_pt"] * 25.4 / 72.0
        contents_height = (
            contents_title_height
            + data["theme"]["spacing"]["contents_title_to_entries_mm"]
        )
        contents_page = {
            "number": 0, "blank": False, "chapter_id": "contents",
            "chapter_color": data["theme"]["colors"]["link"],
            "show_marker": False, "used_mm": contents_height,
            "blocks": [{
                "kind": "contents", "title": data["book"].get("contents_title", "Contents"),
                "entries": [], "height_mm": contents_height,
            }],
        }

    contents_entries = []
    for chapter in data["chapters"]:
        chapter_pages, next_page = pack_chapter(chapter, data["theme"], capacity, next_page)
        pages.extend(chapter_pages)
        first_content_page = next(page["number"] for page in chapter_pages if not page["blank"])
        contents_entries.append({"title": chapter["title"], "page": first_content_page})
    if contents_page is not None:
        contents_page["blocks"][0]["entries"] = contents_entries
        contents_page["blocks"][0]["height_mm"] = (
            contents_title_height
            + data["theme"]["spacing"]["contents_title_to_entries_mm"]
            + len(contents_entries) * data["theme"]["spacing"]["contents_row_mm"]
        )
        contents_page["used_mm"] = contents_page["blocks"][0]["height_mm"]
    output = {
        "book": data["book"], "theme": data["theme"],
        "contents_page": contents_page,
        "pages": pages, "spreads": make_spreads(pages),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Planned {len(pages)} logical pages in {len(output['spreads'])} spreads")
    for page in pages:
        label = "blank" if page["blank"] else f"{page['used_mm']:5.1f} mm"
        print(f"  page {page['number']}: {label}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Planner error: {exc}", file=sys.stderr)
        raise
