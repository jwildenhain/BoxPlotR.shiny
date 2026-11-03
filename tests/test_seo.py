#!/usr/bin/env python3
"""Regression checks for BoxPlotR's crawlable search-engine content."""

from html.parser import HTMLParser
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"
BASE_URL = "https://boxplotr.chemgrid.org"
GUIDES = {
    "box-plot-generator.html": f"{BASE_URL}/box-plot-generator.html",
    "violin-plot-generator.html": f"{BASE_URL}/violin-plot-generator.html",
    "publication-ready-plots.html": f"{BASE_URL}/publication-ready-plots.html",
    "box-plot-whiskers.html": f"{BASE_URL}/box-plot-whiskers.html",
    "mcp-guide.html": f"{BASE_URL}/mcp-guide.html",
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self.meta = {}
        self.canonical = None
        self.h1_count = 0
        self.links = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = values.get("name") or values.get("property")
            if key:
                self.meta[key] = values.get("content", "")
        elif tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"])
        elif tag == "img":
            self.images.append(values)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def parse_page(filename):
    parser = PageParser()
    parser.feed((WWW / filename).read_text(encoding="utf-8"))
    return parser


class SeoTests(unittest.TestCase):
    def test_guides_have_unique_search_metadata(self):
        titles = set()
        descriptions = set()

        for filename, expected_canonical in GUIDES.items():
            with self.subTest(filename=filename):
                page = parse_page(filename)
                self.assertTrue(page.title.strip())
                self.assertNotIn(page.title.strip(), titles)
                titles.add(page.title.strip())

                description = page.meta.get("description", "").strip()
                self.assertGreaterEqual(len(description), 50)
                self.assertNotIn(description, descriptions)
                descriptions.add(description)

                self.assertEqual(page.canonical, expected_canonical)
                self.assertIn("index", page.meta.get("robots", ""))
                self.assertEqual(page.h1_count, 1)

                for image in page.images:
                    self.assertTrue(image.get("alt", "").strip())

    def test_internal_guide_links_resolve(self):
        for filename in GUIDES:
            page = parse_page(filename)
            for href in page.links:
                if href.startswith(("http://", "https://", "mailto:", "#", "/")):
                    continue
                target = (WWW / href.split("#", 1)[0]).resolve()
                with self.subTest(page=filename, href=href):
                    self.assertTrue(target.is_relative_to(WWW.resolve()))
                    self.assertTrue(target.exists())

    def test_sitemap_contains_home_and_every_guide(self):
        root = ET.parse(WWW / "sitemap.xml").getroot()
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = {node.text for node in root.findall("s:url/s:loc", namespace)}
        expected = {f"{BASE_URL}/", *GUIDES.values()}
        self.assertEqual(locations, expected)

    def test_robots_points_to_sitemap(self):
        robots = (WWW / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn(f"Sitemap: {BASE_URL}/sitemap.xml", robots)

    def test_dynamic_homepage_declares_core_metadata(self):
        source = (ROOT / "ui.R").read_text(encoding="utf-8")
        self.assertIn('name = "description"', source)
        self.assertIn('name = "robots"', source)
        self.assertIn('rel = "canonical"', source)
        self.assertIn('property = "og:title"', source)
        self.assertIn('type = "application/ld+json"', source)
        for filename in GUIDES:
            if filename != "mcp-guide.html":
                self.assertIn(filename, source)

    def test_box_plot_guide_has_verified_video_metadata(self):
        source = (WWW / "box-plot-generator.html").read_text(encoding="utf-8")
        self.assertIn('"@type": "VideoObject"', source)
        self.assertIn('"duration": "PT6M46S"', source)
        self.assertIn("youtube-nocookie.com/embed/ls9N6Yp9tRQ", source)
        for video_id in (
            "ls9N6Yp9tRQ",
            "N8u5zOyjyZc",
            "Xf6GGZ7hI50",
            "MgCULTRpQdA",
            "8iQwmuEraRs",
        ):
            self.assertIn(f"youtube.com/watch?v={video_id}", source)


if __name__ == "__main__":
    unittest.main()
