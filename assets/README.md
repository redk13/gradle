# Source media

The repository stores source links, creator names, verified licence terms and use notes in `config/baarle.json` and `SOURCES_AND_LICENSES.md`.

The original photographs, enclave map, Natural Earth boundaries, Pixabay music and recorded Freesound effects are retrieved from their named official pages only at run time into temporary Google Colab storage. They are not cropped or rendered on GitHub. BiRefNet-HR inference is run only in Colab. The pipeline checks licence-page markers before use and stops if a source is missing or its expected licence cannot be confirmed.
