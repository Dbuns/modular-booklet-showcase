#import "src/modules.typ": logical-page, corner-marker, cover-spread

#let data = json("generated/book.json")

#set page(width: 297mm, height: 210mm, margin: 0mm, fill: rgb("#F7F7F6"))
#set text(font: "Arial")

#if "cover" in data.book {
  cover-spread(data.book.cover)
  pagebreak()
}

#if data.at("contents_page", default: none) != none {
  grid(
    columns: (148.5mm, 148.5mm), rows: (210mm,), column-gutter: 0mm,
    logical-page(none, "left"),
    box(width: 148.5mm, height: 210mm)[
      #place(left)[#line(start: (0mm, 0mm), end: (0mm, 210mm), stroke: 0.35pt + rgb("#B8B6B3"))]
      #logical-page(data.contents_page, "right")
    ],
  )
  pagebreak()
}

#for (index, spread) in data.spreads.enumerate() {
  grid(
    columns: (148.5mm, 148.5mm),
    rows: (210mm,),
    column-gutter: 0mm,
    logical-page(spread.left, "left"),
    box(width: 148.5mm, height: 210mm)[
      #place(left)[#line(start: (0mm, 0mm), end: (0mm, 210mm), stroke: 0.35pt + rgb("#B8B6B3"))]
      #logical-page(spread.right, "right")
    ],
  )
  place(bottom + left)[
    #grid(
      columns: (148.5mm, 148.5mm),
      align(left)[
        #if spread.left != none and spread.left.at("show_marker", default: true) {
          corner-marker(spread.left.number, spread.left.chapter_color, "left")
        }
      ],
      align(right)[
        #if spread.right != none and spread.right.at("show_marker", default: true) {
          corner-marker(spread.right.number, spread.right.chapter_color, "right")
        }
      ],
    )
  ]
  if index + 1 < data.spreads.len() { pagebreak() }
}
