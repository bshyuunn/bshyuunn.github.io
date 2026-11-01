import pathlib
import subprocess
import tempfile
import unittest

from bs4 import BeautifulSoup


ROOT = pathlib.Path(__file__).resolve().parents[1]


class EnglishOnlyBlogTest(unittest.TestCase):
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

    def test_english_posts_use_standard_posts_directory(self):
        self.assertEqual(len(list((ROOT / "_posts").glob("*.md"))), 6)
        self.assertFalse((ROOT / "_posts/en").exists())
        self.assertFalse((ROOT / "_posts/ko").exists())

    def test_index_lists_all_posts_without_language_controls(self):
        page = self.page("blog")
        rows = page.select(".post-row")
        self.assertEqual(page.html["lang"], "en")
        self.assertEqual(page.select_one(".page-head h1").get_text(strip=True), "Blog")
        self.assertEqual(len(rows), 6)
        self.assertFalse(page.select(".lang-switch, .lang-marker"))
        self.assertFalse(page.select('script[src*="blog-lang.js"]'))
        self.assertTrue(all(row["href"].startswith("/blog/") for row in rows))

    def test_posts_have_english_urls_and_no_korean_alternates(self):
        for slug in ("ODOS-Protocol-Exploit-Analysis", "Hacking-Claude-Code-with-Claude-Code"):
            page = self.page(f"blog/{slug}")
            self.assertEqual(page.html["lang"], "en")
            self.assertFalse(page.select(".lang-switch, link[hreflang]"))
            self.assertFalse(page.select('a[href^="/ko/"]'))
            self.assertTrue(all(link["href"].startswith("/blog/") for link in page.select(".pn a")))
        self.assertFalse((pathlib.Path(self.output.name) / "ko").exists())

    def test_claude_code_article_and_images_remain(self):
        page = self.page("blog/Hacking-Claude-Code-with-Claude-Code")
        self.assertEqual(page.select_one("h1").get_text(strip=True), "Hacking Claude Code with Claude Code")
        self.assertIn("Hi! I’ve been researching vulnerabilities", page.select_one(".prose p").get_text())
        images = page.select(".prose img")
        self.assertEqual(len(images), 9)
        self.assertTrue(all((pathlib.Path(self.output.name) / image["src"].lstrip("/")).is_file() for image in images))


if __name__ == "__main__":
    unittest.main()
