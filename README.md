# daily-lotus

[![Release](https://img.shields.io/github/v/release/oolonek/daily-lotus)](https://img.shields.io/github/v/release/oolonek/daily-lotus)
[![Build status](https://img.shields.io/github/actions/workflow/status/oolonek/daily-lotus/main.yml?branch=main)](https://github.com/oolonek/daily-lotus/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/oolonek/daily-lotus/branch/main/graph/badge.svg)](https://codecov.io/gh/oolonek/daily-lotus)
[![Commit activity](https://img.shields.io/github/commit-activity/m/oolonek/daily-lotus)](https://img.shields.io/github/commit-activity/m/oolonek/daily-lotus)
[![License](https://img.shields.io/github/license/oolonek/daily-lotus)](https://img.shields.io/github/license/oolonek/daily-lotus)

This is a Python bot for daily_lotus account on Mastodon

- **Github repository**: <https://github.com/oolonek/daily-lotus/>
- **Documentation** <https://oolonek.github.io/daily-lotus/>

# 🤖 daily_lotus bot

**daily_lotus** is a Python bot that toots daily natural products occurrences on Mastodon, via the account [@daily_lotus](https://mastodon.social/@daily_lotus).
It highlights natural compounds found in plants, fungi, bacteria or animals — and includes Wikidata references and visual structure depictions.

The aim is to raise awareness on the hidden chemical diversity of life on Earth and the importance of open data in bio and chemodiversity research.

We also expect that by putting side by side the structure of the molecule, a picture of the taxon and the references backing up the occurence this can serve as an entry point for researchers willing to contribute to the LOTUS Initiative and edit Wikidata.

The bot is part of the [LOTUS Initiative](https://lotus.nprod.net/) and is powered by [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page) and the [Cheminformatics Microservice](https://docs.api.naturalproducts.net/).
The bot is designed to be run daily, but you can also run it manually or in a dry-run mode to preview the output without posting.



## 🛠️ What does it do?

Every day at 8:00 AM, the bot:

1. Selects a random molecule from [Wikidata](https://www.wikidata.org/wiki/) that:
   - Has a known SMILES structure (so we can draw it)
   - Is associated with a specific taxon trhough the find in taxon property ([P703](https://www.wikidata.org/wiki/Property:P703))
   - Has a valid reference documenting this occurrence

2. Fetches:
   - The molecule’s name and it's SMILES structure. The structure is depicted via the [Cheminformatics Microservice](https://docs.api.naturalproducts.net/)
   - The taxon name (e.g., _Curcuma longa_) and its associated image are retrieved via the taxonLabel and the [P18](https://www.wikidata.org/wiki/Property:P18) property.
   - The scientific publication that supports the occurrence is retrieved via the P248 property.
   - The taxon kingdom is retrieved traversing the taxon tree via the [P171](https://www.wikidata.org/wiki/Property:P171) property and searching for Plantae ([Q756](https://www.wikidata.org/wiki/Q756)), Fungi ([Q764](https://www.wikidata.org/wiki/Q754)), Animalia ([Q729](https://www.wikidata.org/wiki/Q729)) or Bacteria ([Q10876](https://www.wikidata.org/wiki/Q10876)).
    - The taxon kingdom is used to select the emoji to be used in the post.


3. Posts a formatted message to Mastodon with:
   - 🧪 Molecule
   - 🌿 or 🍄 or 🐛 or 🦠 depending on the organism's kingdom
   - 📚 Reference
   - ✏️ A note that readers can help improve the data via Wikidata



## 🗒️ Example Post

```bash
📣 Natural Product Occurrence of the Day

🧪 (-)-verbenone [https://www.wikidata.org/wiki/Q6535827] is a molecule
found in a 🌿 plant, Thymus camphoratus [https://www.wikidata.org/wiki/Q145377]
📚 according to: Composition and infraspecific variability of essential oil from Thymus camphoratus [https://www.wikidata.org/wiki/Q58423750]

✏️ This occurrence is curated in the frame of the LOTUS Initiative and is available on Wikidata [https://www.wikidata.org/wiki/]. If you spot an error, feel free to improve it!
````


## 🚀 How to run it

### One-time setup

Install dependencies using [uv](https://github.com/astral-sh/uv):

```bash
uv pip install -e .
```


Then copy .env.example to .env and fill in your Mastodon API credentials:

```bash
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=...
```

Run the bot manually


```bash
uv run run_bot.py
```

To preview the output without posting:

```bash
uv run run_bot.py --dry-run
```

Automate daily posting

To schedule daily runs at 8:00 AM:

```bash
crontab -e
```
Add this line:

```bash
0 8 * * * cd /full/path/to/daily-lotus && uv run run_bot.py >> logs/daily_lotus.log 2>&1
```

For the check_edits.py script, you can run it manually or schedule it with cron as well.

```bash
*/5 * * * * cd /path/to/daily-lotus && uv run daily_lotus/check_edits.py >> logs/check_edits.log 2>&1
```


## Roadmap

- [ ] Add a command line interface (CLI) to to run the bot with different parameters (e.g., focussed taxonomic groups, etc.)

- [ ] Display 3D structures

- [x] Check randomization of the input molecule selection.
Simply dropped the initial LIMIT, the query is anyway runned once a day, we can wait for a pair of seconds and fetch the full LOTUS

- [x] Add a direct link to the found in taxon property and ref of the molecule page on Wikidata (for curation purposes)

Used the #P703 (e.g. https://www.wikidata.org/wiki/Q27290462#P703) anchor tag. Not sure if we can directly redirect to the taxon though ...

- [x] Add relevant #

- [ ] Prepare a Streamlit app to display the same information (structures, taxon image and references) but without waiting for the daily run. This could be a first iteration for a curation interface for LOTUS data


## 🧬 Credits & contribution

This bot is powered by:

- [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page) - the free knowledge base that anyone can edit

- [The LOTUS Initiative](https://lotus.nprod.net/) see also [LOTUS on Wikidata](https://lotus.nprod.net/) - a collaborative effort to curate natural product occurrences. Overview available in the [LOTUS paper](https://doi.org/10.7554%2FELIFE.70780)

- [Cheminformatics Microservice](https://docs.api.naturalproducts.net/)

- [Mastodon.py](https://mastodonpy.readthedocs.io/en/stable/) - a Python wrapper for the Mastodon API


Made with ❤️ by researchers committed to open data, chemistry, and biodiversity.
If you want to contribute, please fork the repository and create a pull request with your changes.
If you want to add a new feature, please open an issue first to discuss it.
If you have any questions, please open an issue.

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
