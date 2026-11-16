# Baarle short — sources, facts and licences

## Official factual references

- **Visit Baarle — 30 enclaves, 2 municipalities, 2 countries:** https://en.visitbaarle.com/locaties/enclaves-5e43f39e38374665355357fe
  - States there are 30 enclaves: 22 Belgian and 8 Dutch; seven Dutch enclaves lie in the two largest Belgian enclaves. It says enclave lines run through streets, houses and even bedrooms. The enclave numbers were assigned when the enclaves were officially raised to national borders in 1995.
- **Visit Baarle — History:** https://en.visitbaarle.com/informatie/geschiedenis
  - Explains the 1198 conflict and land deal involving Duke Hendrik I of Brabant and Godfried II, Lord of Breda; the 1648 Treaty of Münster gave the enclaves international status; the Belgium–Netherlands border was described in 1843; the gap was closed in 1974; the last enclave borders were officially established and recognised as national borders in 1995.
- **Visit Baarle — House with two house numbers:** https://en.visitbaarle.com/locaties/huis-met-2-huisnummers-5b4718d02a5ab0a4b22cec35
  - The house has Belgian house number 2 and Dutch house number 19. The international border passes through the middle of the front door; the location of the main entrance determines the residents' domicile.
- **Natural Earth — 1:110m Admin 0 Countries:** https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/
  - Used as a general country outline layer only. Natural Earth vectors are public domain.

## Map artwork

- **File:** Baarle-Nassau - Baarle-Hertog-en.svg.
- **Author:** Tos.
- **Source:** https://commons.wikimedia.org/wiki/File:Baarle-Nassau_-_Baarle-Hertog-en.svg
- **Licence:** Public domain, as marked on the source file.
- **Direct asset:** https://commons.wikimedia.org/wiki/Special:FilePath/Baarle-Nassau_-_Baarle-Hertog-en.svg

## Photographs

1. **House Shared By Two Countries.jpg**
   - Creator: Jack Soley.
   - Source: https://commons.wikimedia.org/wiki/File:House_Shared_By_Two_Countries.jpg
   - Licence: Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0).
   - Direct asset: https://commons.wikimedia.org/wiki/Special:FilePath/House_Shared_By_Two_Countries.jpg
2. **Baarle-Hertog and Baarle-Nassau border.jpg**
   - Creator: Kayfabebaale.
   - Source: https://commons.wikimedia.org/wiki/File:Baarle-Hertog_and_Baarle-Nassau_border.jpg
   - Licence: Creative Commons Attribution 4.0 International (CC BY 4.0).
   - Direct asset: https://commons.wikimedia.org/wiki/Special:FilePath/Baarle-Hertog_and_Baarle-Nassau_border.jpg
3. **B-NL International Border at Baarle.jpg**
   - Creator: Jack Soley.
   - Source: https://commons.wikimedia.org/wiki/File:B-NL_International_Border_at_Baarle.jpg
   - Licence: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
   - Direct asset: https://commons.wikimedia.org/wiki/Special:FilePath/B-NL_International_Border_at_Baarle.jpg
4. **Baarle-Hertog Loveren 2 - 150095 - onroerenderfgoed.jpg** (alternate cutout candidate)
   - Creator: Vlaamse Gemeenschap.
   - Source: https://commons.wikimedia.org/wiki/File:Baarle-Hertog_Loveren_2_-_150095_-_onroerenderfgoed.jpg
   - Licence: Creative Commons Attribution 4.0 International (CC BY 4.0).
   - Direct asset: https://commons.wikimedia.org/wiki/Special:FilePath/Baarle-Hertog_Loveren_2_-_150095_-_onroerenderfgoed.jpg

Attribution is retained in the final credits and this file. Altered CC BY-SA photographs remain subject to the applicable ShareAlike terms. No creator is represented as endorsing the video.

## Real recorded music and SFX

All sound files are real catalogue recordings downloaded as direct files into temporary Google Colab storage. The pipeline does not generate music or sound effects with code and does not scrape music storefront pages.

### Music

- **“Secret Garden” — Eugenio Mininni**, a playful plucked-string film-score track selected for the dry-comedy tone.
- Official Mixkit catalogue: https://mixkit.co/free-stock-music/mood/humorous/
- Direct file used by Colab: https://assets.mixkit.co/music/preview/mixkit-secret-garden-595.mp3
- Licence: **Mixkit Stock Music Free License**: https://mixkit.co/license/modal/musicFree/
- Mixkit allows its free music in social-media video posts, educational videos, online advertisements and YouTube videos; attribution is not required. A voluntary credit is retained in the final screen and this file.

### Recorded sound effects

- **“Air woosh”** — Mixkit; direct file: https://assets.mixkit.co/active_storage/sfx/1489/1489-preview.mp3
  - Catalogue: https://mixkit.co/free-sound-effects/whoosh/
  - Licence: Mixkit Sound Effects Free License: https://mixkit.co/license/modal/sfxFree/
- **“Stiff paper book paging”** — Mixkit; direct file: https://assets.mixkit.co/active_storage/sfx/1103/1103-preview.mp3
  - Catalogue: https://mixkit.co/free-sound-effects/paper/
  - Licence: Mixkit Sound Effects Free License.
- **“Footsteps on heels on the pavement”** — Mixkit; direct file: https://assets.mixkit.co/active_storage/sfx/542/542-preview.mp3
  - Catalogue: https://mixkit.co/free-sound-effects/footsteps/
  - Licence: Mixkit Sound Effects Free License.

The Mixkit SFX free licence permits use in social-media videos, YouTube, educational and commercial projects; attribution is appreciated but not required. The assets are incorporated into a larger edited video and are not redistributed as standalone stock. If any direct URL returns an error or an HTML page instead of an audio file, the Colab run stops rather than generating a replacement sound.


## Software and model licences

- **Chatterbox TTS:** https://github.com/resemble-ai/chatterbox — MIT. Upstream states that Chatterbox became retired research and is no longer maintained as of August 2026. Package API reference: https://huggingface.co/ResembleAI/chatterbox
- **BiRefNet-HR:** https://huggingface.co/ZhengPeng7/BiRefNet_HR — MIT; model card specifies 2048×2048 high-resolution inference.
- **FFmpeg:** https://ffmpeg.org/ — used only in Colab for the final H.264/AAC render.
