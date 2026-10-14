# Planner architecture

`planner.py` is the boundary between editable content and visual rendering. It decides what fits where; Typst decides how the planned components look.

## Pipeline

1. Load `book.toml`, `theme.toml`, and alphabetically ordered chapter TOML files.
2. Validate IDs, required fields, supported values, coordinates, flags, and asset paths.
3. Estimate text wrapping and component heights in millimetres.
4. Convert each section into a render block containing resolved measurements.
5. Pack blocks into A5 logical pages without splitting a component.
6. Insert blank pages for requested right-hand chapter openings or explicit page preferences.
7. Generate the table of contents from the resulting chapter start pages.
8. Pair logical pages into review spreads.
9. Write `generated/book.json` for Typst.

## Measurement model

Paragraphs use a conservative line estimate. Bullets and captions use proportional Helvetica glyph widths so words such as `iiii` and `WWWW` do not receive the same estimated width. Heights combine the estimated line count with configured font size, leading, paragraph gaps, titles, captions, and component-specific spacing.

The planner does not ask Typst for a rendered measurement. Its estimates are deterministic and fast, but unusual fonts or very long unbroken strings may require a theme adjustment.

## Pagination rules

- A block moves to the next page when its measured height exceeds the remaining capacity.
- `keep_with_next` reserves the following block as part of the fit decision.
- `new_page` starts a fresh page unless the block is already first.
- `preferred_page` is an explicit advanced override.
- Leading inter-section spacing is removed when a block becomes first on a page.
- `exclusive` coordinate-image blocks reserve the rest of their page.
- Chapters start on odd/right-hand pages unless `start_on_odd = false`.

The planner preserves source order. It does not reorder sections to fill holes and does not continuously optimize whitespace.

## Relationships

Relationships turn editorial meaning into a deterministic gap before a section. The values are defined under `[adaptive_layout]` in `theme.toml`.

- `standard`: ordinary transition.
- `attached`: part of the same visual unit.
- `continuation`: direct continuation of the same thought.
- `related`: distinct but closely connected.
- `relaxed`: slightly stronger break.
- `spacious`: strongest supported break.

## Responsibilities outside the planner

Typst owns fonts, colors, drawing, grids, alignment, image fitting, corner markers, and the physical A4 composition. `split_spreads.py` crops the review spreads into ordered A5 pages for printing.

## Extending the system

Adding a section type normally requires four coordinated changes:

1. Add its name to `SUPPORTED_TYPES`.
2. Validate its required content.
3. Measure it and emit a render block in `chapter_blocks`.
4. Render that block in `src/modules.typ`.

Add a unit test for every new rule that affects spacing or pagination, then rebuild and visually inspect the changed page and its neighbors.
