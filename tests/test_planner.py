import copy
import unittest

import planner


class PlannerRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = planner.load_metadata()
        planner.validate(cls.data)
        cls.theme = cls.data["theme"]

    def test_supported_relationships_have_theme_values(self):
        adaptive = self.theme["adaptive_layout"]
        for key in planner.RELATIONSHIP_SPACING_KEYS.values():
            self.assertIn(key, adaptive)

    def test_relationship_spacing_is_deterministic(self):
        expected = {
            "standard": self.theme["spacing"]["section_before_mm"],
            "attached": 0.0,
            "continuation": 0.0,
            "related": 2.0,
            "relaxed": 6.0,
            "spacious": 7.0,
        }
        for relationship, gap in expected.items():
            section = {"type": "text", "relationship": relationship}
            self.assertEqual(planner.resolved_section_before(section, 1, self.theme), gap)

    def test_first_section_has_no_leading_gap(self):
        section = {"type": "text", "relationship": "spacious"}
        self.assertEqual(planner.resolved_section_before(section, 0, self.theme), 0.0)

    def test_invalid_relationship_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["chapters"][0]["sections"][0]["relationship"] = "mystery"
        with self.assertRaisesRegex(ValueError, "Unsupported relationship"):
            planner.validate(data)

    def test_all_current_chapters_fit_within_page_capacity(self):
        capacity = float(self.theme["geometry"]["page_capacity_mm"])
        next_page = int(self.data["book"].get("start_page", 1))
        for chapter in self.data["chapters"]:
            pages, next_page = planner.pack_chapter(chapter, self.theme, capacity, next_page)
            self.assertTrue(pages)
            self.assertTrue(all(page["used_mm"] <= capacity for page in pages))


if __name__ == "__main__":
    unittest.main()
