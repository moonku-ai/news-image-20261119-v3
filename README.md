# news-image-20261119-v3

[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/moonku-ai/news-image-20261119-v3/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/moonku-ai/news-image-20261119-v3/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

The World in One Day — a broadsheet front page summing up Thursday 19 November 2026 in one 1024x1024 image, drawn from scratch in pure Python (standard library only). Six verified stories of the day: the EU's 45bn euro loan for Ukraine, GTA VI's global rollout, Voyager 1 reaching one light-day, four nations demanding Gaza aid access, Eisenkot tapped to lead Israel, and Finland opening the world's first nuclear waste repository.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `out/entry.png` (1024x1024, under 1 MiB). Two runs write identical bytes.

## Tests

```sh
python3 -m unittest discover -s . -p "test_main.py" -v
```

---

<sub>Entered on [make.fun](https://make.fun/bounty/news-image-20261119)</sub>
