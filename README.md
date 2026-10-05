# NNL-Demonstrator: Königsbrücker Heide · Gohrischheide

Demonstrator der dioptify UG (haftungsbeschränkt) zur Ausschreibung 2026-VG-NG17_0001
„Relaunch Website“. **Keine offizielle Website des Staatsbetriebs Sachsenforst.**

Der Demonstrator zeigt die geplante Website der NSG-Verwaltung Königsbrücker Heide/Gohrischheide
Zeithain im Corporate Design der Nationalen Naturlandschaften: Startseite, Unterseiten nach der
Sitemap (Anlage 5b), interaktive Karte, Warnmeldungen, Veranstaltungskalender, Suche, Deutsch und
Englisch, Leichte Sprache. Abrufbar unter https://birkenpapier.github.io/nnl-demonstrator/

## Bauen

    python3 build.py                     # schreibt nach docs/ (GitHub Pages)
    python3 -m http.server -d docs 8000  # lokal ansehen

## Fremde Bestandteile und Lizenzen

- Schrift Atkinson Hyperlegible Next, SIL Open Font License 1.1 (`src/assets/fonts/OFL.txt`),
  als frei lizenzierte Ersatzschrift für die FS Me
- Leaflet 1.9.4, BSD-2-Clause (`src/assets/vendor/leaflet/LICENSE.txt`)
- Gebietsgrenzen und Wege (`src/assets/data/gebiete-wege.geojson`): © OpenStreetMap-Mitwirkende, ODbL 1.0
- Fotos: Wikimedia Commons, CC0 und CC BY, Nachweise im Impressum und in `src/assets/img/fotos.json`

Logos der Nationalen Naturlandschaften, des Staatsbetriebs Sachsenforst und des Freistaates Sachsen
sind nicht enthalten. Die Wellenformen und Infoboxen sind eigene Nachbildungen der NNL-Dialogelemente.
