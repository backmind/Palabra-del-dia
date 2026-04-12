# Palabra del Día

An Atom feed wrapper for [**La Palabra del Día**](https://www.elcastellano.org), the daily Spanish etymology newsletter by Ricardo Soca.

## Why this project

Ricardo Soca has been publishing *La Palabra del Día* for over two decades — a remarkable effort to document and share the origins of Spanish words. His newsletter is one of the longest-running etymology resources in the Spanish-speaking world, and this project exists thanks to his work.

For many years the newsletter arrived as a self-contained email: open it, read it, done. Around 2020 the format changed to a short teaser linking to the website, which today is heavily loaded with advertising. For readers who prefer a distraction-free experience through an RSS/Atom feed reader, this project provides exactly that.

**This is a wrapper, not a replacement.** All content belongs to Ricardo Soca and elcastellano.org. Every entry links back to the original page and attributes the author. If you enjoy the content, [subscribe to the original newsletter](https://www.elcastellano.org/suscripciones) — it's free, and it's the best way to support Ricardo Soca's work directly.

## Feed URL

```
https://backmind.github.io/Palabra-del-dia/feed.xml
```

Add this URL to your favourite feed reader (Feedly, Miniflux, Inoreader, etc.).

## What's included

Each feed entry contains the four sections of the daily newsletter:

| Section | Description |
|---|---|
| **La Palabra del Día** | Word of the day with its etymology and illustration |
| **El Medievalismo del Día** | An archaic Spanish word and its definition |
| **Píldoras de Lenguaje** | Language tips in Q&A format |
| **El Latín del Día** | A Latin quote with its Spanish translation |

## How it works

A GitHub Actions workflow runs every 6 hours (Monday–Friday). It fetches the daily page from `elcastellano.org/envios/YYYY-MM-DD-000000`, extracts the clean content using BeautifulSoup, and appends it to the Atom feed. The feed keeps the last 90 entries.

## Run locally

Requires [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run python src/scraper.py
```

## License

[MIT](LICENSE) — applies to the scraper code only. The newsletter content is property of Ricardo Soca / elcastellano.org.
