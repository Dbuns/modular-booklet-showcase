#import "theme.typ": settings, ink, rule-color, link-color, body-font, title-font, subtitle-font, body-size, body-leading, paragraph-spacing, person-size, teams-icon-size, marmot-size, body-style, chapter-title, section-title

#let paragraphs(items) = {
  for (index, paragraph) in items.enumerate() {
    paragraph
    if index + 1 < items.len() { parbreak() }
  }
}

#let generated-cover-spread(cover) = box(width: 297mm, height: 210mm, fill: rgb(cover.paper_color))[
  #for (index, color) in cover.band_colors.enumerate() {
    place(top + left, dy: (45.4 + index * 12.3) * 1mm)[
      #rect(width: 297mm, height: 10.8mm, fill: rgb(color), stroke: none)
    ]
  }
  #place(top + left, dx: 0mm, dy: 11.9mm)[
    #box(width: 148.5mm)[
      #align(center)[
        #box(width: 134.9mm)[
          #set text(font: "Arial", size: 18pt, fill: rgb(cover.ink_color))
          #set par(leading: 0pt)
          #align(center)[#cover.back_note]
        ]
      ]
    ]
  ]
  #place(top + left, dx: 148.5mm, dy: 44.5mm)[
    #box(width: 148.5mm)[
      #align(center)[
        #box(fill: rgb(cover.paper_color), inset: (x: 5mm, y: 0mm))[
          #set text(font: title-font, size: 140pt, weight: "bold", fill: rgb(cover.ink_color))
          #cover.acronym
        ]
      ]
    ]
  ]
  #place(top + left, dx: 148.5mm, dy: 90.6mm)[
    #box(width: 148.5mm)[
      #align(center)[
        #set text(font: title-font, size: 20pt, weight: "bold", fill: rgb(cover.ink_color))
        #cover.group_name
      ]
    ]
  ]
  #place(top + left, dx: 148.5mm, dy: 99.7mm)[
    #box(width: 148.5mm)[
      #align(center)[
        #set text(font: "Arial", size: 18pt, fill: rgb(cover.ink_color))
        #cover.institute
      ]
    ]
  ]
  #place(top + left, dx: 148.5mm, dy: 181mm)[
    #box(width: 148.5mm)[
      #align(center)[
        #box(width: 135mm)[
          #set text(font: "Arial", size: 18pt, fill: rgb(cover.ink_color))
          #set par(leading: 0pt)
          #align(center)[#cover.tagline]
        ]
      ]
    ]
  ]
]

#let cover-spread(cover) = {
  if cover.at("mode", default: "generated") == "image" {
    image("../" + cover.image, width: 297mm, height: 210mm, fit: "cover")
  } else {
    generated-cover-spread(cover)
  }
}

#let compact-body(body) = {
  set text(font: body-font, size: body-size, fill: ink)
  set par(leading: body-leading, spacing: 0pt, justify: false)
  body
}

#let front-matter-block(item, height) = block(width: 100%, height: height)[
  #place(top + left)[
    #box(width: 100%)[
      #compact-body[
        #item.marmot_note_before
        #box(width: marmot-size * 0.75, height: marmot-size * 0.75, baseline: 40%)[
          #move(dy: -settings.spacing.front_marmot_raise_mm * 1mm)[
            #image("../" + settings.images.marmot_asset, width: 100%, height: 100%, fit: "contain")
          ]
        ]
        #item.marmot_note_after
      ]
    ]
  ]
  #place(bottom + left)[
    #box(width: 100%)[
      #set text(font: body-font, size: body-size, fill: ink)
      #strong(item.document_title)
      #v(4mm)
      #for line in item.document_lines { line; linebreak() }
      #v(4mm)
      #item.updates_note
    ]
  ]
]

#let contents-block(item, height) = block(width: 100%, height: height)[
  #place(top + left)[
    #set text(font: title-font, size: 30pt, weight: "bold", fill: ink)
    #item.title
  ]
  #place(top + left, dy: settings.typography.title_size_pt * 1pt + settings.spacing.contents_title_to_entries_mm * 1mm)[
    #box(width: 100%)[
      #set text(font: body-font, size: body-size, fill: ink)
      #for entry in item.entries {
        block(width: 100%, height: settings.spacing.contents_row_mm * 1mm)[
          #grid(
            columns: (auto, 1fr, auto), column-gutter: 2mm, align: horizon,
            entry.title,
            line(length: 100%, stroke: (paint: ink, thickness: 1pt, dash: "dotted")),
            str(entry.page),
          )
        ]
      }
    ]
  ]
]

#let bullet-column(color, label: none, pitch: settings.bullets.row_pitch_mm) = box(
  width: (settings.bullets.diameter_mm + settings.bullets.edge_to_text_mm) * 1mm,
  height: pitch * 1mm,
)[
  #if label == none {
    place(top + left, dy: settings.bullets.center_y_mm * 1mm)[
      #circle(radius: settings.bullets.diameter_mm * 0.5mm, fill: rgb(color), stroke: none)
    ]
  } else {
    place(top + left)[
      #set text(font: body-font, size: body-size, weight: "bold", fill: rgb(color))
      #label
    ]
  }
]

#let bullets-section(item, height) = block(width: 100%, height: height)[
  #if item.title != "" { section-title(item.title, before: item.before_mm * 1mm, alignment: item.title_align) } else { v(item.before_mm * 1mm) }
  #if "body" in item and item.body.len() > 0 {
    body-style[#paragraphs(item.body)]
    v(3mm)
  }
  #let cells = ()
  #for (entry-index, entry) in item.render_items.enumerate() {
    let marker = if item.at("list_style", default: "bullet") == "number" { str(entry-index + 1) + "." } else { none }
    cells.push(bullet-column(item.chapter_color, label: marker, pitch: entry.height_mm))
    if entry.grouped {
      cells.push(box(width: 100%, height: entry.height_mm * 1mm)[
        #set text(font: body-font, size: body-size, fill: ink)
        #set par(leading: settings.spacing.grouped_leading_pt * 1pt, spacing: settings.spacing.grouped_paragraph_after_pt * 1pt, justify: false)
        #[
          #strong(entry.title)
          #entry.at("title_tail", default: "")
          #if "body" in entry and entry.body.len() > 0 {
            v(settings.spacing.grouped_body_gap_mm * 1mm)
            for (index, paragraph) in entry.body.enumerate() {
              if (entry.at("detail_style", default: "") == "centered" or entry.at("center_last", default: false)) and index + 1 == entry.body.len() {
                v(entry.at("center_last_before_mm", default: settings.adaptive_layout.centered_detail_before_mm) * 1mm)
                align(center)[#paragraph]
              } else {
                paragraph
              }
              if index + 1 < entry.body.len() { parbreak() }
            }
          }
        ]
      ])
    } else {
      cells.push(box(width: 100%, height: entry.height_mm * 1mm)[#compact-body(entry.text)])
    }
  }
  #grid(
    columns: ((settings.bullets.diameter_mm + settings.bullets.edge_to_text_mm) * 1mm, 1fr),
    column-gutter: 0mm, row-gutter: 0mm, align: top,
    ..cells,
  )
  #v(item.at("bullets_after_mm", default: settings.spacing.bullets_after_mm) * 1mm)
]

#let routing-section(item, height) = block(width: 100%, height: height)[
  #if item.title != "" { section-title(item.title, before: item.before_mm * 1mm, alignment: item.title_align) } else { v(item.before_mm * 1mm) }
  #body-style[#paragraphs(item.body)]
  #section-title(item.subtitle, before: settings.spacing.section_before_mm * 1mm, alignment: item.title_align)
  #let cells = ()
  #let row-sizes = ()
  #for row in item.render_rows {
    row-sizes.push(row.height_mm * 1mm)
    cells.push(bullet-column(item.chapter_color, pitch: row.height_mm))
    cells.push(box(width: 100%, height: row.height_mm * 1mm)[#compact-body(row.label)])
    cells.push(box(width: 100%, height: row.height_mm * 1mm)[#compact-body[#sym.arrow.r]])
    cells.push(box(width: 100%, height: row.height_mm * 1mm)[#compact-body(row.destination)])
  }
  #grid(
    columns: ((settings.bullets.diameter_mm + settings.bullets.edge_to_text_mm) * 1mm, 52mm, settings.bullets.routing_arrow_column_mm * 1mm, 1fr),
    rows: row-sizes,
    column-gutter: 0mm, row-gutter: 0mm, align: top,
    ..cells,
  )
]

#let photograph(path) = box(
  width: person-size, height: person-size,
  radius: settings.people.corner_radius_mm * 1mm,
  stroke: settings.people.border_pt * 1pt + ink, clip: true, inset: 0pt,
)[#image("../" + path, width: person-size, height: person-size, fit: "cover")]

#let person-information(person, side) = box(width: 100%, height: person-size)[
  #let horizontal = if side == "left" { left } else { right }
  #let image-gap = settings.people.image_to_text_mm * 1mm
  #let rule-length = settings.people.rule_length_mm * 1mm
  #let rule-y = person-size / 2
  #let name-top = rule-y - body-size - settings.people.name_to_rule_mm * 1mm
  #let room-y = rule-y + settings.people.rule_to_room_mm * 1mm
  #place(top + horizontal, dy: name-top)[
    #set text(font: body-font, size: body-size, fill: ink)
    #person.first_name #strong(person.last_name)
  ]
  #if side == "left" {
    place(top + left, dx: -image-gap, dy: rule-y)[#line(length: rule-length, stroke: settings.people.rule_pt * 1pt + rule-color)]
  } else {
    place(top + right, dx: image-gap, dy: rule-y)[#line(length: rule-length, stroke: settings.people.rule_pt * 1pt + rule-color)]
  }
  #place(top + horizontal, dy: room-y)[
    #set text(font: body-font, size: body-size, fill: ink)
    #person.room
  ]
]

#let person-card(person, side, height: 31mm) = block(width: 100%, height: height)[
  #let image-gap = settings.people.image_to_text_mm * 1mm
  #if side == "left" {
    grid(columns: (person-size, 1fr), column-gutter: image-gap,
      photograph(person.photo), person-information(person, "left"))
  } else {
    grid(columns: (1fr, person-size), column-gutter: image-gap,
      person-information(person, "right"), photograph(person.photo))
  }
]

#let qr-caption-height = settings.spacing.qr_caption_height_mm * 1mm
#let qr-caption-overlap = settings.spacing.qr_caption_overlap_mm * 1mm
#let qr-figure(item) = {
  let figure-size = item.at("qr_size_mm", default: settings.images.qr_box_mm) * 1mm
  let figure-height = figure-size + qr-caption-height - qr-caption-overlap
  box(width: figure-size, height: figure-height)[
  #place(top + left)[
    #link(item.link)[#image("../" + item.image, width: figure-size, height: figure-size, fit: "contain")]
  ]
  #place(top + center, dy: figure-size - qr-caption-overlap)[
    #box(width: figure-size, height: qr-caption-height)[
      #align(center)[
        #set text(font: body-font, size: body-size, fill: ink)
        #set par(leading: body-leading)
        #item.caption
      ]
    ]
  ]
  ]
}

#let qr-section(item, height) = block(width: 100%, height: height)[
  #let figure-size = item.at("qr_size_mm", default: settings.images.qr_box_mm) * 1mm
  #let side-text-offset = item.at("side_text_offset_mm", default: settings.spacing.qr_side_text_offset_mm) * 1mm
  #let side-text-position = if item.at("side_text_align", default: "center") == "top" { top + left } else { left + horizon }
  #let side-body = box(width: 100%, height: figure-size)[
    #place(side-text-position, dy: side-text-offset)[#box(width: 100%)[#align(left)[#body-style[#paragraphs(item.body)]]]]
  ]
  #if item.title != "" { section-title(item.title, before: item.before_mm * 1mm, alignment: item.title_align) } else { v(item.before_mm * 1mm) }
  #if item.layout == "side" {
    if item.qr_side == "left" {
      grid(
        columns: (figure-size, 1fr), column-gutter: settings.spacing.qr_side_gap_mm * 1mm, align: top,
        qr-figure(item), side-body,
      )
    } else {
      grid(
        columns: (1fr, figure-size), column-gutter: settings.spacing.qr_side_gap_mm * 1mm, align: top,
        side-body, qr-figure(item),
      )
    }
  } else {
    body-style[#paragraphs(item.body)]
    v(item.at("qr_before_mm", default: settings.spacing.qr_before_mm) * 1mm)
    align(center)[#qr-figure(item)]
  }
  #v(settings.spacing.qr_after_mm * 1mm)
]

#let linked-picture(item, width, height) = {
  let picture = image(
    "../" + item.image,
    width: width,
    height: height,
    fit: item.at("fit", default: "contain"),
  )
  let target = item.at("link", default: "")
  if target == "" { picture } else { link(target)[#picture] }
}

#let image-caption(item, width) = {
  let caption = item.at("caption", default: "")
  if caption != "" {
    box(width: width, height: item.at("caption_height_mm", default: settings.spacing.qr_caption_height_mm) * 1mm)[
      #set text(font: body-font, size: body-size, fill: ink)
      #set par(leading: body-leading, spacing: 0pt, justify: false)
      #align(center)[#caption]
    ]
  }
}

#let image-section(item, height) = block(width: 100%, height: height)[
  #let picture-width = item.at("width_mm", default: 100.0) * 1mm
  #let picture-height = item.at("image_height_mm", default: 70.0) * 1mm
  #let title-height = item.image_title_height_mm * 1mm
  #if item.title != "" {
    place(top + left)[
      #section-title(
        item.title,
        before: item.before_mm * 1mm,
        after: item.image_title_gap_mm * 1mm,
      )
    ]
  }
  #place(top + center, dy: title-height)[
    #linked-picture(item, picture-width, picture-height)
  ]
  #if item.at("caption", default: "") != "" {
    place(top + center, dy: title-height + picture-height + 2mm)[
      #image-caption(item, picture-width)
    ]
  }
]

// Advanced override: coordinates use the complete A5 page, with (0, 0) at
// the top-left, x increasing rightwards, and y increasing downwards.
#let absolute-image(item) = {
  let x0 = item.x0 * 1mm
  let y0 = item.y0 * 1mm
  let width = (item.x1 - item.x0) * 1mm
  let height = (item.y1 - item.y0) * 1mm
  place(top + left, dx: x0, dy: y0)[
    #linked-picture(item, width, height)
  ]
  if item.at("caption", default: "") != "" {
    place(top + left, dx: x0, dy: item.y1 * 1mm)[
      #image-caption(item, width)
    ]
  }
}

#let teams-link(item) = block(width: 100%)[
  #grid(
    columns: (teams-icon-size, 1fr), column-gutter: 3mm, align: horizon,
    image("../" + item.icon, width: teams-icon-size, height: teams-icon-size, fit: "contain"),
    block[
      #set text(font: body-font, size: 16pt, weight: "medium", fill: ink)
      #set par(leading: settings.spacing.teams_label_leading_pt * 1pt)
      Shared#linebreak()Files
    ],
  )
  #v(settings.spacing.teams_title_to_path_mm * 1mm)
  #set text(font: body-font, size: body-size, fill: ink)
  #set par(leading: body-leading, spacing: paragraph-spacing)
  #item.path.join(" → ") #sym.arrow.r
  #v(settings.spacing.teams_path_to_file_mm * 1mm)
  #text(fill: link-color)[#link(item.link)[#item.filename]]
]

#let teams-section(item, height) = block(width: 100%, height: height)[
  #if item.title != "" { section-title(item.title, before: item.before_mm * 1mm) } else { v(item.before_mm * 1mm) }
  #body-style[#paragraphs(item.body)]
  #v(settings.spacing.teams_before_mm * 1mm)
  #teams-link(item)
  #v(settings.spacing.teams_after_mm * 1mm)
  #if "body_after" in item and item.body_after.len() > 0 {
    v(3mm)
    body-style[#paragraphs(item.body_after)]
  }
]

#let profile-template(item, height) = block(width: 100%, height: height)[
  #section-title(item.title, before: item.before_mm * 1mm, alignment: "center")
  #body-style[#paragraphs(item.body)]
  #v(4mm)
  #let profile-cells = ()
  #for entry in item.render_items {
    profile-cells.push(bullet-column(item.chapter_color))
    profile-cells.push(box(width: 100%, height: entry.height_mm * 1mm)[#compact-body(entry.text)])
  }
  #grid(
    columns: (item.image_width_mm * 1mm, 1fr), column-gutter: 7mm, align: horizon,
    image("../" + item.image, width: item.image_width_mm * 1mm, height: item.image_height_mm * 1mm, fit: "contain"),
    grid(
      columns: ((settings.bullets.diameter_mm + settings.bullets.edge_to_text_mm) * 1mm, 1fr),
      column-gutter: 0mm, row-gutter: settings.spacing.profile_bullet_gap_mm * 1mm, align: top,
      ..profile-cells,
    ),
  )
]

#let margin-marmot(side, top-offset) = {
  let horizontal-offset = 9mm
  let adjusted-top = top-offset + settings.spacing.marmot_vertical_offset_mm * 1mm
  if side == "left" {
    place(top + left, dx: -horizontal-offset, dy: adjusted-top)[
      #image("../" + settings.images.marmot_asset, width: marmot-size, height: marmot-size, fit: "contain")
    ]
  } else {
    place(top + right, dx: horizontal-offset, dy: adjusted-top)[
      #image("../" + settings.images.marmot_asset, width: marmot-size, height: marmot-size, fit: "contain")
    ]
  }
}

#let render-block(item, side) = {
  let height = item.height_mm * 1mm
  if item.at("marked", default: false) {
    let before = item.at("before_mm", default: 0) * 1mm
    let title-box = if "title_box_mm" in item { item.title_box_mm * 1mm } else { settings.typography.subtitle_size_pt * 1pt }
    margin-marmot(side, before + (title-box - marmot-size) / 2 + item.at("marmot_offset_mm", default: 0.0) * 1mm)
  }
  if item.kind == "contents" {
    contents-block(item, height)
  } else if item.kind == "front_matter" {
    front-matter-block(item, height)
  } else if item.kind == "chapter_title" {
    chapter-title(
      item.title,
      after: item.title_after_mm * 1mm,
      alignment: item.title_align,
    )
  } else if item.kind == "section_heading" {
    section-title(item.title, before: item.before_mm * 1mm, alignment: item.title_align)
  } else if item.kind == "text_section" {
    block(width: 100%, height: height)[
      #if item.title != "" { section-title(item.title, before: item.before_mm * 1mm, alignment: item.title_align) } else { v(item.before_mm * 1mm) }
      #body-style[#paragraphs(item.body)]
      #if item.at("link_text", default: "") != "" {
        parbreak()
        body-style[
          #item.at("link_prefix", default: "")
          #text(fill: link-color)[#link(item.link_url)[#item.link_text]]
          #item.at("link_suffix", default: "")
        ]
      }
    ]
  } else if item.kind == "highlight_section" {
    block(width: 100%, height: height)[
      #v(item.before_mm * 1mm)
      #align(center)[
        #body-style[
          #set text(weight: if item.at("style", default: "bold") in ("bold", "bold-italic") { "bold" } else { "regular" },
                    style: if item.at("style", default: "bold") in ("italic", "bold-italic") { "italic" } else { "normal" })
          #paragraphs(item.body)
        ]
      ]
    ]
  } else if item.kind == "person" {
    person-card(item.person, item.side, height: height)
  } else if item.kind == "qr_section" {
    qr-section(item, height)
  } else if item.kind == "teams_section" {
    teams-section(item, height)
  } else if item.kind == "bullets_section" {
    bullets-section(item, height)
  } else if item.kind == "routing_section" {
    routing-section(item, height)
  } else if item.kind == "image_section" {
    image-section(item, height)
  } else if item.kind == "profile_template" {
    profile-template(item, height)
  }
}

#let corner-marker(number, color, side) = {
  box(width: 25mm, height: 25mm)[
    #if side == "left" {
      place(top + left)[#polygon((0mm, 0mm), (0mm, 25mm), (25mm, 25mm), fill: rgb(color), stroke: none)]
      place(bottom + left, dx: 4mm, dy: -3mm)[
        #set text(font: body-font, size: 18pt, fill: ink)
        #number
      ]
    } else {
      place(top + left)[#polygon((25mm, 0mm), (0mm, 25mm), (25mm, 25mm), fill: rgb(color), stroke: none)]
      place(bottom + right, dx: -4mm, dy: -3mm)[
        #set text(font: body-font, size: 18pt, fill: ink)
        #number
      ]
    }
  ]
}

#let logical-page(page-data, side) = box(width: 148.5mm, height: 210mm, fill: white)[
  #if page-data != none {
    for item in page-data.blocks {
      if item.kind == "absolute_image" { absolute-image(item) }
    }
    let left-margin = (if side == "left" { settings.geometry.even_left_mm } else { settings.geometry.odd_left_mm }) * 1mm
    let right-margin = (if side == "left" { settings.geometry.even_right_mm } else { settings.geometry.odd_right_mm }) * 1mm
    let top-margin = settings.geometry.top_mm * 1mm
    let content-height = settings.geometry.page_capacity_mm * 1mm
    let content-width = 148.5mm - left-margin - right-margin
    place(top + left, dx: left-margin, dy: top-margin)[
      #box(width: content-width, height: content-height)[
        #for item in page-data.blocks {
          if item.kind != "absolute_image" { render-block(item, side) }
        }
      ]
    ]
  }
]
