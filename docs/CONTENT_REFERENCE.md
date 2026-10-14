# Content and formatting reference

## Chapter files

Chapter files are loaded alphabetically from `content/chapters`, so numeric prefixes provide an obvious reading order.

```toml
[chapter]
id = "example"
title = "Example chapter"
color = "#2F6F6D"
start_on_odd = true
marked = false
title_align = "left"
```

`id`, `title`, and `color` are required. `start_on_odd` defaults to `true`. `marked` adds the configured audience icon. `title_align` may be `left` or `center`.

## Fields shared by sections

Every section needs a unique `id` and a supported `type`.

Common optional fields:

- `relationship`: `standard`, `attached`, `continuation`, `related`, `relaxed`, or `spacious`.
- `before_mm`: explicit gap override; use sparingly because it replaces the relationship rule.
- `keep_with_next`: move this block when necessary so the following block stays with it.
- `new_page`: start the block on a new page when the current page already contains content.
- `preferred_page`: advanced escape hatch that inserts pages until the requested logical page number.
- `marked`: show the configured audience marker.
- `title_align`: `left` or `center`.

## Text

```toml
[[sections]]
id = "introduction"
type = "text"
title = "Introduction"
body = [
  "First paragraph.",
  "Second paragraph."
]
```

Optional link fields are `link_text`, `link_url`, `link_prefix`, and `link_suffix`.

## Bullets

```toml
[[sections]]
id = "checklist"
type = "bullets"
title = "Checklist"
items = ["First item", "Second item"]
```

Use `list_style = "number"` for numbered steps. A grouped item may contain a bold `title`, optional `title_tail`, and a `body` array.

## Highlight

```toml
[[sections]]
id = "key-message"
type = "highlight"
title = ""
style = "bold"
body = ["A short statement that deserves emphasis."]
```

Supported styles are `bold`, `italic`, `bold-italic`, and regular text when omitted.

## People

```toml
[[sections]]
id = "team"
type = "people"
title = "Team"

[[sections.people]]
first_name = "Alex"
last_name = "Example"
room = "Role or contact line"
photo = "assets/showcase/person.png"
```

Portraits alternate between the inner and outer edges automatically.

## Routing rows

```toml
[[sections]]
id = "routing"
type = "routing"
title = "Where should this live?"
body = ["Use rows to map a subject to a destination."]
subtitle = "Subject to destination"
rows = [
  { label = "Images", destination = "assets/" },
  { label = "Page copy", destination = "content/chapters/" }
]
```

Each row is measured independently. Wrapped rows become taller without changing the pitch of neighboring single-line rows.

## QR links

```toml
[[sections]]
id = "resource"
type = "qr"
title = "Resource"
body = ["A short explanation."]
image = "assets/showcase/qr-example.png"
caption = "Open resource"
link = "https://example.com"
layout = "side"
qr_size_mm = 42
```

`layout` may be `side`, `stacked`, or `auto`. Side layouts are intended for very short explanations. `attached` also reduces the internal gap before a stacked QR figure.

## Shared-file link

The historical internal name is `teams`, but the component can represent any repository or shared-file location.

```toml
[[sections]]
id = "shared-file"
type = "teams"
title = "Shared file"
body = ["Explanation."]
icon = "assets/showcase/folder-icon.svg"
path = ["Repository", "content"]
filename = "example.toml"
link = "https://example.com"
```

## Flow image

```toml
[[sections]]
id = "diagram"
type = "image"
title = "Diagram"
image = "assets/showcase/diagram.svg"
caption = "Optional caption"
width_mm = 104
height_mm = 58
fit = "contain"
```

`fit` may be `contain`, `cover`, or `stretch`. Flow images reserve space and move later content automatically.

Advanced decorative images may specify all four page coordinates: `x0`, `x1`, `y0`, and `y1`. Coordinates use the complete 148.5 x 210 mm logical page. Coordinate images are overlays and should be used sparingly.

## Image-and-list template

```toml
[[sections]]
id = "profile-template"
type = "profile_template"
title = "Image and list"
body = ["Short introduction."]
image = "assets/showcase/person.png"
image_width_mm = 34.5
image_height_mm = 34.5
items = ["First point", "Second point"]
```

## Asset formats

- SVG: logos, icons, diagrams, and geometric illustrations.
- PNG: QR codes, screenshots, transparency, and lossless raster graphics.
- JPEG: photographs where compact file size matters.

An SVG may embed a raster image. That is useful for cropping or framing, but it does not turn a photograph into vector artwork.
