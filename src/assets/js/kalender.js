/* Veranstaltungskalender: Filter nach Monat, Art und Gebiet, Export als iCal und CSV. */
(function () {
  "use strict";
  var form = document.querySelector("[data-kalender-filter]");
  var liste = document.querySelector("[data-kalender-liste]");
  if (!form || !liste) return;
  var status = document.querySelector("[data-kalender-status]");
  var termine = Array.prototype.slice.call(liste.querySelectorAll(".termin"));
  var daten = null;

  function filtern() {
    var f = {};
    form.querySelectorAll("[data-filter]").forEach(function (s) { f[s.getAttribute("data-filter")] = s.value; });
    var n = 0;
    termine.forEach(function (t) {
      var ok = (!f.monat || t.getAttribute("data-monat") === f.monat) && (!f.art || t.getAttribute("data-art") === f.art) && (!f.ort || t.getAttribute("data-ort") === f.ort);
      t.hidden = !ok;
      if (ok) n++;
    });
    status.textContent = (n === 1 ? "1 Termin" : n + " Termine") + (n ? ". Alle Termine sind Beispieldaten." : " gefunden. Bitte Filter ändern.");
  }
  form.addEventListener("change", filtern);
  form.addEventListener("submit", function (e) { e.preventDefault(); });

  function sichtbareIds() { return termine.filter(function (t) { return !t.hidden; }).map(function (t) { return t.getAttribute("data-id"); }); }
  function laden(R) {
    if (daten) return Promise.resolve(daten);
    return fetch(R + "assets/data/termine.json").then(function (r) { return r.json(); }).then(function (d) { daten = d; return d; });
  }
  function ics(d) { return d.replace(/[-:]/g, "") + "00"; }
  function esc(s) { return String(s).replace(/\\/g, "\\\\").replace(/;/g, "\;").replace(/,/g, "\\,").replace(/\n/g, "\\n"); }
  function speichern(name, inhalt, typ) {
    var b = new Blob([inhalt], { type: typ });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(b); a.download = name;
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }
  document.addEventListener("click", function (e) {
    var k = e.target.closest("[data-export]");
    if (!k) return;
    var art = k.getAttribute("data-export");
    laden(k.getAttribute("data-root") || "").then(function (alle) {
      var ids = sichtbareIds();
      var auswahl = alle.filter(function (t) { return ids.indexOf(t.id) !== -1; });
      if (art === "ics") {
        var z = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//NNL-Demonstrator//Veranstaltungen//DE", "X-WR-TIMEZONE:Europe/Berlin"];
        auswahl.forEach(function (t) {
          z.push("BEGIN:VEVENT", "UID:" + t.id + "@nnl-demonstrator", "DTSTAMP:20261005T080000Z", "DTSTART;TZID=Europe/Berlin:" + ics(t.beginn),
            "DTEND;TZID=Europe/Berlin:" + ics(t.ende), "SUMMARY:" + esc(t.titel + " (Beispieltermin)"), "LOCATION:" + esc(t.ort + ", " + t.gebiet),
            "DESCRIPTION:" + esc(t.text), "END:VEVENT");
        });
        z.push("END:VCALENDAR");
        speichern("veranstaltungen.ics", z.join("\r\n"), "text/calendar");
      } else {
        var c = ["Titel;Beginn;Ende;Art;Gebiet;Ort;Beschreibung"];
        auswahl.forEach(function (t) {
          c.push([t.titel, t.beginn.replace("T", " "), t.ende.replace("T", " "), t.art, t.gebiet, t.ort, t.text].map(function (v) { return '"' + String(v).replace(/"/g, '""') + '"'; }).join(";"));
        });
        speichern("veranstaltungen.csv", "\ufeff" + c.join("\r\n"), "text/csv;charset=utf-8");
      }
      status.textContent = auswahl.length + " Termine exportiert.";
    });
  });
})();
