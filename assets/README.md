# Source media

The repository stores source links, creator names, verified licence terms and use notes in `config/baarle.json` and `SOURCES_AND_LICENSES.md`.

The original photographs and enclave map are resolved at run time through Wikimedia Commons' official imageinfo API; the returned upload.wikimedia.org media URLs and API licence metadata are used in temporary Google Colab storage. A descriptive project User-Agent is sent, and no Commons file-description page is scraped. Natural Earth boundaries are fetched into temporary Google Colab storage. All music and sound effects use direct Mixkit CDN files; no Pixabay or Freesound storefront pages are scraped. Audio is not stored in GitHub, synthesized, cropped or rendered there. BiRefNet-HR inference is run only in Colab.
