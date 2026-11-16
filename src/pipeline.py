"""Colab-only video pipeline. No synthesis, cutout or render runs on GitHub."""
from __future__ import annotations

import json, math, random, subprocess, textwrap
from pathlib import Path
import numpy as np
import requests
import soundfile as sf
import torch
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from shapely.geometry import shape, box, Polygon, MultiPolygon, GeometryCollection

W, H, FPS = 1080, 1920, 60
CW, CH = W * 2, H * 2
C = {"ocean":"#69D5E9","land":"#F7FBFF","ink":"#172D55","be":"#F3B33D","nl":"#8E66D9","accent":"#FF6A4A","dark":"#10223E","white":"#FFFFFF"}
ASSET_URLS = {
 "map":"https://commons.wikimedia.org/wiki/Special:FilePath/Baarle-Nassau_-_Baarle-Hertog-en.svg",
 "house":"https://commons.wikimedia.org/wiki/Special:FilePath/House_Shared_By_Two_Countries.jpg",
 "house_alt":"https://commons.wikimedia.org/wiki/Special:FilePath/Baarle-Hertog_Loveren_2_-_150095_-_onroerenderfgoed.jpg",
 "shop":"https://commons.wikimedia.org/wiki/Special:FilePath/Baarle-Hertog_and_Baarle-Nassau_border.jpg",
 "pavement":"https://commons.wikimedia.org/wiki/Special:FilePath/B-NL_International_Border_at_Baarle.jpg",
 "geo":"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
}
# Direct file downloads avoid scraping pages that may reject Colab with HTTP 403.
# The Mixkit track and SFX are real recorded catalogue assets; no audio is synthesized.
MIXKIT_FILES = {
 "music": {
  "url":"https://assets.mixkit.co/music/preview/mixkit-secret-garden-595.mp3",
  "source":"https://mixkit.co/free-stock-music/mood/humorous/",
  "title":"Secret Garden — Eugenio Mininni",
  "license":"Mixkit Stock Music Free License"
 },
 "whoosh": {
  "url":"https://assets.mixkit.co/active_storage/sfx/1489/1489-preview.mp3",
  "source":"https://mixkit.co/free-sound-effects/whoosh/",
  "title":"Air woosh",
  "license":"Mixkit Sound Effects Free License"
 },
 "paper": {
  "url":"https://assets.mixkit.co/active_storage/sfx/1103/1103-preview.mp3",
  "source":"https://mixkit.co/free-sound-effects/paper/",
  "title":"Stiff paper book paging",
  "license":"Mixkit Sound Effects Free License"
 },
 "footstep": {
  "url":"https://assets.mixkit.co/active_storage/sfx/542/542-preview.mp3",
  "source":"https://mixkit.co/free-sound-effects/footsteps/",
  "title":"Footsteps on heels on the pavement",
  "license":"Mixkit Sound Effects Free License"
 }
}

LICENCE_MARKERS = {
 "https://commons.wikimedia.org/wiki/File:Baarle-Nassau_-_Baarle-Hertog-en.svg":["Public domain"],
 "https://commons.wikimedia.org/wiki/File:House_Shared_By_Two_Countries.jpg":["Attribution-ShareAlike 3.0","CC BY-SA 3.0"],
 "https://commons.wikimedia.org/wiki/File:Baarle-Hertog_and_Baarle-Nassau_border.jpg":["Attribution 4.0","CC BY 4.0"],
 "https://commons.wikimedia.org/wiki/File:B-NL_International_Border_at_Baarle.jpg":["Attribution-ShareAlike 4.0","CC BY-SA 4.0"],
 "https://commons.wikimedia.org/wiki/File:Baarle-Hertog_Loveren_2_-_150095_-_onroerenderfgoed.jpg":["Attribution 4.0","CC BY 4.0"]
}
SCRIPT_TITLE = "Baarle: The Border That Runs Through Your Front Door"

class PipelineError(RuntimeError):
    pass

def run_cmd(args):
    p = subprocess.run(args, text=True, capture_output=True)
    if p.returncode:
        raise PipelineError("Command failed: " + " ".join(args[:7]) + "\n" + p.stderr[-3500:])

def seed_all(seed=42):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

def get(url, timeout=90):
    headers = {
        "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36",
        "Accept":"*/*"
    }
    last_error = None
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if r.status_code in (429,500,502,503,504) and attempt < 2:
                import time; time.sleep(2 ** attempt); continue
            if r.status_code == 403:
                raise PipelineError(
                    "The media host denied this request (HTTP 403). The pipeline now uses direct Mixkit CDN "
                    "files instead of the Pixabay storefront. Check the exact source URL and retry from Colab: " + url
                )
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 2:
                import time; time.sleep(2 ** attempt)
    raise PipelineError(f"Download failed after retries for {url}: {last_error}")

def verify_licences():
    # Image-source licences are checked against their Wikimedia file pages.
    for page, markers in LICENCE_MARKERS.items():
        html = get(page, 60).text.lower()
        if not any(m.lower() in html for m in markers):
            raise PipelineError("Expected public licence marker not found; stop and review: " + page)
    # Mixkit's free music and SFX catalogues have separate official licences.
    # Their direct CDN files are used, so Colab does not need to scrape the
    # Mixkit storefront (the former Pixabay page scrape returned HTTP 403).
    if any("Mixkit Stock Music Free License" not in x["license"] for k,x in MIXKIT_FILES.items() if k == "music"):
        raise PipelineError("Music asset is not marked with the Mixkit Stock Music Free License.")
    if any("Mixkit Sound Effects Free License" not in x["license"] for k,x in MIXKIT_FILES.items() if k != "music"):
        raise PipelineError("SFX asset is not marked with the Mixkit Sound Effects Free License.")

def download(url, path, min_bytes=1000):
    r = get(url)
    content_type = r.headers.get("Content-Type","").lower()
    if "text/html" in content_type or r.content.lstrip().lower().startswith((b"<!doctype html",b"<html")):
        raise PipelineError(f"Expected a media/binary asset but the server returned HTML: {url}")
    if len(r.content) < min_bytes:
        raise PipelineError(f"Asset too small ({len(r.content)} bytes): {url}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    return path

def obtain_assets(root):
    verify_licences()
    a = root / "assets"; a.mkdir(parents=True, exist_ok=True)
    out = {k:download(v, a / ({"map":"baarle.svg","geo":"countries.geojson"}.get(k, k+".jpg")), 10000)
           for k,v in ASSET_URLS.items()}
    # Music and most SFX are pulled from stable Mixkit CDN file URLs.
    # This bypasses the storefront page that returned HTTP 403 in Colab.
    for key, item in MIXKIT_FILES.items():
        out[key] = download(item["url"], a / (key+".mp3"), 1200)
    return out

def font(size, bold=True):
    names = (["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
             if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"])
    for p in names:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def centered(d, xy, txt, f, color, stroke=0):
    d.text(xy, txt, font=f, fill=color, anchor="mm", stroke_width=stroke, stroke_fill=C["ink"])

def panel(d, xy, fill, radius=38, outline=C["ink"], width=7):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def add_head(im, kicker, title, sub=""):
    d=ImageDraw.Draw(im)
    centered(d,(CW//2,175),kicker.upper(),font(42),C["ink"])
    lines=textwrap.wrap(title.upper(), 25)
    y=375
    for line in lines[:2]:
        centered(d,(CW//2,y),line,font(105),C["white"],7); y+=125
    if sub: centered(d,(CW//2,y+28),sub.upper(),font(48),C["ink"])

def footer(im, txt, y=3500):
    d=ImageDraw.Draw(im)
    panel(d,(105,y-86,CW-105,y+90),C["dark"],38,C["white"],5)
    centered(d,(CW//2,y+3),txt,font(48),C["white"])

def draw_map(geo, extent, highlight=None, mapbox=(100,850,CW-100,3000)):
    from shapely.geometry import shape, box
    data=json.loads(geo.read_text(encoding="utf-8"))
    minx,maxx,miny,maxy=extent
    im=Image.new("RGBA",(CW,CH),C["ocean"]); d=ImageDraw.Draw(im)
    x0,y0,x1,y1=mapbox; clip=box(minx,miny,maxx,maxy)
    def project(coords):
        x,y=coords[0],coords[1]
        return (int(x0+(x-minx)/(maxx-minx)*(x1-x0)),int(y1-(y-miny)/(maxy-miny)*(y1-y0)))
    for feat in data["features"]:
        geom=feat.get("geometry")
        if not geom: continue
        try: clipped=shape(geom).intersection(clip)
        except Exception: continue
        name=(feat.get("properties",{}).get("ADMIN") or feat.get("properties",{}).get("NAME") or "")
        col=(highlight or {}).get(name,C["land"])
        polys=[]
        if clipped.geom_type=="Polygon": polys=[clipped]
        elif clipped.geom_type=="MultiPolygon": polys=list(clipped.geoms)
        elif clipped.geom_type=="GeometryCollection":
            polys=[g for g in clipped.geoms if g.geom_type=="Polygon"]
        for poly in polys:
            pts=[project(c) for c in poly.exterior.coords]
            if len(pts)>2: d.polygon(pts,fill=col,outline=C["ink"],width=5)
    return im

def place_photo(base, path, rect):
    x0,y0,x1,y1=rect
    img=Image.open(path).convert("RGB")
    img.thumbnail((x1-x0,y1-y0),Image.Resampling.LANCZOS)
    card=Image.new("RGBA",(x1-x0+26,y1-y0+26),C["white"])
    matte=Image.new("RGB",(x1-x0,y1-y0),C["white"])
    matte.paste(img,((matte.width-img.width)//2,(matte.height-img.height)//2))
    card.paste(matte,(13,13))
    sh=Image.new("RGBA",(card.width+90,card.height+90),(0,0,0,0))
    mask=Image.new("L",sh.size,0)
    ImageDraw.Draw(mask).rounded_rectangle((42,42,42+card.width,42+card.height),radius=32,fill=120)
    sh.putalpha(mask.filter(ImageFilter.GaussianBlur(24)))
    base.alpha_composite(sh,(x0-42+8,y0-42+22)); base.alpha_composite(card,(x0,y0))

def crop_birefnet(candidates, outpath):
    from transformers import AutoModelForImageSegmentation
    from torchvision import transforms
    device="cuda" if torch.cuda.is_available() else "cpu"
    model=AutoModelForImageSegmentation.from_pretrained("ZhengPeng7/BiRefNet_HR",trust_remote_code=True)
    model.to(device).eval()
    if device=="cuda": model.half()
    norm=transforms.Normalize([.485,.456,.406],[.229,.224,.225])
    failures=[]
    for path in candidates:
        original=Image.open(path).convert("RGB")
        # Letterbox to square, rather than stretching the photo or deforming the subject.
        fitted=original.copy(); fitted.thumbnail((2048,2048),Image.Resampling.LANCZOS)
        px=(2048-fitted.width)//2; py=(2048-fitted.height)//2
        square=Image.new("RGB",(2048,2048),(127,127,127)); square.paste(fitted,(px,py))
        tensor=norm(transforms.ToTensor()(square)).unsqueeze(0).to(device)
        if device=="cuda": tensor=tensor.half()
        with torch.inference_mode(): pred=model(tensor)[-1].sigmoid().float().cpu()[0,0].numpy()
        m=Image.fromarray(np.uint8(np.clip(pred*255,0,255)))
        m=m.crop((px,py,px+fitted.width,py+fitted.height)).resize(original.size,Image.Resampling.LANCZOS)
        m=m.filter(ImageFilter.GaussianBlur(.65))
        a=np.asarray(m); fg=a>25
        ratio=float(fg.mean()); bbox=m.getbbox()
        edges=np.concatenate([fg[0,:],fg[-1,:],fg[:,0],fg[:,-1]])
        edge_ratio=float(edges.mean())
        # Reject near-empty/full masks and subject masks visibly truncated at the photo edge.
        ok=bbox is not None and .05<ratio<.94 and not (edge_ratio>.15)
        if not ok:
            failures.append(f"{path.name}: ratio={ratio:.3f}, edge={edge_ratio:.3f}")
            continue
        l,t,r,b=bbox; pad_x=int(original.width*.02); pad_y=int(original.height*.02)
        crop=(max(0,l-pad_x),max(0,t-pad_y),min(original.width,r+pad_x),min(original.height,b+pad_y))
        rgba=original.convert("RGBA"); rgba.putalpha(m); rgba=rgba.crop(crop)
        rgba.save(outpath,optimize=True)
        del model
        if torch.cuda.is_available(): torch.cuda.empty_cache()
        return outpath
    del model
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    raise PipelineError("All real-photo cutout candidates failed completeness QA: "+" | ".join(failures))

def build_scenes(a, root, cutout):
    import cairosvg
    map_png=root/"assets"/"enclave.png"
    cairosvg.svg2png(url=str(a["map"]),write_to=str(map_png),output_width=1700,output_height=1700)
    scenes=root/"scenes"; scenes.mkdir(exist_ok=True)
    result=[]
    im=draw_map(a["geo"],(-180,180,-58,85),mapbox=(90,920,CW-90,2790))
    add_head(im,"GEOGRAPHY / 01","A border through your bedroom?","BELGIUM × THE NETHERLANDS")
    footer(im,"NO FLIGHT. NO PASSPORT. JUST SLIPPERS.")
    p=scenes/"01_world.png"; im.convert("RGB").save(p); result.append(p)

    im=draw_map(a["geo"],(-1.5,13.5,48,56.2),{"Belgium":C["be"],"Netherlands":C["nl"]},(160,900,CW-160,3000))
    add_head(im,"ZOOM IN","Two countries. One town.","BAARLE-HERTOG / BAARLE-NASSAU")
    d=ImageDraw.Draw(im); panel(d,(155,3000,990,3190),C["be"]); centered(d,(570,3095),"BELGIUM",font(54),C["ink"])
    panel(d,(1170,3000,2005,3190),C["nl"]); centered(d,(1585,3095),"THE NETHERLANDS",font(48),C["white"])
    footer(im,"THE BORDER IS NOT A STRAIGHT LINE.")
    p=scenes/"02_europe.png"; im.convert("RGB").save(p); result.append(p)

    im=draw_map(a["geo"],(0.5,9,49,54.5),{"Belgium":C["be"],"Netherlands":C["nl"]},(180,910,CW-180,3020))
    add_head(im,"THE PAPERWORK BEGINS","1198 — the land deal","BRABANT / BREDA")
    d=ImageDraw.Draw(im)
    panel(d,(150,1740,1035,2480),"#F4E6C8"); centered(d,(592,1920),"BRABANT",font(95),C["ink"]); centered(d,(592,2160),"OLD PARCELS",font(52),C["ink"])
    panel(d,(1125,1740,2010,2480),"#E7D2A2"); centered(d,(1567,1920),"BREDA",font(95),C["ink"]); centered(d,(1567,2160),"LAND GRANTS",font(52),C["ink"])
    centered(d,(CW//2,2650),"1648  →  1843  →  1995",font(82),C["accent"],3)
    footer(im,"HISTORY REFUSED TO TIDY UP.")
    p=scenes/"03_history.png"; im.convert("RGB").save(p); result.append(p)

    im=Image.new("RGBA",(CW,CH),C["ocean"]); add_head(im,"THE CARTOGRAPHIC PUZZLE","30 enclaves","A PATCHWORK, NOT A NORMAL BORDER")
    diagram=Image.open(map_png).convert("RGBA"); diagram.thumbnail((CW-320,1900),Image.Resampling.LANCZOS)
    x=(CW-diagram.width)//2; y=850
    im.alpha_composite(diagram,(x,y))
    d=ImageDraw.Draw(im)
    panel(d,(140,2810,1010,3210),C["be"]); centered(d,(575,2940),"22",font(100),C["ink"]); centered(d,(575,3080),"BELGIAN",font(45),C["ink"])
    panel(d,(1150,2810,2020,3210),C["nl"]); centered(d,(1585,2940),"8",font(100),C["white"]); centered(d,(1585,3080),"DUTCH",font(45),C["white"])
    centered(d,(CW//2,3320),"7 DUTCH ENCLAVES SIT INSIDE THE TWO LARGEST BELGIAN ONES",font(37),C["ink"])
    p=scenes/"04_enclaves.png"; im.convert("RGB").save(p); result.append(p)

    im=Image.new("RGBA",(CW,CH),C["ocean"]); add_head(im,"LOOK CLOSER","The border goes through buildings","NOT JUST FIELDS AND ROADS")
    place_photo(im,a["shop"],(175,1000,CW-175,2940)); footer(im,"THE BORDER CAN CUT THROUGH A SHOP.")
    p=scenes/"05_shop.png"; im.convert("RGB").save(p); result.append(p)

    im=Image.new("RGBA",(CW,CH),C["ocean"]); add_head(im,"LOVEREN / BAARLE","One front door. Two countries.","THE HOUSE HAS TWO ADDRESSES")
    place_photo(im,a["house"],(110,1250,950,2780))
    subject=Image.open(cutout).convert("RGBA"); subject.thumbnail((980,1700),Image.Resampling.LANCZOS)
    im.alpha_composite(subject,(1040,1060))
    d=ImageDraw.Draw(im)
    panel(d,(140,2830,1000,3215),C["be"]); centered(d,(570,3020),"BELGIUM / No. 2",font(52),C["ink"])
    panel(d,(1160,2830,2020,3215),C["nl"]); centered(d,(1590,3020),"DUTCH / No. 19",font(52),C["white"])
    footer(im,"THE BORDER RUNS THROUGH THE FRONT DOOR.")
    p=scenes/"06_two_addresses.png"; im.convert("RGB").save(p); result.append(p)

    im=Image.new("RGBA",(CW,CH),C["ocean"]); add_head(im,"ON THE GROUND","Step over the border","THE MARKERS SHOW EXACTLY WHERE IT RUNS")
    place_photo(im,a["pavement"],(170,1050,CW-170,2980))
    centered(ImageDraw.Draw(im),(CW//2,3100),"ONE FOOT IN BELGIUM. ONE IN THE NETHERLANDS.",font(56),C["ink"])
    footer(im,"YOUR COMMUTE: FOUR STEPS.")
    p=scenes/"07_pavement.png"; im.convert("RGB").save(p); result.append(p)

    im=Image.new("RGBA",(CW,CH),C["ocean"]); add_head(im,"THE PLOT TWIST","It took until 1995","TO OFFICIALLY ESTABLISH THE LAST ENCLAVE BORDERS")
    d=ImageDraw.Draw(im); years=[(1198,"LAND DEAL"),(1648,"INTERNATIONAL STATUS"),(1843,"BORDER DESCRIBED"),(1995,"LAST LINES OFFICIAL")]
    y=1210
    for i,(yr,label) in enumerate(years):
        col=C["be"] if i%2==0 else C["nl"]; panel(d,(230,y,CW-230,y+190),col)
        centered(d,(500,y+95),str(yr),font(78),C["ink"] if i%2==0 else C["white"])
        centered(d,(1350,y+95),label,font(40),C["ink"] if i%2==0 else C["white"]); y+=230
    footer(im,"THE WORLD'S SLOWEST GROUP PROJECT.",y=2240)
    lines=["MAP: TOS / WIKIMEDIA COMMONS — PUBLIC DOMAIN",
           "HOUSE: JACK SOLEY / CC BY-SA 3.0  •  SHOP: KAYFABEBAALE / CC BY 4.0",
           "PAVEMENT: JACK SOLEY / CC BY-SA 4.0  •  NATURAL EARTH / PUBLIC DOMAIN",
           "MUSIC: EUGENIO MININNI / MIXKIT  •  RECORDED SFX: MIXKIT"]
    for i,line in enumerate(lines): centered(d,(CW//2,2760+i*65),line,font(30),C["ink"])
    p=scenes/"08_final_credits.png"; im.convert("RGB").save(p); result.append(p)
    return result

def trim_audio(x,sr):
    x=np.asarray(x,dtype=np.float32).reshape(-1); step=max(1,int(sr*.02)); vals=[]
    for i in range(0,len(x),step):
        c=x[i:i+step]; vals.append(float(np.sqrt(np.mean(c*c)+1e-12)))
    db=20*np.log10(np.maximum(vals,1e-8)); active=np.where(db>-48)[0]
    if not len(active): return x
    pad=int(sr*.065); return x[max(0,active[0]*step-pad):min(len(x),(active[-1]+1)*step+pad)]

def crossfade(chunks,sr,ms=95):
    out=chunks[0].astype(np.float32); n0=max(1,int(sr*ms/1000))
    for nxt in chunks[1:]:
        n=min(n0,len(out),len(nxt))
        if n<2: out=np.concatenate([out,nxt]); continue
        f=np.linspace(1,0,n,dtype=np.float32)
        out=np.concatenate([out[:-n],out[-n:]*f+nxt[:n]*(1-f),nxt[n:]])
    return out

def generate_voice(parts, work):
    from chatterbox.tts import ChatterboxTTS
    seed_all(42); device="cuda" if torch.cuda.is_available() else "cpu"
    model=ChatterboxTTS.from_pretrained(device=device); sr=int(model.sr)
    chunks=[]; seconds=[]
    for i,txt in enumerate(parts,1):
        wav=model.generate(txt,exaggeration=.35,cfg_weight=.45)
        arr=trim_audio(wav.squeeze().detach().float().cpu().numpy(),sr)
        if len(arr)<sr: raise PipelineError(f"Voice segment {i} is empty or too short.")
        chunks.append(arr); seconds.append(len(arr)/sr)
        sf.write(work/f"voice_{i:02d}.wav",arr,sr)
    full=crossfade(chunks,sr); peak=float(np.max(np.abs(full))+1e-9)
    full*=min(.72/peak,1.0); sf.write(work/"voiceover.wav",full,sr,subtype="PCM_16")
    del model
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    return work/"voiceover.wav",seconds,sr

def render_visuals(scenes, seconds, work):
    clips=[]; frames=[]
    for i,(scene,sec) in enumerate(zip(scenes,seconds),1):
        n=max(1,round(sec*FPS)); frames.append(n); out=work/f"visual_{i:02d}.mp4"
        z=f"1+0.035*(1-cos(PI*on/{max(1,n-1)}))/2"
        vf=f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},format=yuv420p"
        run_cmd(["ffmpeg","-y","-hide_banner","-loglevel","error","-loop","1","-framerate",str(FPS),"-i",str(scene),"-frames:v",str(n),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p",str(out)])
        clips.append(out)
    tr=.095; inputs=[]; pre=[]
    for p in clips: inputs += ["-i",str(p)]
    for i in range(len(clips)): pre.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]")
    graph=pre[:]; prev="[v0]"; elapsed=frames[0]/FPS
    for i in range(1,len(clips)):
        lab=f"[x{i}]"; graph.append(f"{prev}[v{i}]xfade=transition=fade:duration={tr}:offset={elapsed-tr:.6f}{lab}")
        prev=lab; elapsed+=frames[i]/FPS-tr
    out=work/"visuals.mp4"
    run_cmd(["ffmpeg","-y","-hide_banner","-loglevel","error",*inputs,"-filter_complex",";".join(graph),"-map",prev,"-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p","-r",str(FPS),str(out)])
    return out,elapsed

def mix_audio(voice, assets, seconds, sr, work):
    from pydub import AudioSegment
    from pydub.effects import normalize
    v=normalize(AudioSegment.from_file(voice).set_frame_rate(sr).set_channels(2),headroom=3.0)
    total=len(v); music=AudioSegment.from_file(assets["music"]).set_frame_rate(sr).set_channels(2)
    if not len(music): raise PipelineError("The real music file is empty.")
    # Seamless loop with a 0.9s crossfade between repetitions.
    loop=min(900,max(100,len(music)//4))
    while len(music)<total:
        # Pydub performs an actual overlap/crossfade; the former concatenation
        # expression could accidentally lengthen the bed instead of looping it.
        music=music.append(music,crossfade=loop)
    music=music[:total].apply_gain(-26).fade_in(1000).fade_out(1500)
    mix=v.overlay(music)
    starts=[]; cursor=0.0
    for sec in seconds: starts.append(cursor); cursor+=sec-.095
    placements=[("whoosh",starts[0]+1.0),("paper",starts[2]+.7),("whoosh",starts[3]+1.3),
                ("whoosh",starts[4]+1.6),("footstep",starts[6]+.6),("paper",starts[7]+2.0)]
    for key,at in placements:
        s=AudioSegment.from_file(assets[key]).set_frame_rate(sr).set_channels(2).apply_gain(-19)
        if int(at*1000)<total: mix=mix.overlay(s,position=int(at*1000))
    out=work/"final_mix.wav"; mix.fade_out(450).export(out,format="wav")
    return out

def run_pipeline(repo_root, output_path):
    root=Path(repo_root)
    script_file=root/"content"/"baarle_script.txt"
    cfg=json.loads((root/"config"/"baarle.json").read_text(encoding="utf-8"))
    parts=[p.strip() for p in script_file.read_text(encoding="utf-8").split("\n\n") if p.strip()]
    if len(parts)!=8: raise PipelineError(f"Expected eight narration paragraphs, found {len(parts)}.")
    work=Path("/content/baarle-build"); work.mkdir(parents=True,exist_ok=True)
    seed_all(42)
    assets=obtain_assets(work)
    cut=crop_birefnet([assets["house"],assets["house_alt"]],work/"house_cutout.png")
    voice,seconds,sr=generate_voice(parts,work)
    spoken=sum(seconds)-.095*(len(seconds)-1)
    if not 60<=spoken<=95:
        raise PipelineError(f"Natural Chatterbox output is {spoken:.1f}s. No speed-up applied; revise the script rather than time-stretching.")
    scenes=build_scenes(assets,work,cut)
    visuals,vis_len=render_visuals(scenes,seconds,work)
    audio=mix_audio(voice,assets,seconds,sr,work)
    final=Path(output_path); final.parent.mkdir(parents=True,exist_ok=True)
    run_cmd(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(visuals),"-i",str(audio),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest",str(final)])
    probe=subprocess.run(["ffprobe","-v","error","-show_entries","stream=codec_type,width,height,r_frame_rate:format=duration,size","-of","json",str(final)],capture_output=True,text=True,check=True)
    meta=json.loads(probe.stdout); v=next((x for x in meta["streams"] if x["codec_type"]=="video"),None); a=next((x for x in meta["streams"] if x["codec_type"]=="audio"),None)
    dur=float(meta["format"]["duration"]); size=int(meta["format"]["size"])
    if not v or not a or (v["width"],v["height"],v["r_frame_rate"])!=(1080,1920,"60/1") or dur<60 or size<500000:
        raise PipelineError(f"Final QA failed: video={v}, audio={bool(a)}, duration={dur:.2f}, bytes={size}")
    qa={"file":str(final),"duration_seconds":dur,"bytes":size,"resolution":"1080x1920","fps":60,"voice":"Chatterbox default English speaker","seed":42,"voice_chunk_seconds":seconds,"cutout":"BiRefNet_HR 2048, soft alpha, candidate completeness QA","render_location":"Google Colab","github_actions_render":False}
    (work/"qa.json").write_text(json.dumps(qa,indent=2),encoding="utf-8")
    return final
