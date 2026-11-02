import pathlib
import shutil
import subprocess
import tempfile
import unittest

from bs4 import BeautifulSoup


ROOT = pathlib.Path(__file__).resolve().parents[1]
SLUG = "ODOS-Protocol-Exploit-Analysis"
RESEARCH_SLUG = "Hacking-Claude-Code-with-Claude-Code"


class BilingualBuildTest(unittest.TestCase):
    def test_posts_are_grouped_under_one_posts_directory(self):
        self.assertTrue((ROOT / "_posts/en" / f"2025-04-20-{SLUG}.md").exists())
        self.assertFalse((ROOT / "_posts/ko" / f"2025-04-20-{SLUG}.md").exists())
        self.assertTrue((ROOT / "_posts/ko" / f"2026-11-01-{RESEARCH_SLUG}.md").exists())
        self.assertFalse((ROOT / "ko/_posts").exists())

    @classmethod
    def setUpClass(cls):
        cls.output = tempfile.TemporaryDirectory()
        subprocess.run(
            ["ruby", "-r", "jekyll", "-e",
             'Jekyll::Commands::Build.process({"destination" => ARGV[0]})',
             cls.output.name],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.output.cleanup()

    def page(self, path):
        return BeautifulSoup(
            (pathlib.Path(self.output.name) / path / "index.html").read_text(),
            "html.parser",
        )

    def test_twin_posts_have_distinct_languages_and_reciprocal_links(self):
        en = self.page(f"blog/{RESEARCH_SLUG}")
        ko = self.page(f"ko/blog/{RESEARCH_SLUG}")
        self.assertEqual(en.html["lang"], "en")
        self.assertEqual(ko.html["lang"], "ko")
        self.assertEqual(en.select_one('.lang-switch a[hreflang="ko"]')["href"], f"/ko/blog/{RESEARCH_SLUG}/")
        self.assertEqual(ko.select_one('.lang-switch a[hreflang="en"]')["href"], f"/blog/{RESEARCH_SLUG}/")
        for page in (en, ko):
            alternates = {link["hreflang"]: link["href"] for link in page.select('link[rel="alternate"][hreflang]')}
            self.assertEqual(alternates["en"], f"https://bshyuunn.github.io/blog/{RESEARCH_SLUG}/")
            self.assertEqual(alternates["ko"], f"https://bshyuunn.github.io/ko/blog/{RESEARCH_SLUG}/")
            self.assertEqual(alternates["x-default"], alternates["en"])
            self.assertNotIn("ko", page.select_one(".meta .accent").get_text(strip=True).lower())
        self.assertEqual(ko.select_one(".toc-label").get_text(strip=True), "이 글의 목차")
        self.assertEqual(len(en.select(".prose h2, .prose h3")), len(ko.select(".prose h2, .prose h3")))

    def test_single_language_post_has_no_missing_language_link(self):
        page = self.page(f"blog/{SLUG}")
        self.assertEqual(page.select_one(".lang-switch").get_text(strip=True), "EN")
        self.assertIsNone(page.select_one(".lang-switch a"))
        self.assertFalse(page.select('link[rel="alternate"][hreflang]'))
        self.assertFalse((pathlib.Path(self.output.name) / "ko" / "blog" / SLUG).exists())

    def test_research_post_has_both_languages_and_local_figures(self):
        slug = "Hacking-Claude-Code-with-Claude-Code"
        for language, path, other in (("en", f"blog/{slug}", "ko"), ("ko", f"ko/blog/{slug}", "en")):
            page = self.page(path)
            self.assertEqual(page.html["lang"], language)
            self.assertEqual(page.select_one("h1").get_text(strip=True), "Hacking Claude Code with Claude Code")
            self.assertEqual(page.select_one(".meta .accent").get_text(strip=True), "Research")
            self.assertIsNotNone(page.select_one(f'.lang-switch a[hreflang="{other}"]'))
            images = page.select(".prose img")
            self.assertEqual(len(images), 9)
            self.assertTrue(all((pathlib.Path(self.output.name) / image["src"].lstrip("/")).is_file() for image in images))
            self.assertFalse(page.select(".prose strong"))
            headings = [heading.get_text(" ", strip=True) for heading in page.select(".prose h2, .prose h3")]
            self.assertEqual(len(headings), 15)
            self.assertIn("2.3. Understanding the Target", headings)
            self.assertIsNone(page.select_one(".paragraph-gap"))

    def test_korean_post_keeps_english_title(self):
        en = self.page(f"blog/{RESEARCH_SLUG}")
        ko = self.page(f"ko/blog/{RESEARCH_SLUG}")
        self.assertEqual(ko.select_one("h1").get_text(strip=True), en.select_one("h1").get_text(strip=True))

    def test_blog_language_switch_sits_beside_blog_title(self):
        page = self.page("blog")
        title_row = page.select_one(".page-head .blog-title-row")
        self.assertEqual(title_row.select_one("h1").get_text(strip=True), "Blog")
        self.assertEqual(title_row.select_one(".lang-switch").get_text(" ", strip=True), "EN / KO")
        self.assertIsNone(page.select_one(".page-head .blog-meta"))
        self.assertTrue(any("/assets/js/blog-lang.js?v=" in script.get("src", "") for script in page.select("script[src]")))

    def test_post_script_url_changes_with_build(self):
        page = self.page(f"blog/{SLUG}")
        scripts = [script.get("src", "") for script in page.select("script[src]")]
        self.assertTrue(any("/assets/js/toc.js?v=" in src for src in scripts))
        stylesheets = [link.get("href", "") for link in page.select('link[rel="stylesheet"]')]
        self.assertTrue(any("/assets/css/site.css?v=" in href for href in stylesheets))

    def test_major_sections_have_one_break_from_section_two_onward(self):
        posts = list((ROOT / "_posts/en").glob("*.md"))
        posts += list((ROOT / "_posts/ko").glob("*.md"))
        for post in posts:
            language = post.parent.name
            slug = post.stem[11:]
            path = f"ko/blog/{slug}" if language == "ko" else f"blog/{slug}"
            for index, heading in enumerate(self.page(path).select(".prose h2")):
                previous = heading.find_previous_sibling()
                is_break = previous is not None and previous.name == "p" and len(previous.find_all("br")) == 1 and not previous.get_text(strip=True)
                self.assertEqual(is_break, index > 0, f"{path}: section {index + 1}")

    def test_index_has_one_row_per_article_and_both_versions(self):
        page = self.page("blog")
        rows = page.select(".post-row")
        self.assertEqual(len(rows), 7)
        odos = next(row for row in rows if SLUG in row.get("data-href-en", ""))
        self.assertEqual(odos["data-href-ko"], "")
        self.assertEqual(odos.select_one(".lang-marker").get_text(strip=True), "· EN")
        research = next(row for row in rows if "Hacking-Claude-Code-with-Claude-Code" in row.get("data-href-en", ""))
        self.assertEqual(research["data-href-ko"], "/ko/blog/Hacking-Claude-Code-with-Claude-Code/")
        self.assertIn("#research", research.get_text())
        self.assertEqual(research.select_one(".lang-marker").get_text(strip=True), "· EN / KO")
        self.assertEqual(page.select_one(".page-head h1").get_text(strip=True), "Blog")
        self.assertTrue(all(row.select_one(".lang-marker") for row in rows))
        self.assertTrue(all(row.get("data-href-en") or row.get("data-href-ko") for row in rows))

    def test_korean_only_and_ref_pairing_in_temporary_site(self):
        with tempfile.TemporaryDirectory() as root:
            source = pathlib.Path(root) / "source"
            output = pathlib.Path(root) / "output"
            shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "_site", "__pycache__"))
            extra = {
                "_posts/ko/2025-05-01-korean-only.md": "---\nlayout: post\ntitle: 한국어 전용\ncategories: [Writeup]\n---\n\n## 첫 번째\n\n본문\n",
                "_posts/en/2025-05-03-english-ref.md": "---\nlayout: post\ntitle: English ref\nref: shared-ref\n---\n\n## First\n",
                "_posts/ko/2025-05-04-korean-ref.md": "---\nlayout: post\ntitle: 한국어 ref\nref: shared-ref\n---\n\n## 첫 번째\n",
            }
            for relative, body in extra.items():
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body)
            subprocess.run(
                ["ruby", "-r", "jekyll", "-e",
                 'Jekyll::Commands::Build.process({"destination" => ARGV[0]})', str(output)],
                cwd=source, check=True, capture_output=True, text=True,
            )

            index = BeautifulSoup((output / "blog/index.html").read_text(), "html.parser")
            self.assertEqual(len(index.select(".post-row")), 9)
            ko_only = next(row for row in index.select(".post-row") if "korean-only" in row.get("data-href-ko", ""))
            self.assertEqual(ko_only["data-href-en"], "")
            self.assertEqual(ko_only.select_one(".lang-marker").get_text(strip=True), "· KO")
            self.assertFalse(ko_only.has_attr("hidden"))
            ref_row = next(row for row in index.select(".post-row") if "english-ref" in row.get("data-href-en", ""))
            self.assertIn("korean-ref", ref_row["data-href-ko"])
            ko_page = BeautifulSoup((output / "ko/blog/korean-only/index.html").read_text(), "html.parser")
            nav = ko_page.select(".pn a")
            self.assertTrue(nav)
            self.assertTrue(all(link["href"].startswith("/ko/blog/") for link in nav))
            self.assertTrue(any("다음 글" in link.get_text() for link in nav))


if __name__ == "__main__":
    unittest.main()
