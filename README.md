# Baarle Map Short — production pack

A map-led vertical geography/history short using the visual language of the supplied British Empire reference: saturated cyan oceans, pale land, highlighted countries, geographic zooms, concise labels, numerical cards, and occasional dry visual jokes.

## Locked repository

**Only** `redk13/gradle` is used. The Colab notebook hard-codes this repository and refuses a different name. It never embeds a token. Create a fresh fine-grained GitHub token (the previously exposed token must be revoked) and save it in Google Colab Secrets as `GH_TOKEN`, with Contents: Read and write for this repository only.

## Project files

- `used_scripts.txt`: independent, append-only topic/script ledger.
- `config/baarle.json`: format, style, voice, facts, asset URLs and timings.
- `content/baarle_script.txt`: complete English voiceover, split into eight scene paragraphs.
- `src/pipeline.py`: Colab-only Chatterbox generation, BiRefNet-HR cutout, maps, visual scenes, audio mix, rendering and QA.
- `colab/BAARLE_SINGLE_CELL.ipynb`: one-code-cell Colab entry point. It reads the ledger first, checks duplicates, downloads this repository, runs TTS and background removal in Colab, renders the MP4 in Colab, then appends the script only after QA succeeds.
- `.github/workflows/ci.yml`: limited syntax and unit checks only.

## Hard separation

GitHub stores source code, narration, settings, manifest and tests. Chatterbox inference, BiRefNet-HR inference and final video rendering happen **only in Google Colab**. GitHub Actions does not generate content, download media, synthesize audio or render video.

## Run in Colab

1. Open `colab/BAARLE_SINGLE_CELL.ipynb`.
2. Set a GPU runtime.
3. Save a fresh fine-grained token as the Colab Secret `GH_TOKEN`.
4. Run the single code cell.
5. The MP4 is saved as `/content/BAARLE_Border_Through_Your_Bedroom_1080x1920_60fps.mp4` and downloaded after QA.

## Voice note

The official Chatterbox repository states that the project became retired research and is no longer maintained in August 2026, although the code and weights remain available under MIT. The notebook pins the upstream package version used by its documented API. Chatterbox's default speaker is used as requested; the default speaker is not a user-selected voice identity, so a male timbre cannot be guaranteed from the default alone. No reference voice is cloned and no audio is sped up to force a duration.

## Asset handling

Real photographs, the public-domain enclave SVG, country boundaries, music and recorded effects are fetched from the source pages listed in `SOURCES_AND_LICENSES.md`. The pipeline verifies page licence markers before use. Unavailable or unverified sources cause an explicit stop; it does not replace them with generated audio or unlicensed media.
