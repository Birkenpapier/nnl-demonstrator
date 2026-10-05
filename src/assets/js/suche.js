/* Volltextsuche über den beim Bau erzeugten Index, Trefferliste mit Ranking. */
(function () {
  "use strict";
  var liste = document.getElementById("suche-treffer");
  if (!liste) return;
  var R = liste.getAttribute("data-root") || "";
  var status = document.getElementById("suche-status");
  var feld = document.getElementById("suche-q");
  var q = (new URLSearchParams(location.search).get("q") || "").trim();
  feld.value = q;
  if (!q) return;
  function norm(s) { return s.toLowerCase().replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss").normalize("NFKD").replace(/[̀-ͯ]/g, ""); }
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
  fetch(R + "assets/data/suchindex.json").then(function (r) { return r.json(); }).then(function (index) {
    var woerter = norm(q).split(/\s+/).filter(function (w) { return w.length > 1; });
    var treffer = index.map(function (s) {
      var t = norm(s.titel), u = norm(s.ueberschriften.join(" ")), x = norm(s.text), punkte = 0, alle = true;
      woerter.forEach(function (w) {
        var p = 0;
        if (t.indexOf(w) !== -1) p += 10;
        if (u.indexOf(w) !== -1) p += 4;
        var n = x.split(w).length - 1;
        p += Math.min(n, 6);
        if (!p) alle = false;
        punkte += p;
      });
      return { s: s, punkte: alle ? punkte : 0 };
    }).filter(function (e) { return e.punkte > 0; }).sort(function (a, b) { return b.punkte - a.punkte; });
    status.textContent = treffer.length ? treffer.length + (treffer.length === 1 ? " Treffer" : " Treffer") + " für „" + q + "“" : "Keine Treffer für „" + q + "“. Versuchen Sie einen anderen Begriff.";
    liste.innerHTML = treffer.slice(0, 30).map(function (e) {
      var s = e.s, roh = s.text, n = norm(roh), pos = -1;
      woerter.some(function (w) { pos = n.indexOf(w); return pos !== -1; });
      var start = Math.max(0, pos - 80), aus = (start ? "… " : "") + roh.substr(start, 220) + " …";
      var html = esc(aus);
      woerter.forEach(function (w) {
        var re = new RegExp("(" + q.split(/\s+/).map(function (x) { return x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }).join("|") + ")", "gi");
        html = html.replace(re, "<mark>$1</mark>");
      });
      return '<li><p class="treffer__bereich">' + esc(s.bereich || "Website") + '</p><h2 class="treffer__titel"><a href="' + R + s.url + '">' + esc(s.titel) + '</a></h2><p>' + html + '</p><p class="treffer__url">' + esc(R + s.url) + '</p></li>';
    }).join("");
  });
})();
