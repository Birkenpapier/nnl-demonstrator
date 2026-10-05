/* Interaktive Karte (Leaflet, OpenStreetMap). Überblick mit Gebietsumrissen,
   Zoom in ein Gebiet zeigt Pfade und Aussichtspunkte, Störungsmeldung per Klick. */
(function () {
  "use strict";
  var el = document.getElementById("karte");
  if (!el || !window.L) return;
  var R = el.getAttribute("data-root") || "";
  var modus = el.getAttribute("data-modus") || "pfade";
  var DETAIL_ZOOM = 11;
  var FARBE = { gebiet: "#446428", pfad: "#962e45", rad: "#23538a" };

  var map = L.map(el, { scrollWheelZoom: false, zoomSnap: 0.25, minZoom: 8, maxZoom: 17 });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap-Mitwirkende</a>'
  }).addTo(map);
  map.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>');
  map.on("click focus", function () { map.scrollWheelZoom.enable(); });
  map.on("mouseout blur", function () { map.scrollWheelZoom.disable(); });

  var ebenen = { pfad: L.layerGroup(), rad: L.layerGroup(), ziele: L.layerGroup() };
  var gebiete = {}, wege = {}, ziele = {}, alleGrenzen = L.latLngBounds([]), detailGrenzen = {};
  var sichtbar = { pfad: true, rad: true, ziele: true };
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
  function iconSvg(n) { return '<svg class="icon" aria-hidden="true" focusable="false"><use href="#i-' + n + '"/></svg>'; }

  Promise.all([
    fetch(R + "assets/data/gebiete-wege.geojson").then(function (r) { return r.json(); }),
    fetch(R + "assets/data/karteninhalte.json").then(function (r) { return r.json(); })
  ]).then(function (daten) {
    var geo = daten[0], inhalt = daten[1];
    var texte = {};
    inhalt.wege.forEach(function (w) { texte[w.id] = w; });
    var gebietInfo = {};
    inhalt.gebiete.forEach(function (g) { gebietInfo[g.id] = g; });

    geo.features.forEach(function (f) {
      var p = f.properties;
      if (p.art === "gebiet") {
        var gid = p.id;
        var info = gebietInfo[gid] || { name: p.name, kurz: p.name, text: "" };
        var lyr = L.geoJSON(f, { style: { color: FARBE.gebiet, weight: 3, fillColor: "#b4c897", fillOpacity: 0.32 } });
        lyr.bindTooltip(info.kurz, { permanent: true, direction: "center", className: "gebietsname" });
        lyr.on("click", function () { zeigeGebiet(gid); });
        lyr.addTo(map);
        gebiete[gid] = lyr;
        alleGrenzen.extend(lyr.getBounds());
      } else {
        var t = texte[p.id] || { name: p.name, text: "", gebiet: "", art: p.art };
        var art = p.art === "rad" ? "rad" : "pfad";
        var unter = L.geoJSON(f, { style: { color: "#fff", weight: 8, opacity: 0.95 }, interactive: false });
        var linie = L.geoJSON(f, { style: { color: FARBE[art], weight: 4.5, dashArray: art === "rad" ? "9 7" : null } });
        var link = modus === "pfade" ? "#pfad-" + p.id : R + "besuchen/besucherpfade/#pfad-" + p.id;
        linie.bindPopup('<p class="popup__art">' + (art === "rad" ? "Radrundweg" : "Wanderpfad") + '</p><h3>' + esc(t.name) +
          '</h3><p>' + esc(t.text) + '</p><p class="popup__links"><a href="' + link + '">Mehr erfahren …</a>' +
          '<a href="' + R + 'teilnehmen-buchen/">Geführte Wanderung buchen</a></p>');
        var gruppe = L.layerGroup([unter, linie]);
        gruppe.gebiet = t.gebiet;
        ebenen[art].addLayer(gruppe);
        wege[p.id] = linie;
        if (t.gebiet) { detailGrenzen[t.gebiet] = detailGrenzen[t.gebiet] || L.latLngBounds([]); detailGrenzen[t.gebiet].extend(linie.getBounds()); }
      }
    });

    inhalt.ziele.forEach(function (z) {
      var art = z.icon === "huette" ? "huette" : (z.icon === "info" ? "info" : "turm");
      var m = L.marker(z.lage, {
        title: z.name, alt: z.name, keyboard: true,
        icon: L.divIcon({ className: "", html: '<span class="kartenpunkt kartenpunkt--' + art + '">' + iconSvg(z.icon) + '</span>', iconSize: [38, 38], iconAnchor: [19, 19], popupAnchor: [0, -18] })
      });
      var mehr = (modus === "ziele" ? "#ziel-" : R + "besuchen/ausflugsziele/#ziel-") + z.id;
      m.bindPopup('<p class="popup__art">' + esc(z.typ) + '</p><h3>' + esc(z.name) + '</h3><p>' + esc(z.text) + '</p>' +
        '<p class="popup__links"><a href="' + mehr + '">Mehr erfahren …</a>' + (z.buchbar ? '<a href="' + R + 'teilnehmen-buchen/">Teilnehmen &amp; Buchen</a>' : '') + '</p>');
      m.gebiet = z.gebiet;
      ebenen.ziele.addLayer(m);
      ziele[z.id] = m;
      detailGrenzen[z.gebiet] = detailGrenzen[z.gebiet] || L.latLngBounds([]);
      detailGrenzen[z.gebiet].extend(z.lage);
    });

    var auswahl = document.getElementById("meldung-pfad");
    if (auswahl) inhalt.wege.forEach(function (w) { var o = document.createElement("option"); o.textContent = w.name; auswahl.appendChild(o); });

    map.fitBounds(alleGrenzen, { padding: [24, 24] });
    map.on("zoomend", aktualisiere);
    aktualisiere();
    var start = (location.hash.match(/gebiet=(kh|gh)/) || [])[1];
    if (start) zeigeGebiet(start);
  }).catch(function () {
    el.innerHTML = '<p style="padding:2rem">Die Karte konnte nicht geladen werden. Alle Wege stehen in der Liste unter der Karte.</p>';
  });

  function aktualisiere() {
    var detail = map.getZoom() >= DETAIL_ZOOM;
    ["pfad", "rad"].forEach(function (k) {
      var an = sichtbar[k] && detail;
      if (an && !map.hasLayer(ebenen[k])) ebenen[k].addTo(map);
      if (!an && map.hasLayer(ebenen[k])) map.removeLayer(ebenen[k]);
    });
    var zieleAn = sichtbar.ziele && (detail || modus === "ziele");
    if (zieleAn && !map.hasLayer(ebenen.ziele)) ebenen.ziele.addTo(map);
    if (!zieleAn && map.hasLayer(ebenen.ziele)) map.removeLayer(ebenen.ziele);
    Object.keys(gebiete).forEach(function (g) {
      gebiete[g].setStyle({ fillOpacity: detail ? 0.14 : 0.32 });
      gebiete[g].eachLayer(function (l) { var t = l.getTooltip && l.getTooltip(); if (t) l.setTooltipContent(t.getContent()); });
    });
    el.setAttribute("aria-label", "Karte der Schutzgebiete" + (detail ? " mit Besucherpfaden und Aussichtspunkten" : ", Überblick"));
  }

  var knoepfe = document.querySelectorAll("[data-gebiet]");
  function druecke(id) { knoepfe.forEach(function (k) { k.setAttribute("aria-pressed", k.getAttribute("data-gebiet") === id ? "true" : "false"); }); }
  function zeigeGebiet(id) {
    if (id === "alle" || !gebiete[id]) { map.flyToBounds(alleGrenzen, { padding: [24, 24], duration: 0.8 }); druecke("alle"); return; }
    var g = L.latLngBounds(gebiete[id].getBounds().getSouthWest(), gebiete[id].getBounds().getNorthEast());
    if (detailGrenzen[id]) g.extend(detailGrenzen[id]);
    map.flyToBounds(g, { padding: [16, 16], duration: 0.8, maxZoom: 13 });
    druecke(id);
  }
  knoepfe.forEach(function (k) { k.addEventListener("click", function () { zeigeGebiet(k.getAttribute("data-gebiet")); }); });
  document.querySelectorAll("[data-ebene]").forEach(function (c) {
    c.addEventListener("change", function () { sichtbar[c.getAttribute("data-ebene")] = c.checked; aktualisiere(); });
  });

  function zurKarte() { document.getElementById("karte-bereich").scrollIntoView({ block: "start" }); el.focus({ preventScroll: true }); }
  document.addEventListener("click", function (e) {
    var w = e.target.closest("[data-zeige-weg]"), z = e.target.closest("[data-zeige-ziel]");
    if (w && wege[w.getAttribute("data-zeige-weg")]) {
      var l = wege[w.getAttribute("data-zeige-weg")];
      zurKarte();
      map.fitBounds(l.getBounds(), { padding: [30, 30], maxZoom: 15 });
      map.once("moveend", function () { l.openPopup(l.getBounds().getCenter()); });
    } else if (z && ziele[z.getAttribute("data-zeige-ziel")]) {
      var m = ziele[z.getAttribute("data-zeige-ziel")];
      zurKarte();
      map.setView(m.getLatLng(), 15);
      map.once("moveend", function () { m.openPopup(); });
    }
  });

  /* Störungsmeldung */
  var start = document.querySelector("[data-meldung-start]");
  var dialog = document.getElementById("meldung-dialog");
  var hinweis = document.getElementById("karte-hinweis");
  var meldeMarker = null, meldemodus = false;
  function oeffneMeldung() {
    if (!dialog || typeof dialog.showModal !== "function") return;
    var ok = dialog.querySelector(".formular__ok"); if (ok) ok.hidden = true;
    dialog.showModal();
  }
  if (start) start.addEventListener("click", function (e) {
    if (e.detail === 0) { oeffneMeldung(); return; }   /* Tastatur: direkt zum Formular */
    meldemodus = true;
    document.querySelector(".kartenmodul").classList.add("karte--meldemodus");
    if (hinweis) hinweis.hidden = false;
    zurKarte();
  });
  map.on("click", function (e) {
    if (!meldemodus) return;
    meldemodus = false;
    document.querySelector(".kartenmodul").classList.remove("karte--meldemodus");
    if (hinweis) hinweis.hidden = true;
    if (meldeMarker) map.removeLayer(meldeMarker);
    meldeMarker = L.marker(e.latlng, { icon: L.divIcon({ className: "", html: '<span class="kartenpunkt kartenpunkt--meldung">' + iconSvg("stoerung") + "</span>", iconSize: [38, 38], iconAnchor: [19, 19] }), title: "Gemeldete Stelle" }).addTo(map);
    var ort = document.getElementById("meldung-ort");
    if (ort) ort.value = e.latlng.lat.toFixed(5) + ", " + e.latlng.lng.toFixed(5);
    oeffneMeldung();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && meldemodus) { meldemodus = false; if (hinweis) hinweis.hidden = true; document.querySelector(".kartenmodul").classList.remove("karte--meldemodus"); }
  });
  if (dialog) dialog.addEventListener("click", function (e) { if (e.target.closest("[data-meldung-schliessen]")) dialog.close(); });
})();
