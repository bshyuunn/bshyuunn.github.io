# Blog posts

Add each post directly under `_posts/` using a date and slug in its filename:

```text
_posts/2026-11-01-my-post.md    # /blog/my-post/
```

The blog is English only. Add a title, category, tags, and body to each post's front matter and content.

## Post style

Use one primary `categories` value per post:

- `Exploit Analysis` for real-world incidents and attack paths.
- `CTF Writeup` for challenge solutions.
- `Tool Development` for tools and templates built by the author.
- `Research` for technical or vulnerability research outside a specific incident or CTF solution.

Use the matching lowercase, hyphenated type as the first tag (`exploit-analysis`, `ctf-writeup`, `tool-development`, or `research`), followed by specific topics such as `evm`, `solidity`, or `proxy`. Keep `blockchain` as a topic tag when useful, not as the primary category.

Open with a short introduction that makes the post's subject and purpose clear.
