# Palabra del Día

An automated scraper that extracts the daily etymology newsletter from [elcastellano.org](https://www.elcastellano.org) (by Ricardo Soca) and serves it as a clean, ad-free **Atom feed**.

## Feed URL

```
https://raw.githubusercontent.com/backmind/Palabra-del-dia/main/feed.xml
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

[MIT](LICENSE)
