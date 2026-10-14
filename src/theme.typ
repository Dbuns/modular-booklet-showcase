#let settings = toml("../content/theme.toml")

#let ink = rgb(settings.colors.ink)
#let rule-color = rgb(settings.colors.rule)
#let link-color = rgb(settings.colors.link)
#let body-font = settings.typography.body_font
#let title-font = settings.typography.title_font
#let subtitle-font = settings.typography.subtitle_font
#let body-size = settings.typography.body_size_pt * 1pt
#let body-leading = (settings.typography.body_leading_pt - settings.typography.body_size_pt) * 1pt
#let paragraph-spacing = settings.typography.paragraph_after_pt * 1pt
#let title-size = settings.typography.title_size_pt * 1pt
#let title-leading = (settings.typography.title_leading_pt - settings.typography.title_size_pt) * 1pt
#let subtitle-size = settings.typography.subtitle_size_pt * 1pt
#let subtitle-leading = (settings.typography.subtitle_leading_pt - settings.typography.subtitle_size_pt) * 1pt
#let person-size = settings.images.person_mm * 1mm
#let teams-icon-size = settings.images.teams_icon_mm * 1mm
#let marmot-size = settings.images.marmot_mm * 1mm
#let subtitle-after = settings.spacing.subtitle_after_mm * 1mm

#let body-style(body) = {
  set text(font: body-font, size: body-size, fill: ink)
  set par(leading: body-leading, spacing: paragraph-spacing, justify: true)
  body
}

#let chapter-title(title, after: 0mm, alignment: "left") = block(width: 100%)[
  #set text(font: title-font, size: title-size, weight: "bold", fill: ink)
  #set par(leading: title-leading)
  #if alignment == "center" { align(center)[#title] } else { title }
  #v(after)
]

#let section-title(title, before: 0mm, alignment: "left", after: subtitle-after) = block(width: 100%)[
  #v(before)
  #set text(font: subtitle-font, size: subtitle-size, weight: "medium", fill: ink)
  #set par(leading: subtitle-leading)
  #if alignment == "center" { align(center)[#title] } else { title }
  #v(after)
]
