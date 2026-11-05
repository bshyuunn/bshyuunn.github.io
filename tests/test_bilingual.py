import pathlib
import shutil
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree

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

    def test_about_redirects_before_rendering(self):
        page = self.page("about")
        script = page.head.find("script")
        self.assertIsNotNone(script)
        self.assertIsNone(script.find_previous("body"))
        result = subprocess.run(
            ["node", "-e", "const vm = require('node:vm');"
             "const location = {replace: url => process.stdout.write(url)};"
             "vm.runInNewContext(process.argv[1], {location});", script.string],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual(result.stdout, "/")
        self.assertIsNotNone(page.head.find("meta", attrs={"http-equiv": "refresh"}))

    def test_single_language_post_has_no_missing_language_link(self):
        page = self.page(f"blog/{SLUG}")
        self.assertEqual(page.select_one(".lang-switch").get_text(strip=True), "EN")
        self.assertIsNone(page.select_one(".lang-switch a"))
        self.assertFalse(page.select('link[rel="alternate"][hreflang]'))
        self.assertFalse((pathlib.Path(self.output.name) / "ko" / "blog" / SLUG).exists())

    def test_research_post_is_published(self):
        output = pathlib.Path(self.output.name)
        self.assertTrue((output / "blog" / RESEARCH_SLUG).exists())
        self.assertTrue((output / "ko" / "blog" / RESEARCH_SLUG).exists())
        self.assertTrue(any(RESEARCH_SLUG in row.get("href", "") for row in self.page("blog").select(".post-row")))
        self.assertIn(RESEARCH_SLUG, (output / "feed.xml").read_text())

    def test_blog_index_has_no_language_switch(self):
        page = self.page("blog")
        self.assertEqual(page.select_one(".page-head h1").get_text(strip=True), "Blog")
        self.assertIsNone(page.select_one(".page-head .lang-switch"))
        self.assertFalse(any("blog-lang.js" in script.get("src", "") for script in page.select("script[src]")))

    def test_sitemap_lists_public_pages_and_language_versions(self):
        output = pathlib.Path(self.output.name)
        root = ElementTree.fromstring((output / "sitemap.xml").read_text())
        urls = {node.text for node in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
        self.assertIn("https://bshyuunn.github.io/", urls)
        self.assertIn("https://bshyuunn.github.io/blog/", urls)
        self.assertIn(f"https://bshyuunn.github.io/blog/{RESEARCH_SLUG}/", urls)
        self.assertIn(f"https://bshyuunn.github.io/ko/blog/{RESEARCH_SLUG}/", urls)
        self.assertFalse(any("hacking-with-artificial-intelligence" in url for url in urls))
        self.assertFalse(any("404" in url or "/about/" in url for url in urls))
        self.assertIn("Sitemap: https://bshyuunn.github.io/sitemap.xml", (output / "robots.txt").read_text())
        blog = self.page("blog")
        self.assertIn("Security research", blog.select_one('meta[name="description"]')["content"])

    def test_post_script_url_changes_with_build(self):
        page = self.page(f"blog/{SLUG}")
        scripts = [script.get("src", "") for script in page.select("script[src]")]
        self.assertTrue(any("/assets/js/toc.js?v=" in src for src in scripts))
        stylesheets = [link.get("href", "") for link in page.select('link[rel="stylesheet"]')]
        self.assertTrue(any("/assets/css/site.css?v=" in href for href in stylesheets))

    def test_talk_slides_link_to_pdfs_without_a_blog_post(self):
        page = self.page("")
        talk = next(section for section in page.select("section") if "Talk" in section.select_one("h2").get_text())
        rows = talk.select(".entry")
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row.select_one(".entry-top .date") for row in rows))
        self.assertFalse(talk.select(".entry-title a"))
        links = talk.select(".talk-links a")
        self.assertEqual([link.get_text(strip=True) for link in links], ["PDF", "PDF"])
        self.assertEqual([link["href"] for link in links], [
            "/assets/pdf/getting-started-with-smart-contract-audit-contests.pdf",
            "/assets/pdf/hacking-with-ai-reinforcement-learning.pdf",
        ])
        self.assertTrue(all((pathlib.Path(self.output.name) / link["href"].lstrip("/")).is_file() for link in links))
        self.assertFalse((pathlib.Path(self.output.name) / "blog/hacking-with-artificial-intelligence").exists())

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
        self.assertEqual(len(rows), 6)
        odos = next(row for row in rows if SLUG in row["href"])
        self.assertEqual(odos.select_one(".lang-marker").get_text(strip=True), "· EN")
        self.assertTrue(any(RESEARCH_SLUG in row["href"] for row in rows))
        self.assertEqual(page.select_one(".page-head h1").get_text(strip=True), "Blog")
        self.assertTrue(all(row.select_one(".lang-marker") for row in rows))
        self.assertTrue(all(row.get("href") for row in rows))

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
            self.assertEqual(len(index.select(".post-row")), 7)
            ko_only = next(row for row in index.select(".post-row") if "korean-only" in row["href"])
            self.assertEqual(ko_only.select_one(".lang-marker").get_text(strip=True), "· KO")
            self.assertFalse(ko_only.has_attr("hidden"))
            ref_row = next(row for row in index.select(".post-row") if "english-ref" in row["href"])
            self.assertEqual(ref_row.select_one(".lang-marker").get_text(strip=True), "· EN / KO")
            ko_page = BeautifulSoup((output / "ko/blog/korean-only/index.html").read_text(), "html.parser")
            nav = ko_page.select(".pn a")
            self.assertTrue(nav)
            self.assertTrue(all(link["href"].startswith("/ko/blog/") for link in nav))
            self.assertTrue(any("다음 글" in link.get_text() for link in nav))


if __name__ == "__main__":
    unittest.main()
