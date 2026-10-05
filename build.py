#!/usr/bin/env python3
"""Baut den Website-Demonstrator im Design der Nationalen Naturlandschaften.

Zweck: Nachweis zum Wertungskriterium "Website im NNL-Design" der Ausschreibung
2026-VG-NG17_0001 (Relaunch Website, Staatsbetrieb Sachsenforst). Die Seiten sind
statisch und ohne Abhängigkeiten, damit sie auf GitHub Pages, auf jedem Webserver
und lokal laufen.

    python3 build.py            # schreibt nach docs/
    python3 -m http.server -d docs 8000

Aufbau:
    src/seiten/*.html      Seiteninhalte (nur der Hauptteil), oben ein META-Kommentar
    src/assets/            CSS, JS, Schrift, Leaflet, Bilder, Daten
    docs/                  Ergebnis, wird von GitHub Pages ausgeliefert

Regeln, die der Bau prüft: keine Gedankenstriche im sichtbaren Text, jede Seite
trägt den Demonstrator-Hinweis und noindex, jedes Bild hat einen Alternativtext,
jeder interne Link zeigt auf eine vorhandene Datei.
"""
import datetime
import html
import json
import pathlib
import re
import shutil
import sys
import unicodedata

HIER = pathlib.Path(__file__).resolve().parent
SRC = HIER / "src"
OUT = HIER / "docs"

BASIS_URL = "https://birkenpapier.github.io/nnl-demonstrator/"
VERGABE = "2026-VG-NG17_0001"
DEMO_HINWEIS = ("Demonstrator der dioptify UG (haftungsbeschränkt) zur Ausschreibung "
                f"{VERGABE}. Keine offizielle Website des Staatsbetriebs Sachsenforst.")
DEMO_HINWEIS_EN = ("Demonstrator by dioptify UG (haftungsbeschränkt) for tender "
                   f"{VERGABE}. Not an official website of Staatsbetrieb Sachsenforst.")
WORTMARKE = ("Königsbrücker Heide", "Gohrischheide")
STAND = datetime.date.today().strftime("%d.%m.%Y")

# ---------------------------------------------------------------- Sitemap (Anlage 5b)
# (schlüssel, titel, kurztext für Übersichten und Platzhalter, ausgearbeitet?)
NAV = [
    {"id": "entdecken", "bild": "kh-hirsch", "unterzeile": "Zwei Schutzgebiete, ihre Geschichte und ihre Besonderheiten", "titel": "Entdecken & Informieren", "zeilen": ("Entdecken", "& Informieren"),
     "icon": "fernglas", "farbe": "dunkelgruengelb", "unter": [
        ("wildnisgebiet-koenigsbruecker-heide", "Wildnisgebiet Königsbrücker Heide",
         "Steckbrief, Geschichte, Besonderheiten und Schutzstatus des größten Schutzgebiets der Verwaltung."),
        ("gohrischheide-zeithain", "Naturschutzgebiet Gohrischheide und Elbniederterrasse Zeithain",
         "Sandheiden und Binnendünen zwischen Riesa, Gröditz und Mühlberg/Elbe."),
        ("haeufige-fragen", "Häufige Fragen (FAQ)",
         "Antworten zu Wegen, Munitionsbelastung und Wildnis."),
        ("ueber-uns", "Über uns",
         "Aufgaben und Ziele der NSG-Verwaltung, Ansprechpersonen, Ausschreibungen und Formulare zum Herunterladen, etwa für Gestattungen."),
    ]},
    {"id": "besuchen", "bild": "kh-see", "unterzeile": "Besucherpfade, Ausflugsziele und Veranstaltungen", "titel": "Besuchen & Erleben", "zeilen": ("Besuchen", "& Erleben"),
     "icon": "karte", "farbe": "mittelblau", "unter": [
        ("besucherinformation", "Besucherinformation",
         "Infothek und Angebote für Besucherinnen und Besucher, als ausklappbare Artikel."),
        ("besucherpfade", "Besucherpfade",
         "Interaktive Karte mit allen Besucherpfaden, Radrundwegen und Aussichtspunkten."),
        ("ausflugsziele", "Ausflugsziele",
         "Aussichtstürme, Rastplätze und Besucherzentrum auf einen Blick."),
        ("veranstaltungen", "Veranstaltungen",
         "Führungen, Vorträge und Mitmachaktionen mit Kalender, Filter und Export."),
    ]},
    {"id": "lernen", "bild": "wiedehopf", "unterzeile": "Forschung, Umweltbildung und Junior Ranger", "titel": "Lernen & Verstehen", "zeilen": ("Lernen", "& Verstehen"),
     "icon": "buch", "farbe": "punktblau", "unter": [
        ("forschung-monitoring", "Forschung & Monitoring",
         "Ziele von Forschung und Monitoring, Kennzahlen zur Entwicklung, drei Schlaglichter und Publikationen."),
        ("umweltbildung", "Umweltbildung für Kitas & Schulen",
         "Umwelt- und Wildnisbildung, BiberBus für Kids, buchbare Angebote und Anmeldeformular."),
        ("junior-ranger", "Junior Ranger",
         "Das Programm für Kinder und Jugendliche mit Schlaglichtern zu aktuellen Themen."),
        ("naturschutz-fuer-kids", "Naturschutz für Kids",
         "Kinderseite mit Wissen und einem interaktiven Spiel, als Erweiterung vorgesehen."),
    ]},
    {"id": "mitmachen", "bild": "biber", "unterzeile": "Praktikum, Freiwilligendienst, Ehrenamt und Citizen Science", "titel": "Mitmachen & Unterstützen", "zeilen": ("Mitmachen", "& Unterstützen"),
     "icon": "daumen", "farbe": "aubergine", "unter": [
        ("praktika", "Praktika", "Praktika in beiden Schutzgebieten und die Ansprechperson dafür."),
        ("foej", "Freiwilliges Ökologisches Jahr (FÖJ)",
         "Tätigkeiten im FÖJ bei der NSG-Verwaltung, Faltblatt und Ansprechperson."),
        ("bfd", "Bundesfreiwilligendienst (BFD)", "Tätigkeiten im BFD und Ansprechperson."),
        ("ehrenamt", "Ehrenamt",
         "Ehrenamtlich als Geländeführung, in der Wacht oder in der Infothek."),
        ("citizen-science", "Citizen Science",
         "Mit einer App auf den Besucherpfaden selbst mitforschen."),
        ("abschlussarbeiten", "Abschlussarbeiten",
         "Themen für Abschlussarbeiten und die Ansprechperson."),
    ]},
    {"id": "teilnehmen-buchen", "titel": "Teilnehmen & Buchen", "zeilen": ("Teilnehmen", "& Buchen"),
     "icon": "ticket", "farbe": "violett", "unter": []},
]
NAV_BY_ID = {n["id"]: n for n in NAV}

FUSS_LINKS = [
    ("impressum/", "Impressum"),
    ("datenschutz/", "Datenschutz"),
    ("barrierefreiheit/", "Erklärung zur Barrierefreiheit"),
    ("agb-teilnahmebedingungen/", "AGB und Teilnahmebedingungen"),
    ("transparenzhinweis/", "Transparenzhinweis"),
    ("presse/", "Presse"),
    ("downloads/", "Downloads und Publikationen"),
    ("kontakt/", "Kontakt"),
]

PLATZHALTER_FUSS = {
    "agb-teilnahmebedingungen": ("AGB und Teilnahmebedingungen",
                                 "Allgemeine Geschäftsbedingungen und Teilnahmebedingungen für Veranstaltungen und Buchungen."),
    "transparenzhinweis": ("Transparenzhinweis",
                           "Pflichtangaben zur Transparenz des Auftraggebers, etwa zu Förderungen."),
    "presse": ("Presse", "Ansprechperson für die Presse und Pressemappe zum Herunterladen."),
    "downloads": ("Downloads und Publikationen",
                  "Faltblätter wie „Fahrradfahren im Wald“ und „Sicher unterwegs im Wald“, Jahresprogramm und Publikationen."),
}

# Element- und Akzentfarben aus der 36-Farben-Palette des NNL-CD (Farbwerte, Stand CD-Manual)
FARBEN = {
    "dunkelblau": "#002c50", "mittelblau": "#205b7d", "punktblau": "#23538a",
    "himmelblau": "#cce9f3", "hellblau": "#abc6d1", "helltuerkis": "#96cfc1",
    "khaki": "#576749", "dunkelgruengelb": "#446428", "hellgruengelb": "#b4c897",
    "gelborange": "#f9b342", "gelb": "#ffde14", "mittelgelb": "#ffe37e",
    "hellbeige": "#dcc6a3", "aubergine": "#962e45", "violett": "#83406f",
    "helleslila": "#bdabc6", "rosa": "#f18fa2",
}
# Elementfarben mit weißer Schrift (Farben Typografie) und Kontrast >= 4,5:1 auf dem Bildschirm
WEISSE_SCHRIFT = {"dunkelblau", "mittelblau", "punktblau", "khaki", "dunkelgruengelb", "aubergine", "violett"}

# ---------------------------------------------------------------- Formen
# Eigene Nachbildungen der Dialogelemente (keine Originaldateien des NNL-CD).
# Im Projekt werden die Originalformen aus dem CD-Manual eingesetzt.
FORM_KOPF = ("0 0 1440 130",
             "M0 0H1440V64C1398 92 1330 112 1250 112C1170 112 1120 92 1104 66C1092 46 1098 26 1078 16"
             "C1054 4 1012 10 1002 36C996 54 1008 70 1022 80C1036 92 1016 104 978 108C880 116 780 96 660 86"
             "C520 74 400 86 280 102C180 114 80 120 0 112Z")
FORM_TITEL = ("0 0 1440 150",
              "M0 150V70C140 34 300 20 460 44C600 66 680 112 820 108C960 104 1040 40 1180 30"
              "C1290 22 1380 44 1440 66V150Z")
FORM_OBEN = ("0 0 1440 120",
             "M0 120V54C180 10 360 8 560 40C720 66 860 96 1040 72C1200 50 1320 20 1440 34V120Z")
FORM_UNTEN = ("0 0 1440 120",
              "M0 0H1440V62C1300 96 1160 108 1000 86C840 64 720 30 540 40C360 50 200 92 0 70Z")
FORM_FUSS = ("0 0 1440 160",
             "M0 160V96C120 70 220 40 340 44C420 47 452 80 432 104C420 120 440 132 470 126"
             "C560 108 640 60 760 56C900 52 1000 104 1160 100C1280 97 1370 72 1440 58V160Z")
FORM_LOGO = ("0 0 460 170",
             "M0 0H460C412 8 388 50 356 88C310 142 226 164 124 162C72 161 32 154 0 146Z")


def form(f, klasse):
    vb, d = f
    return (f'<svg class="{klasse}" viewBox="{vb}" preserveAspectRatio="none" aria-hidden="true" '
            f'focusable="false"><path d="{d}"/></svg>')


# ---------------------------------------------------------------- Piktogramme (linear, einfarbig)
ICONS = {
    "fernglas": '<path d="M6.5 6.5 8 4h2l1 3M17.5 6.5 16 4h-2l-1 3"/><circle cx="6.5" cy="15.5" r="4"/><circle cx="17.5" cy="15.5" r="4"/><path d="M10.5 15.5h3M4 12.5l2.5-6h3.5l.5 6.5M20 12.5l-2.5-6H14l-.5 6.5"/>',
    "karte": '<path d="M3 6.5 8.5 4l7 2.5L21 4v13.5L15.5 20l-7-2.5L3 20z"/><path d="M8.5 4v13.5M15.5 6.5V20"/>',
    "buch": '<path d="M12 6.5C10 5 7.5 4.5 3.5 4.5v13c4 0 6.5.5 8.5 2 2-1.5 4.5-2 8.5-2v-13c-4 0-6.5.5-8.5 2z"/><path d="M12 6.5v13"/>',
    "daumen": '<path d="M7 10.5v9H4v-9zM7 10.5l3.5-6.5c1.6 0 2.5 1.1 2.2 2.6l-.7 3.4h5.6a2 2 0 0 1 2 2.4l-1.3 5.9a2 2 0 0 1-2 1.7H7"/>',
    "ticket": '<path d="M3.5 7.5h17v3a2 2 0 0 0 0 4v3h-17v-3a2 2 0 0 0 0-4z"/><path d="M14.5 7.5v10" stroke-dasharray="1.6 1.8"/>',
    "suche": '<circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5 5"/>',
    "pfeil": '<path d="M4.5 12h14M13 6.5l5.5 5.5-5.5 5.5"/>',
    "pfeil-oben": '<path d="M12 19.5v-14M6.5 11 12 5.5l5.5 5.5"/>',
    "extern": '<path d="M7 17 17 7M9 7h8v8"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "schliessen": '<path d="m6 6 12 12M18 6 6 18"/>',
    "menue": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "kontrast": '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5v17a8.5 8.5 0 0 0 0-17z" fill="currentColor"/>',
    "vorlesen": '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11"/>',
    "leicht": '<rect x="4.5" y="3.5" width="15" height="17" rx="2"/><path d="M8 8h8M8 11.5h8M8 15l2 2 4-4"/>',
    "gebaerden": '<path d="M8 13V6.5a1.5 1.5 0 0 1 3 0V12M11 11V5a1.5 1.5 0 0 1 3 0v6M14 11V6.5a1.5 1.5 0 0 1 3 0V14c0 3.5-2.5 6.5-6 6.5-2.4 0-3.7-1.2-5-3.2L4.5 15a1.6 1.6 0 0 1 2.6-1.8L8 14.4"/>',
    "welt": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.6 2.6 3.6 5.4 3.6 8.5s-1 5.9-3.6 8.5c-2.6-2.6-3.6-5.4-3.6-8.5s1-5.9 3.6-8.5z"/>',
    "warnung": '<path d="M12 4 21 19.5H3z"/><path d="M12 10v4.5M12 17h.01"/>',
    "feuer": '<path d="M12 21c-3.6 0-6-2.4-6-5.6 0-3.4 2.6-5 3.4-8.4 1.9 1.3 2.6 3.1 2.4 4.9 1-.6 1.7-1.7 1.8-3.2 2.4 1.9 4.4 4.3 4.4 6.9 0 3.1-2.4 5.4-6 5.4z"/>',
    "info": '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8h.01"/>',
    "kalender": '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M8 3v4M16 3v4"/>',
    "ort": '<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.4"/>',
    "turm": '<path d="M8.5 21 10 9h4l1.5 12M7 9h10M8 5.5h8L17 9H7zM9.3 15h5.4M12 3v2.5"/>',
    "huette": '<path d="M3 11.5 12 4l9 7.5M5.5 9.5V20h13V9.5M10 20v-5h4v5"/>',
    "rad": '<circle cx="6" cy="16" r="3.5"/><circle cx="18" cy="16" r="3.5"/><path d="M6 16l3.5-7h6L18 16M9.5 9 12 16h-6M14 6h2.5"/>',
    "wandern": '<path d="M13.5 5.5a1.6 1.6 0 1 0 0-3.2 1.6 1.6 0 0 0 0 3.2zM11 21l2-6-2.5-2.5L12 8l3 3 2.5 1M10.5 12.5 8 21M12 8 8.5 9.5 7.5 13"/>',
    "download": '<path d="M12 4v11M7 10.5l5 5 5-5M5 19.5h14"/>',
    "mail": '<rect x="3.5" y="5.5" width="17" height="13" rx="2"/><path d="m4 7 8 6 8-6"/>',
    "telefon": '<path d="M6.5 3.5h3l1.5 4-2 1.5a10 10 0 0 0 6 6l1.5-2 4 1.5v3a2 2 0 0 1-2 2A16.5 16.5 0 0 1 4.5 5.5a2 2 0 0 1 2-2z"/>',
    "uhr": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3 2"/>',
    "facebook": '<circle cx="12" cy="12" r="8.5"/><path d="M13 20.5V12h2.5M13 12V9.5c0-1.2.8-2 2-2h1M10.5 12H13"/>',
    "instagram": '<rect x="4" y="4" width="16" height="16" rx="4.5"/><circle cx="12" cy="12" r="3.6"/><path d="M16.8 7.2h.01"/>',
    "youtube": '<rect x="3" y="6" width="18" height="12" rx="3.5"/><path d="m10.5 9.5 4 2.5-4 2.5z"/>',
    "haken": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "stoerung": '<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><path d="M12 7v4M12 13.5h.01"/>',
    "ebenen": '<path d="m12 4 8.5 4.5L12 13 3.5 8.5z"/><path d="m3.5 12.5 8.5 4.5 8.5-4.5M3.5 16.5 12 21l8.5-4.5"/>',
    "fokus": '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>',
}


def icon(name, klasse="icon"):
    return (f'<svg class="{klasse}" aria-hidden="true" focusable="false"><use href="#i-{name}"/></svg>')


def sprite():
    teile = "".join(
        f'<symbol id="i-{n}" viewBox="0 0 24 24">{p}</symbol>' for n, p in ICONS.items())
    return (f'<svg class="sprite" aria-hidden="true" focusable="false" '
            f'xmlns="http://www.w3.org/2000/svg">{teile}</svg>')


# ---------------------------------------------------------------- Bilder
def bilder_laden():
    p = SRC / "assets/img/fotos.json"
    return json.loads(p.read_text("utf8")) if p.exists() else {}


BILDER = bilder_laden()


def nachweis_text(b):
    sym = f'{html.escape(b["symbolbild"])}. ' if b.get("symbolbild") else ""
    return (f'{sym}Foto: {html.escape(b["urheber"])}, <a href="{b["lizenz_url"]}" rel="license noopener">'
            f'{html.escape(b["lizenz"])}</a>, via <a href="{b["quelle"]}" rel="noopener">Wikimedia Commons</a>')


def ueberlagerter_nachweis(key):
    b = BILDER.get(key)
    return f'<p class="bildnachweis bildnachweis--ueber">{nachweis_text(b)}</p>' if b else ""


def bild(key, r, klasse="", groessen="100vw", laden="lazy", mit_nachweis=True):
    """<figure> mit srcset aus fotos.json. Ohne Foto: eigene Illustration."""
    b = BILDER.get(key)
    if not b:
        return ""
    srcset = ", ".join(f'{r}assets/img/{b["datei"]}-{w}.jpg {w}w' for w in b["breiten"])
    groesste = b["breiten"][-1]
    hoehe = round(groesste * b["verhaeltnis"])
    prio = ' fetchpriority="high"' if laden == "eager" else ""
    img = (f'<img src="{r}assets/img/{b["datei"]}-{b["breiten"][min(1, len(b["breiten"]) - 1)]}.jpg" '
           f'srcset="{srcset}" sizes="{groessen}" width="{groesste}" height="{hoehe}" '
           f'alt="{html.escape(b["alt"])}" loading="{laden}" decoding="async"{prio}'
           f' style="object-position:{b.get("fokus", "50% 50%")}">')
    nachweis = ""
    if mit_nachweis:
        nachweis = f'<figcaption class="bildnachweis">{nachweis_text(b)}</figcaption>'
    return f'<figure class="foto {klasse}">{img}{nachweis}</figure>'


# ---------------------------------------------------------------- Seitenlayout
def rel(pfad):
    """Relativer Weg zur Wurzel für eine Seite mit Pfad wie 'a/b/'."""
    tiefe = pfad.count("/")
    return "../" * tiefe


def kopf_html(seite, r):
    aktiv = seite.get("bereich")
    nav_items = []
    for n in NAV:
        ist = ' aria-current="true"' if aktiv == n["id"] else ""
        z1, z2 = n["zeilen"]
        label = f'<span class="hauptnav__text"><span>{html.escape(z1)}</span> <span>{html.escape(z2)}</span></span>'
        if n["unter"]:
            unter = "".join(
                f'<li><a href="{r}{n["id"]}/{u[0]}/"'
                f'{" aria-current=\"page\"" if seite["pfad"] == n["id"] + "/" + u[0] + "/" else ""}>'
                f'<span class="fahne" aria-hidden="true"></span>{html.escape(u[1])}</a></li>'
                for u in n["unter"])
            nav_items.append(
                f'<li class="hauptnav__punkt{" ist-aktiv" if ist else ""}">'
                f'<button class="hauptnav__knopf" type="button" aria-expanded="false" '
                f'aria-controls="panel-{n["id"]}">{icon(n["icon"], "icon icon--nav")}{label}</button>'
                f'<div class="hauptnav__panel" id="panel-{n["id"]}" hidden>'
                f'<ul class="hauptnav__liste">'
                f'<li class="hauptnav__uebersicht"><a href="{r}{n["id"]}/">Übersicht {html.escape(n["titel"])}'
                f'{icon("pfeil")}</a></li>{unter}</ul></div></li>')
        else:
            nav_items.append(
                f'<li class="hauptnav__punkt{" ist-aktiv" if ist else ""}">'
                f'<a class="hauptnav__knopf" href="{r}{n["id"]}/"{ist}>'
                f'{icon(n["icon"], "icon icon--nav")}{label}</a></li>')
    en = seite.get("lang") == "en"
    sprache = (f'<a href="{r}" lang="de" hreflang="de" class="sprache__link"'
               f'{" aria-current=\"true\"" if not en else ""}>'
               f'<span aria-hidden="true">DE</span><span class="visually-hidden">Deutsch</span></a>'
               f'<a href="{r}en/" lang="en" hreflang="en" class="sprache__link"'
               f'{" aria-current=\"true\"" if en else ""}>'
               f'<span aria-hidden="true">EN</span><span class="visually-hidden">English</span></a>')
    t = TEXTE["en" if en else "de"]
    return f'''
<header class="kopf" id="kopf">
  <div class="kopf__flaeche">
    <div class="kopf__logos">
      {form(FORM_LOGO, "kopf__logoform")}
      <div class="kopf__logoplatz" role="img" aria-label="{t["logoplatz_label"]}">
        <span class="logoplatzhalter">Logo Staatsbetrieb Sachsenforst</span>
        <span class="logoplatzhalter">Logo Freistaat Sachsen</span>
      </div>
    </div>
    <a class="wortmarke" href="{r}{"en/" if en else ""}">
      <span class="wortmarke__name">{WORTMARKE[0]}<span class="wortmarke__punkt" aria-hidden="true"> · </span><span class="visually-hidden"> und </span><br>{WORTMARKE[1]}</span>
      <span class="wortmarke__zusatz">Demonstrator</span>
    </a>
    <button class="menuekopf" type="button" aria-expanded="false" aria-controls="kopf-navbereich">
      {icon("menue")}<span class="menuekopf__text">{t["menue"]}</span>
    </button>
    <div class="kopf__navbereich" id="kopf-navbereich">
      <div class="service">
        <ul class="service__links">
          <li><a href="{r}aktuelles/">{t["aktuelles"]}</a></li>
          <li><a href="{r}kontakt/">{t["kontakt"]}</a></li>
          <li><a href="{r}besuchen/besucherpfade/#karte-bereich">{icon("karte")}{t["karte"]}</a></li>
        </ul>
        <form class="suchfeld" role="search" aria-label="{t["suche_label"]}" action="{r}suche/" method="get">
          <label class="visually-hidden" for="suchfeld-eingabe">{t["suche_label"]}</label>
          <input id="suchfeld-eingabe" name="q" type="search" placeholder="{t["suche_platzhalter"]}" autocomplete="off" enterkeyhint="search">
          <button type="submit" class="suchfeld__knopf">{icon("suche")}<span class="visually-hidden">{t["suche_starten"]}</span></button>
        </form>
        <div class="sprache" role="group" aria-label="{t["sprache"]}">{sprache}</div>
        <ul class="service__zugang">
          <li><a href="{r}leichte-sprache/" class="zugang__link">{icon("leicht")}<span>Leichte Sprache</span></a></li>
          <li><a href="{r}gebaerdensprache/" class="zugang__link">{icon("gebaerden")}<span>Gebärdensprache</span></a></li>
        </ul>
        <div class="werkzeuge" role="group" aria-label="{t["werkzeuge"]}">
          <button type="button" class="werkzeug" data-aktion="kleiner" title="{t["kleiner"]}"><span aria-hidden="true">A&#8722;</span><span class="visually-hidden">{t["kleiner"]}</span></button>
          <button type="button" class="werkzeug" data-aktion="groesser" title="{t["groesser"]}"><span aria-hidden="true">A+</span><span class="visually-hidden">{t["groesser"]}</span></button>
          <button type="button" class="werkzeug" data-aktion="kontrast" aria-pressed="false" title="{t["kontrast"]}">{icon("kontrast")}<span class="visually-hidden">{t["kontrast"]}</span></button>
          <button type="button" class="werkzeug" data-aktion="vorlesen" aria-pressed="false" title="{t["vorlesen"]}">{icon("vorlesen")}<span class="visually-hidden">{t["vorlesen"]}</span></button>
        </div>
        <ul class="sozial" aria-label="Social Media">
          <li><a href="{r}kontakt/#social-media" title="Facebook">{icon("facebook")}<span class="visually-hidden">Facebook ({t["folgt"]})</span></a></li>
          <li><a href="{r}kontakt/#social-media" title="Instagram">{icon("instagram")}<span class="visually-hidden">Instagram ({t["folgt"]})</span></a></li>
          <li><a href="{r}kontakt/#social-media" title="YouTube">{icon("youtube")}<span class="visually-hidden">YouTube ({t["folgt"]})</span></a></li>
        </ul>
      </div>
      <nav class="hauptnav" id="hauptnav" aria-label="{t["hauptnav"]}">
        <ul class="hauptnav__ebene">{"".join(nav_items)}</ul>
      </nav>
    </div>
  </div>
  {form(FORM_KOPF, "kopf__kante")}
</header>'''


def warn_html(r, en=False):
    t = TEXTE["en" if en else "de"]
    return f'''
<div class="warnleiste" role="region" aria-label="{t["warn_label"]}">
  <div class="warnleiste__innen">
    <p class="warnleiste__meldung" data-anzeigen-ab="2026-09-01" data-anzeigen-bis="2027-03-31">
      {icon("feuer")}<span><strong>{t["waldbrand"]}</strong> {t["waldbrand_wert"]}</span>
    </p>
    <p class="warnleiste__meldung">
      {icon("warnung")}<span><strong>{t["munition"]}</strong> {t["munition_text"]}</span>
    </p>
    <a class="warnleiste__link" href="{r}aktuelles/#warnmeldungen">{t["alle_meldungen"]}{icon("pfeil")}</a>
  </div>
</div>'''


def demo_html(r, en=False):
    text = DEMO_HINWEIS_EN if en else DEMO_HINWEIS
    mehr = "About this demonstrator" if en else "Über diesen Demonstrator"
    zusatz = f'<span class="visually-hidden">{DEMO_HINWEIS}</span>' if en else ""
    return (f'<section class="demoleiste" aria-label="{"About this demonstrator" if en else "Hinweis zum Demonstrator"}">'
            f'<p>{icon("info")}<span>{text}</span>{zusatz} '
            f'<a href="{r}demonstrator/">{mehr}</a></p></section>')


def fuss_html(r, en=False):
    t = TEXTE["en" if en else "de"]
    links = "".join(f'<li><a href="{r}{p}">{html.escape(l)}</a></li>' for p, l in FUSS_LINKS)
    return f'''
<footer class="fuss">
  {form(FORM_FUSS, "fuss__kante")}
  <div class="fuss__flaeche">
    <div class="wrap fuss__raster">
      <div class="fuss__gebiet">
        <p class="fuss__titel">{t["fuss_titel"]}</p>
        <p>{t["fuss_text"]}</p>
      </div>
      <div class="fuss__kontakt">
        <p class="fuss__zwischentitel">{t["fuss_kontakt"]}</p>
        <p>{t["fuss_kontakt_text"]}</p>
        <p><a class="knopf knopf--hell" href="{r}kontakt/">{t["kontakt"]}{icon("pfeil")}</a></p>
      </div>
      <div class="fuss__nnl">
        <p class="fuss__zwischentitel">{t["nnl_titel"]}</p>
        <p>{t["nnl_text"]}</p>
        <p><a class="knopf knopf--hell" href="https://nationale-naturlandschaften.de/" rel="noopener">{icon("extern")}nationale-naturlandschaften.de</a></p>
      </div>
    </div>
    <div class="wrap fuss__unten">
      <nav aria-label="{t["fussnav"]}"><ul class="fuss__links">{links}</ul></nav>
      <a class="fuss__redaktion" href="{r}demonstrator/#redaktion">{t["redaktion"]}</a>
    </div>
    <div class="wrap fuss__demo">
      <p>{icon("info")}<span>{DEMO_HINWEIS_EN if en else DEMO_HINWEIS}</span></p>
      <p class="fuss__stand">{t["stand"]} {STAND}</p>
    </div>
  </div>
  <a class="nachoben" href="#seitenanfang">{icon("pfeil-oben")}<span class="visually-hidden">{t["nachoben"]}</span></a>
</footer>'''


TEXTE = {
    "de": {
        "logoplatz_label": "Platzhalter für die Logos des Staatsbetriebs Sachsenforst und des Freistaates Sachsen",
        "logoplatz": "Platzhalter: Logos liefert der Auftraggeber",
        "menue": "Menü", "aktuelles": "Aktuelles", "kontakt": "Kontakt", "karte": "Interaktive Karte",
        "suche_label": "Website durchsuchen", "suche_platzhalter": "Ich suche …", "suche_starten": "Suche starten",
        "sprache": "Sprache wählen", "werkzeuge": "Darstellung anpassen",
        "kleiner": "Schrift verkleinern", "groesser": "Schrift vergrößern",
        "kontrast": "Kontrast erhöhen", "vorlesen": "Seite vorlesen", "folgt": "Link folgt",
        "hauptnav": "Hauptnavigation",
        "warn_label": "Warnmeldungen und Waldbrandgefahr",
        "waldbrand": "Waldbrandgefahrenstufe 2 von 5:",
        "waldbrand_wert": "geringe Gefahr (Beispielwert)",
        "munition": "Munitionsbelastung:",
        "munition_text": "Betreten nur auf ausgewiesenen Wegen.",
        "alle_meldungen": "Alle Meldungen",
        "fuss_titel": "Wildnisgebiet Königsbrücker Heide und Naturschutzgebiet Gohrischheide und Elbniederterrasse Zeithain",
        "fuss_text": "Beide Schutzgebiete betreut die NSG-Verwaltung Königsbrücker Heide/Gohrischheide Zeithain im Staatsbetrieb Sachsenforst.",
        "fuss_kontakt": "Kontakt",
        "fuss_kontakt_text": "Postanschrift, Besucheradresse, Telefon und E-Mail der Ansprechpersonen werden mit den Daten des Auftraggebers befüllt.",
        "nnl_titel": "Teil der Nationalen Naturlandschaften",
        "nnl_text": "Das Wildnisgebiet Königsbrücker Heide gehört zu den Nationalen Naturlandschaften, dem Bündnis der deutschen Nationalparks, Biosphärenreservate, Naturparke und Wildnisgebiete.",
        "fussnav": "Rechtliches und Service", "redaktion": "Anmeldung für Redakteure",
        "stand": "Stand des Demonstrators:", "nachoben": "Nach oben",
    },
    "en": {
        "logoplatz_label": "Placeholder for the logos of Staatsbetrieb Sachsenforst and the Free State of Saxony",
        "logoplatz": "Placeholder: logos supplied by the client",
        "menue": "Menu", "aktuelles": "News", "kontakt": "Contact", "karte": "Interactive map",
        "suche_label": "Search this website", "suche_platzhalter": "Search …", "suche_starten": "Start search",
        "sprache": "Choose language", "werkzeuge": "Display settings",
        "kleiner": "Decrease text size", "groesser": "Increase text size",
        "kontrast": "Increase contrast", "vorlesen": "Read page aloud", "folgt": "link to follow",
        "hauptnav": "Main navigation",
        "warn_label": "Warnings and forest fire risk",
        "waldbrand": "Forest fire danger level 2 of 5:",
        "waldbrand_wert": "low danger (example value)",
        "munition": "Unexploded ordnance:",
        "munition_text": "Stay on marked paths.",
        "alle_meldungen": "All notices",
        "fuss_titel": "Königsbrücker Heide Wilderness Area and Gohrischheide und Elbniederterrasse Zeithain Nature Reserve",
        "fuss_text": "Both protected areas are managed by the nature reserve administration within Staatsbetrieb Sachsenforst, the state forestry enterprise of Saxony.",
        "fuss_kontakt": "Contact",
        "fuss_kontakt_text": "Postal address, visitor address, phone numbers and e-mail addresses will be filled in with the client's data.",
        "nnl_titel": "Part of the National Natural Landscapes",
        "nnl_text": "The Königsbrücker Heide Wilderness Area belongs to the National Natural Landscapes, the alliance of Germany's national parks, biosphere reserves, nature parks and wilderness areas.",
        "fussnav": "Legal notices and service", "redaktion": "Editor login",
        "stand": "Demonstrator version:", "nachoben": "Back to top",
    },
}


def brotkrumen(seite, r):
    if seite["pfad"] == "" or seite.get("lang") == "en":
        return ""
    teile = [(f"{r}", "Startseite")]
    stufen = [s for s in seite["pfad"].strip("/").split("/") if s]
    weg = ""
    for i, s in enumerate(stufen):
        weg += s + "/"
        titel = TITEL_NACH_PFAD.get(weg, s)
        teile.append((f"{r}{weg}", titel))
    li = []
    for i, (href, titel) in enumerate(teile):
        if i == len(teile) - 1:
            li.append(f'<li><span aria-current="page">{html.escape(titel)}</span></li>')
        else:
            li.append(f'<li><a href="{href}">{html.escape(titel)}</a></li>')
    return f'<nav class="brotkrumen" aria-label="Brotkrumennavigation"><ol>{"".join(li)}</ol></nav>'


def titelbereich(seite, r):
    """Bildband und Elementform mit dem Seitentitel (Element-Bild-Kombination)."""
    art = seite.get("kopf", "band")
    farbe = seite.get("farbe") or NAV_BY_ID.get(seite.get("bereich"), {}).get("farbe", "dunkelgruengelb")
    schrift = "hell" if farbe in WEISSE_SCHRIFT else "dunkel"
    bildkey = seite.get("bild")
    if art == "start":
        foto = bild(bildkey, r, "held__foto", "100vw", "eager", mit_nachweis=False)
        return f'''
<section class="held" aria-labelledby="seitentitel">
  <div class="held__bild">{foto}{ueberlagerter_nachweis(bildkey)}</div>
  <div class="titelelement titelelement--{farbe} titelelement--{schrift} titelelement--start">
    {form(FORM_TITEL, "titelelement__kante")}
    <div class="wrap titelelement__innen">
      {seite["titelbereich"]}
    </div>
  </div>
</section>'''
    foto = bild(bildkey, r, "band__foto", "100vw", "eager", mit_nachweis=False) if bildkey else ""
    ohne = "" if foto else " band--ohnebild"
    unterzeile = f'<p class="titelelement__unterzeile">{seite["unterzeile"]}</p>' if seite.get("unterzeile") else ""
    return f'''
<div class="band{ohne}">
  <div class="band__bild">{foto or illustration(seite)}{ueberlagerter_nachweis(bildkey) if foto else ""}</div>
  <div class="titelelement titelelement--{farbe} titelelement--{schrift}">
    {form(FORM_TITEL, "titelelement__kante")}
    <div class="wrap titelelement__innen">
      <h1 id="seitentitel">{html.escape(seite["titel"])}</h1>
      {unterzeile}
    </div>
  </div>
</div>'''


def illustration(seite):
    """Eigene Illustration statt Foto: Heidelandschaft aus Flächen der NNL-Palette."""
    return ('<svg class="band__illustration" viewBox="0 0 1440 420" preserveAspectRatio="xMidYMid slice" '
            'aria-hidden="true" focusable="false">'
            '<rect width="1440" height="420" fill="#cce9f3"/>'
            '<path d="M0 250C180 200 320 214 480 236s300 10 460-26 340-30 500 6V420H0z" fill="#b4c897"/>'
            '<path d="M0 300c220-40 420-30 620 0s380 24 560-6 200-10 260 4V420H0z" fill="#719751"/>'
            '<path d="M0 352c260-26 520-18 760 6s460 20 680-10V420H0z" fill="#dcc6a3"/>'
            '<g fill="#576749"><path d="M140 300l26-90 26 90zM200 304l20-70 20 70zM1180 288l28-100 28 100zM1240 296l22-76 22 76z"/></g>'
            '<g fill="#fff"><rect x="340" y="190" width="9" height="130" rx="4"/><rect x="372" y="214" width="7" height="106" rx="3"/>'
            '<rect x="980" y="200" width="9" height="120" rx="4"/></g>'
            '<g fill="#002c50"><rect x="342" y="214" width="5" height="3"/><rect x="342" y="252" width="5" height="3"/>'
            '<rect x="374" y="240" width="3" height="3"/><rect x="982" y="236" width="5" height="3"/></g>'
            '<g fill="#d093a8"><circle cx="520" cy="352" r="6"/><circle cx="560" cy="360" r="5"/><circle cx="600" cy="350" r="6"/>'
            '<circle cx="860" cy="356" r="5"/><circle cx="900" cy="348" r="6"/><circle cx="1320" cy="352" r="6"/></g>'
            '</svg>')


SEITEN = []          # alle Seiten-Metadaten
TITEL_NACH_PFAD = {}  # für Brotkrumen


def seite_rendern(seite, inhalt):
    r = "/nnl-demonstrator/" if seite.get("datei") == "404.html" else rel(seite["pfad"])
    en = seite.get("lang") == "en"
    inhalt = token_ersetzen(inhalt, r, seite)
    m = re.search(r"<!--TITEL-->(.*?)<!--/TITEL-->", inhalt, re.S)
    if m:
        seite["titelbereich"] = m.group(1)
        inhalt = inhalt.replace(m.group(0), "")
    css = "".join(f'<link rel="stylesheet" href="{r}assets/{c}">' for c in seite.get("css", []))
    js = "".join(f'<script src="{r}assets/{j}" defer></script>' for j in seite.get("js", []))
    titel = seite["titel"] if seite["pfad"] else "Startseite"
    if en:
        titel = seite["titel"]
    beschreibung = html.escape(seite.get("beschreibung", "Demonstrator im Design der Nationalen Naturlandschaften."))
    alternates = ""
    if seite["pfad"] in ("", "en/"):
        alternates = (f'<link rel="alternate" hreflang="de" href="{BASIS_URL}">'
                      f'<link rel="alternate" hreflang="en" href="{BASIS_URL}en/">')
    hauptklasse = seite.get("hauptklasse", "")
    return f'''<!doctype html>
<html lang="{"en" if en else "de"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{html.escape(titel)} | Königsbrücker Heide · Gohrischheide (Demonstrator)</title>
<meta name="description" content="{beschreibung}">
<meta name="theme-color" content="#002c50">
<link rel="icon" href="{r}assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{r}assets/fonts/atkinson-hyperlegible-next-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}assets/css/site.css">{css}{alternates}
<script>(function(){{try{{var d=document.documentElement,s=localStorage.getItem("nnl-schrift"),k=localStorage.getItem("nnl-kontrast");if(s)d.setAttribute("data-schrift",s);if(k==="hoch")d.setAttribute("data-kontrast","hoch");}}catch(e){{}}document.documentElement.classList.add("js");}})();</script>
</head>
<body id="seitenanfang">
{sprite()}
<ul class="sprunglinks">
  <li><a href="#inhalt">{"Skip to content" if en else "Zum Inhalt springen"}</a></li>
  <li><a href="#hauptnav">{"Skip to main navigation" if en else "Zur Hauptnavigation springen"}</a></li>
  <li><a href="#suchfeld-eingabe">{"Skip to search" if en else "Zur Suche springen"}</a></li>
</ul>
{demo_html(r, en)}
{warn_html(r, en)}
{kopf_html(seite, r)}
<main id="inhalt" tabindex="-1" class="{hauptklasse}">
{titelbereich(seite, r)}
{brotkrumen(seite, r)}
{inhalt}
</main>
{fuss_html(r, en)}
{dialoge(r, en)}
<script src="{r}assets/js/site.js" defer></script>{js}
</body>
</html>
'''


def dialoge(r, en=False):
    if en:
        return f'''<dialog class="dialog" id="extern-dialog" aria-labelledby="extern-titel">
  <h2 id="extern-titel">You are leaving this website</h2>
  <p>The link opens an external website in a new window. Its operator is responsible for the content.</p>
  <p class="dialog__ziel" id="extern-ziel"></p>
  <p class="dialog__demo" id="extern-demo" hidden>In the demonstrator, the online shop link has no target yet.</p>
  <div class="knopfreihe"><button type="button" class="knopf" data-dialog-schliessen>Cancel</button>
  <a class="knopf knopf--voll" id="extern-weiter" href="#" target="_blank" rel="noopener">Continue{icon("extern")}</a></div>
</dialog>'''
    return f'''<dialog class="dialog" id="extern-dialog" aria-labelledby="extern-titel">
  <h2 id="extern-titel">Sie verlassen diese Website</h2>
  <p>Der Link öffnet eine externe Website in einem neuen Fenster. Für deren Inhalte ist der jeweilige Anbieter verantwortlich.</p>
  <p class="dialog__ziel" id="extern-ziel"></p>
  <p class="dialog__demo" id="extern-demo" hidden>Im Demonstrator führt die Weiterleitung zum Online-Shop noch nicht zum Ziel. Im Projekt wird hier der Shop Korona.Event des Auftraggebers verknüpft.</p>
  <div class="knopfreihe"><button type="button" class="knopf" data-dialog-schliessen>Abbrechen</button>
  <a class="knopf knopf--voll" id="extern-weiter" href="#" target="_blank" rel="noopener">Weiter{icon("extern")}</a></div>
</dialog>'''


# ---------------------------------------------------------------- Bausteine in Inhalten
def karte_teaser(r):
    """Zwei Übersichtsfelder aus den echten Gebietsgrenzen und Wegen (OpenStreetMap)."""
    import math
    daten = json.loads((SRC / "assets/data/gebiete-wege.geojson").read_text("utf8"))
    inhalte = json.loads((SRC / "assets/data/karteninhalte.json").read_text("utf8"))
    gebiet_von = {w["id"]: w["gebiet"] for w in inhalte["wege"]}
    gebiet_von.update({"kh": "kh", "gh": "gh"})
    kx, ky = math.cos(math.radians(51.35)) * 111.32, 110.57
    felder = [("kh", "Königsbrücker Heide", 0), ("gh", "Gohrischheide", 520)]
    teile = []
    for gid, name, x0 in felder:
        feats = [f for f in daten["features"] if gebiet_von.get(f["properties"]["id"]) == gid]
        pts = []
        for f in feats:
            g = f["geometry"]
            linien = [ring for poly in g["coordinates"] for ring in poly] if g["type"] == "MultiPolygon" else g["coordinates"]
            for l in linien:
                pts += [(x * kx, y * ky) for x, y in l]
        minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
        miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
        m = min(440 / (maxx - minx), 360 / (maxy - miny))
        ox = x0 + 20 + (440 - (maxx - minx) * m) / 2
        oy = 20 + (360 - (maxy - miny) * m) / 2
        def pkt(x, y):
            return f"{ox + (x * kx - minx) * m:.1f},{oy + (maxy - y * ky) * m:.1f}"
        for f in sorted(feats, key=lambda f: f["properties"]["art"] != "gebiet"):
            g, art = f["geometry"], f["properties"]["art"]
            if g["type"] == "MultiPolygon":
                for poly in g["coordinates"]:
                    teile.append(f'<path class="mk-gebiet" d="M{" L".join(pkt(*q) for q in poly[0])}Z"/>')
            else:
                for l in g["coordinates"]:
                    teile.append(f'<path class="mk-{art}" d="M{" L".join(pkt(*q) for q in l)}"/>')
        teile.append(f'<text x="{x0 + 240}" y="430" class="mk-text">{name}</text>')
    return ('<svg class="minikarte" viewBox="0 0 1000 450" role="img" aria-labelledby="minikarte-titel">'
            '<title id="minikarte-titel">Umrisse der beiden Schutzgebiete mit Besucherpfaden und Radrundwegen, '
            'jeweils eigener Maßstab</title>' + "".join(teile) + "</svg>")


def termine_liste(r, anzahl=None, kompakt=False):
    termine = json.loads((SRC / "assets/data/termine.json").read_text("utf8"))
    termine.sort(key=lambda t: t["beginn"])
    if anzahl:
        termine = termine[:anzahl]
    monate = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
              "Oktober", "November", "Dezember"]
    tage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    li = []
    for t in termine:
        d = datetime.datetime.fromisoformat(t["beginn"])
        e = datetime.datetime.fromisoformat(t["ende"])
        zeit = f"{d:%H:%M} bis {e:%H:%M} Uhr"
        li.append(f'''<li class="termin" data-id="{t["id"]}" data-monat="{d:%Y-%m}" data-art="{html.escape(t["art"])}" data-ort="{html.escape(t["gebiet"])}">
  <div class="termin__datum" aria-hidden="true"><span class="termin__tag">{d.day}</span><span class="termin__monat">{monate[d.month - 1][:3]}</span></div>
  <div class="termin__text">
    <h3 class="termin__titel">{html.escape(t["titel"])}</h3>
    <p class="termin__meta"><span class="visually-hidden">Datum: </span>{tage[d.weekday()]}, {d.day}. {monate[d.month - 1]} {d.year} · {zeit}</p>
    <p class="termin__meta">{icon("ort")}{html.escape(t["ort"])} · {html.escape(t["art"])}</p>
    {"" if kompakt else f'<p>{html.escape(t["text"])}</p>'}
    <p class="termin__marken"><span class="marke marke--beispiel">Beispieltermin</span></p>
  </div>
  {"" if kompakt else f'<div class="termin__aktion"><a class="knopf knopf--klein" href="{r}teilnehmen-buchen/">Teilnehmen &amp; Buchen{icon("pfeil")}</a></div>'}
</li>''')
    return "".join(li)


def kalender(r):
    termine = json.loads((SRC / "assets/data/termine.json").read_text("utf8"))
    monate = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
              "Oktober", "November", "Dezember"]
    mon = sorted({t["beginn"][:7] for t in termine})
    arten = sorted({t["art"] for t in termine})
    orte = sorted({t["gebiet"] for t in termine})
    o_mon = "".join(f'<option value="{m}">{monate[int(m[5:]) - 1]} {m[:4]}</option>' for m in mon)
    o_art = "".join(f'<option>{html.escape(a)}</option>' for a in arten)
    o_ort = "".join(f'<option>{html.escape(o)}</option>' for o in orte)
    return f'''<form class="kalender__filter" data-kalender-filter aria-label="Termine filtern">
  <div class="feld"><label for="f-monat">Monat</label><select id="f-monat" data-filter="monat"><option value="">Alle Monate</option>{o_mon}</select></div>
  <div class="feld"><label for="f-art">Art der Veranstaltung</label><select id="f-art" data-filter="art"><option value="">Alle Arten</option>{o_art}</select></div>
  <div class="feld"><label for="f-ort">Gebiet</label><select id="f-ort" data-filter="ort"><option value="">Beide Gebiete</option>{o_ort}</select></div>
</form>
<p class="kalender__status" role="status" data-kalender-status>{len(termine)} Termine. Alle Termine sind Beispieldaten.</p>
<ul class="termine" data-kalender-liste>{termine_liste(r)}</ul>
<div class="kalender__export">
  <button type="button" class="knopf knopf--klein" data-export="ics" data-root="{r}">{icon("kalender")}Gefilterte Termine als iCal</button>
  <button type="button" class="knopf knopf--klein" data-export="csv" data-root="{r}">{icon("download")}Gefilterte Termine als CSV</button>
</div>
<p class="quelle">Der Export funktioniert mit Outlook, Apple Kalender, Google Kalender und Excel. Für den Import aus externen Kalendern ist eine offene Schnittstelle (iCal, CSV) vorgesehen.</p>'''


def pfadliste(r, gebiet):
    inhalte = json.loads((SRC / "assets/data/karteninhalte.json").read_text("utf8"))
    out = []
    for p in inhalte["wege"]:
        if p["gebiet"] != gebiet:
            continue
        art = "Radrundweg" if p["art"] == "rad" else "Wanderpfad"
        out.append(f'''<li class="pfad" id="pfad-{p["id"]}">
  <div class="pfad__icon" aria-hidden="true">{icon("rad" if p["art"] == "rad" else "wandern")}</div>
  <div class="pfad__text">
    <h3 class="pfad__titel">{html.escape(p["name"])}</h3>
    <p class="pfad__art">{art}</p>
    <p>{html.escape(p["text"])}</p>
    <p class="pfad__aktionen">
      <button type="button" class="knopf knopf--klein" data-zeige-weg="{p["id"]}">{icon("fokus")}Auf der Karte zeigen</button>
      <span class="knopf knopf--klein knopf--inaktiv" aria-disabled="true">{icon("download")}Faltblatt (PDF, folgt)</span>
    </p>
  </div>
</li>''')
    return "".join(out)


def zielliste(r, gebiet=None):
    inhalte = json.loads((SRC / "assets/data/karteninhalte.json").read_text("utf8"))
    out = []
    for z in inhalte["ziele"]:
        if gebiet and z["gebiet"] != gebiet:
            continue
        g = "Königsbrücker Heide" if z["gebiet"] == "kh" else "Gohrischheide"
        shop = (f' <a class="knopf knopf--klein" href="{r}teilnehmen-buchen/">Buchen{icon("pfeil")}</a>'
                if z.get("buchbar") else "")
        out.append(f'''<li class="ziel" id="ziel-{z["id"]}">
  <div class="pfad__icon" aria-hidden="true">{icon(z["icon"])}</div>
  <div class="pfad__text">
    <h3 class="pfad__titel">{html.escape(z["name"])}</h3>
    <p class="pfad__art">{html.escape(z["typ"])} · {g}</p>
    <p>{html.escape(z["text"])}</p>
    <p class="pfad__aktionen"><button type="button" class="knopf knopf--klein" data-zeige-ziel="{z["id"]}">{icon("fokus")}Auf der Karte zeigen</button>{shop}</p>
  </div>
</li>''')
    return "".join(out)


def token_ersetzen(text, r, seite):
    text = text.replace("{{R}}", r)
    text = re.sub(r"\{\{icon ([a-z-]+)\}\}", lambda m: icon(m.group(1)), text)
    text = re.sub(r"\{\{bild ([a-z0-9-]+)(?: ([a-z_-]+))?(?: ([^}]+))?\}\}",
                  lambda m: bild(m.group(1), r, m.group(2) or "", m.group(3) or "(min-width: 900px) 50vw, 100vw"), text)
    text = text.replace("{{minikarte}}", karte_teaser(r))
    if "{{kalender}}" in text:
        text = text.replace("{{kalender}}", kalender(r))
    text = re.sub(r"\{\{termine( \d+)?( kompakt)?\}\}",
                  lambda m: termine_liste(r, int(m.group(1)) if m.group(1) else None, bool(m.group(2))), text)
    text = re.sub(r"\{\{pfade (kh|gh)\}\}", lambda m: pfadliste(r, m.group(1)), text)
    text = re.sub(r"\{\{ziele( kh| gh)?\}\}", lambda m: zielliste(r, (m.group(1) or "").strip() or None), text)
    text = re.sub(r"\{\{welle (oben|unten) ([a-z]+)\}\}",
                  lambda m: form(FORM_OBEN if m.group(1) == "oben" else FORM_UNTEN,
                                 f"welle welle--{m.group(1)} welle--{m.group(2)}"), text)
    text = text.replace("{{uebersicht}}", uebersicht_karten(seite, r))
    text = text.replace("{{demohinweis}}", DEMO_HINWEIS)
    if "{{bildnachweise}}" in text:
        zeilen = "".join(
            f'<tr><td>{html.escape(b["alt"])}</td><td>{html.escape(b["urheber"])}</td>'
            f'<td><a href="{b["lizenz_url"]}" rel="license noopener">{html.escape(b["lizenz"])}</a></td>'
            f'<td><a href="{b["quelle"]}" rel="noopener">{html.escape(b["titel"].replace("File:", "Datei: "))}</a>'
            f'{"<br>" + html.escape(b["symbolbild"]) if b.get("symbolbild") else ""}<br>{html.escape(b["aenderung"])}</td></tr>'
            for b in BILDER.values())
        text = text.replace("{{bildnachweise}}", '<div class="tabellenhuelle"><table class="tabelle"><thead><tr><th scope="col">Motiv</th>'
                            '<th scope="col">Urheber</th><th scope="col">Lizenz</th><th scope="col">Quelle und Änderung</th></tr></thead>'
                            f'<tbody>{zeilen}</tbody></table></div>')
    return text


def uebersicht_karten(seite, r):
    n = NAV_BY_ID.get(seite.get("bereich"))
    if not n:
        return ""
    karten = []
    for key, titel, text in n["unter"]:
        karten.append(f'''<li class="karte karte--text">
  <div class="karte__icon" aria-hidden="true">{icon(n["icon"])}</div>
  <h2 class="karte__titel"><a href="{r}{n["id"]}/{key}/">{html.escape(titel)}</a></h2>
  <p>{html.escape(text)}</p>
  <p class="karte__mehr" aria-hidden="true">Mehr erfahren{icon("pfeil")}</p>
</li>''')
    return f'<ul class="karten karten--drei" role="list">{"".join(karten)}</ul>'


# ---------------------------------------------------------------- Seiten einlesen
def meta_lesen(datei):
    roh = datei.read_text("utf8")
    m = re.match(r"\s*<!--META\s*(\{.*?\})\s*-->\s*", roh, re.S)
    if not m:
        raise SystemExit(f"META fehlt in {datei.name}")
    return json.loads(m.group(1)), roh[m.end():]


def platzhalter_inhalt(titel, text, bereich_titel=None):
    zurueck = ""
    return f'''
<div class="wrap wrap--text abschnitt">
  <p class="einleitung">{html.escape(text)}</p>
  <div class="infobox infobox--himmelblau">
    <h2 class="infobox__titel">Platzhalter im Demonstrator</h2>
    <p>Diese Seite gehört zur Sitemap der neuen Website und ist im Demonstrator nur angelegt. Navigation,
    Brotkrumen und Seitentyp stehen; die Inhalte liefert die Redaktion.</p>
  </div>
  {zurueck}
</div>'''


def alle_seiten():
    seiten = []
    for datei in sorted((SRC / "seiten").glob("*.html")):
        meta, inhalt = meta_lesen(datei)
        meta["quelle"] = datei.name
        seiten.append((meta, inhalt))
    vorhanden = {m["pfad"] for m, _ in seiten}
    # Platzhalter für alle übrigen Sitemap-Seiten
    for n in NAV:
        for key, titel, text in n["unter"]:
            pfad = f'{n["id"]}/{key}/'
            if pfad not in vorhanden:
                seiten.append(({"pfad": pfad, "titel": titel, "bereich": n["id"],
                                "beschreibung": text, "unterzeile": n["titel"], "platzhalter": True},
                               platzhalter_inhalt(titel, text)))
    for n in NAV:
        pfad = f'{n["id"]}/'
        if n["unter"] and pfad not in vorhanden:
            seiten.append(({"pfad": pfad, "titel": n["titel"], "bereich": n["id"], "bild": n.get("bild"),
                            "unterzeile": n.get("unterzeile", ""), "beschreibung": f'Übersicht {n["titel"]}'},
                           '<div class="wrap abschnitt">{{uebersicht}}</div>'))
    for key, (titel, text) in PLATZHALTER_FUSS.items():
        pfad = f"{key}/"
        if pfad not in vorhanden:
            seiten.append(({"pfad": pfad, "titel": titel, "beschreibung": text,
                            "farbe": "dunkelblau", "platzhalter": True}, platzhalter_inhalt(titel, text)))
    return seiten


# ---------------------------------------------------------------- Prüfungen
def sichtbarer_text(dok):
    t = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", dok, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(t)


def pruefen(pfad, dok):
    fehler = []
    text = sichtbarer_text(dok)
    if re.search("[–—]", text):
        stelle = re.search(".{0,40}[–—].{0,40}", text).group(0)
        fehler.append(f"Gedankenstrich: …{stelle}…")
    if re.search(r"\s-\s", text):
        stelle = re.search(r".{0,40}\s-\s.{0,40}", text).group(0)
        fehler.append(f"Bindestrich als Gedankenstrich: …{stelle}…")
    if DEMO_HINWEIS not in text:
        fehler.append("Demonstrator-Hinweis fehlt")
    if 'content="noindex, nofollow"' not in dok:
        fehler.append("noindex fehlt")
    for img in re.findall(r"<img[^>]*>", dok):
        if 'alt="' not in img:
            fehler.append(f"Bild ohne alt: {img[:80]}")
    return fehler


def links_pruefen(dateien):
    fehler = []
    for datei in dateien:
        if datei.name == "404.html":
            continue
        dok = datei.read_text("utf8")
        for href in re.findall(r'(?:href|src)="([^"#]+)(?:#[^"]*)?"', dok):
            if href.startswith(("http:", "https:", "mailto:", "tel:", "data:")):
                continue
            ziel = (datei.parent / href).resolve()
            if href.endswith("/"):
                ziel = ziel / "index.html"
            if not ziel.exists():
                fehler.append(f"{datei.relative_to(OUT)}: Link ins Leere {href}")
    return fehler


# ---------------------------------------------------------------- Suchindex
def norm(s):
    s = s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def index_eintrag(seite, dok):
    m = re.search(r"<main[^>]*>(.*)</main>", dok, re.S)
    hauptteil = m.group(1) if m else dok
    hauptteil = re.sub(r'<nav class="brotkrumen".*?</nav>', " ", hauptteil, flags=re.S)
    ueberschriften = [html.unescape(re.sub(r"<[^>]+>", "", h)).strip()
                      for h in re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", hauptteil, re.S)]
    text = re.sub(r"\s+", " ", sichtbarer_text(hauptteil)).strip()
    return {"titel": seite["titel"], "url": seite["pfad"], "bereich": NAV_BY_ID.get(seite.get("bereich"), {}).get("titel", ""),
            "ueberschriften": ueberschriften[:20], "text": text[:4000]}


# ---------------------------------------------------------------- Hauptteil
def main():
    if OUT.exists():
        for kind in OUT.iterdir():
            if kind.is_dir():
                shutil.rmtree(kind)
            else:
                kind.unlink()
    OUT.mkdir(exist_ok=True)
    shutil.copytree(SRC / "assets", OUT / "assets", ignore=shutil.ignore_patterns("fotos.json", ".DS_Store", "quelle"))
    (OUT / ".nojekyll").write_text("")

    seiten = alle_seiten()
    for meta, _ in seiten:
        TITEL_NACH_PFAD[meta["pfad"]] = meta["titel"]
    for n in NAV:
        TITEL_NACH_PFAD.setdefault(f'{n["id"]}/', n["titel"])

    fehler, index, dateien = [], [], []
    for meta, inhalt in seiten:
        dok = seite_rendern(meta, inhalt)
        ziel = OUT / meta["pfad"] / "index.html" if meta["pfad"] else OUT / "index.html"
        if meta.get("datei"):
            ziel = OUT / meta["datei"]
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(dok, "utf8")
        dateien.append(ziel)
        fehler += [f"{meta['pfad'] or '/'}: {f}" for f in pruefen(meta["pfad"], dok)]
        if not meta.get("nicht_suchen"):
            index.append(index_eintrag(meta, dok))
    (OUT / "assets/data/suchindex.json").write_text(json.dumps(index, ensure_ascii=False), "utf8")
    fehler += links_pruefen(dateien)
    print(f"{len(dateien)} Seiten gebaut nach {OUT}")
    if fehler:
        print("\n".join(fehler))
        sys.exit(1)


if __name__ == "__main__":
    main()
