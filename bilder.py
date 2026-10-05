#!/usr/bin/env python3
"""Rechnet die frei lizenzierten Commons-Fotos (bilder-commons/) in Webgrößen um
und schreibt src/assets/img/fotos.json mit Alternativtext und Bildnachweis."""
import json, pathlib
from PIL import Image, ImageOps
HIER = pathlib.Path(__file__).resolve().parent
Q, Z = HIER / "bilder-commons", HIER / "src/assets/img"
M = {b["file"]: b for b in json.loads((Q / "manifest.json").read_text("utf8"))}
# schlüssel: (datei, alt, symbolbild-hinweis, fokus)
AUSWAHL = {
  "held-kh": ("kh-luftbild-haselbergturm.jpg", "Luftbild der Königsbrücker Heide: Der hölzerne Haselbergturm steht zwischen Birken, Kiefern und offenen Flächen mit gelb blühendem Ginster.", None, "50% 45%"),
  "kh-blick": ("kh-blick-haselbergturm-keulenberg.jpg", "Blick vom Haselbergturm über geschlossenen Wald bis zum Keulenberg am Horizont.", None, "50% 60%"),
  "kh-turm": ("kh-haselbergturm.jpg", "Der hölzerne Haselbergturm vor blauem Himmel, davor junge Birken.", None, "50% 35%"),
  "kh-see": ("kh-see-der-freundschaft-1.jpg", "See der Freundschaft mit Uferweg, Holzbank und kleiner Hütte am Waldrand.", None, "50% 50%"),
  "kh-tafeln": ("kh-see-der-freundschaft-2.jpg", "Uferweg am See der Freundschaft mit zwei überdachten Informationstafeln.", None, "50% 55%"),
  "kh-hirsch": ("kh-rothirsch.jpg", "Ein weiblicher Rothirsch steht im hohen Gras.", None, "40% 40%"),
  "kh-flechten": ("kh-flechten-silbergrasflur.jpg", "Rötliche Becherflechten auf einem alten Kiefernstumpf, dahinter blühendes Heidekraut und Birken.", None, "50% 60%"),
  "kh-schild": ("kh-schild-nsg-kampfmittel.jpg", "Schild am Naturschutzgebiet mit Hinweis auf Kampfmittelbelastung und Betretungsverbot, dahinter junger Wald.", None, "50% 45%"),
  "biber": ("koenigsbrueck-biberweg-schnitzerei.jpg", "Holzschnitzerei mit mehreren Bibern in einem überdachten Unterstand.", None, "50% 50%"),
  "gh-heide": ("allg-calluna-heide-birke.jpg", "Symbolbild: blühende Besenheide mit Birke und jungen Kiefern unter blauem Himmel.", "Symbolbild aus dem NSG Kleine Schorfheide (Brandenburg)", "50% 55%"),
  "gh-sand": ("allg-sandheide-kiefern.jpg", "Symbolbild: offener Sand mit blühendem Heidekraut vor Kiefern und Birken.", "Symbolbild aus dem NSG Kleine Schorfheide (Brandenburg)", "50% 50%"),
  "wiedehopf": ("allg-wiedehopf.jpg", "Ein Wiedehopf füttert ein Jungtier an einer Baumhöhle.", "Symbolbild aus dem Ruppiner Wald (Brandenburg)", "50% 40%"),
}
out = {}
for key, (datei, alt, symbol, fokus) in AUSWAHL.items():
    b = M[datei]
    im = ImageOps.exif_transpose(Image.open(Q / datei)).convert("RGB")
    w, h = im.size
    stufen = [b2 for b2 in ((960, 1600, 2400) if w >= 2400 else (640, 1000, 1400)) if b2 <= w] or [w]
    for s in stufen:
        im.resize((s, round(h * s / w)), Image.LANCZOS).save(Z / f"{key}-{s}.jpg", "JPEG", quality=76, optimize=True, progressive=True)
    lizenz = b["license_short"].replace("CC0", "CC0 1.0")
    out[key] = {"datei": key, "breiten": stufen, "verhaeltnis": round(h / w, 4), "alt": alt, "fokus": fokus,
                "urheber": b["author"], "lizenz": lizenz, "lizenz_url": b["license_url"],
                "quelle": b["commons_page_url"], "titel": b["commons_title"], "symbolbild": symbol,
                "aenderung": "verkleinert und zugeschnitten"}
(Z / "fotos.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf8")
print(len(out), "Fotos;", sum(f.stat().st_size for f in Z.glob("*.jpg")) // 1024, "KB")
