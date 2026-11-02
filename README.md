# Blog posts

All posts live under `_posts/`, grouped by language. Give translations the same date and slug in their filenames:

```text
_posts/en/2026-11-01-my-post.md    # English → /blog/my-post/
_posts/ko/2026-11-01-my-post.md    # Korean  → /ko/blog/my-post/
```

The site pairs posts with the same Jekyll `slug` and different `lang`. If the filenames must differ, set the same `ref:` in both posts' front matter. Language and Korean permalink defaults are set in `_config.yml`; each post still needs its own title, tags, categories, and body. A post with only one file shows its language without a switch link.

The blog index always shows every article. EN and KO choose the preferred version of bilingual posts; single-language posts remain visible with a small language label. The selected language is remembered in the browser; `/blog/?lang=ko` opens the Korean view directly.

Keep the `##` and `###` heading order the same in translations so the language switch can preserve the reader's section. The ODOS post is English only.

## Post style

Use one primary `categories` value per post:

- `Exploit Analysis` for real-world incidents and attack paths.
- `CTF Writeup` for challenge solutions.
- `Tool Development` for tools and templates built by the author.
- `Research` for technical or vulnerability research outside a specific incident or CTF solution.

Use the matching lowercase, hyphenated type as the first tag (`exploit-analysis`, `ctf-writeup`, `tool-development`, or `research`), followed by specific topics such as `evm`, `solidity`, or `proxy`. Keep `blockchain` as a topic tag when useful, not as the primary category.

Write each introduction in the voice and structure that fits the post. For an unfinished translation, state its draft status clearly.

Do not add a `<br>` before the first `##` section. Put exactly one standalone `<br>` before each later `##` section; keep `###` subsections within their parent section.

To embed a PDF in a post, put it under `assets/pdf/`, use an `<iframe>` inside a `pdf-viewer` div, and add a normal link to the PDF beneath it. This lets readers open or download the file if their browser does not display embedded PDFs.
