/* Grundfunktionen des Demonstrators: Navigation, Darstellung, Vorlesen,
   Anzeigezeitraum von Meldungen, Hinweis vor externen Links. Ohne Bibliotheken. */
(function () {
  "use strict";
  var doc = document.documentElement;
  var en = doc.lang === "en";

  function lies(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function schreib(k, v) { try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { /* privat */ } }

  /* ---------------- Hauptnavigation: Klappmenüs ---------------- */
  var knoepfe = Array.prototype.slice.call(document.querySelectorAll("button.hauptnav__knopf"));
  function schliesseAlle(ausser) {
    knoepfe.forEach(function (k) {
      if (k === ausser) return;
      k.setAttribute("aria-expanded", "false");
      var p = document.getElementById(k.getAttribute("aria-controls"));
      if (p) p.hidden = true;
    });
  }
  knoepfe.forEach(function (k) {
    k.addEventListener("click", function () {
      var offen = k.getAttribute("aria-expanded") === "true";
      schliesseAlle(k);
      k.setAttribute("aria-expanded", offen ? "false" : "true");
      var p = document.getElementById(k.getAttribute("aria-controls"));
      if (p) p.hidden = offen;
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    var offen = document.querySelector('button.hauptnav__knopf[aria-expanded="true"]');
    if (offen) { schliesseAlle(); offen.focus(); }
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".hauptnav")) schliesseAlle();
  });

  /* ---------------- Menü auf kleinen Bildschirmen ---------------- */
  var kopf = document.getElementById("kopf");
  var menue = document.querySelector(".menuekopf");
  if (menue && kopf) {
    menue.addEventListener("click", function () {
      var offen = menue.getAttribute("aria-expanded") === "true";
      menue.setAttribute("aria-expanded", offen ? "false" : "true");
      kopf.classList.toggle("kopf--offen", !offen);
      var text = menue.querySelector(".menuekopf__text");
      if (text) text.textContent = offen ? (en ? "Menu" : "Menü") : (en ? "Close" : "Schließen");
    });
  }

  /* ---------------- Schriftgröße und Kontrast ---------------- */
  var stufe = parseInt(lies("nnl-schrift") || "0", 10) || 0;
  function setzeSchrift(s) {
    stufe = Math.max(-1, Math.min(3, s));
    if (stufe === 0) { doc.removeAttribute("data-schrift"); schreib("nnl-schrift", null); }
    else { doc.setAttribute("data-schrift", String(stufe)); schreib("nnl-schrift", String(stufe)); }
    melde((en ? "Text size: " : "Schriftgröße: ") + [87.5, 100, 112.5, 125, 150][stufe + 1] + " %");
  }
  var kontrastKnopf = document.querySelector('[data-aktion="kontrast"]');
  function setzeKontrast(an) {
    if (an) { doc.setAttribute("data-kontrast", "hoch"); schreib("nnl-kontrast", "hoch"); }
    else { doc.removeAttribute("data-kontrast"); schreib("nnl-kontrast", null); }
    if (kontrastKnopf) kontrastKnopf.setAttribute("aria-pressed", an ? "true" : "false");
  }
  if (kontrastKnopf) kontrastKnopf.setAttribute("aria-pressed", doc.getAttribute("data-kontrast") === "hoch" ? "true" : "false");

  /* Ansagen für Screenreader */
  var ansage = document.createElement("div");
  ansage.className = "visually-hidden";
  ansage.setAttribute("aria-live", "polite");
  document.body.appendChild(ansage);
  function melde(t) { ansage.textContent = ""; window.setTimeout(function () { ansage.textContent = t; }, 60); }

  /* ---------------- Vorlesen (Web Speech API) ---------------- */
  var vorlesen = document.querySelector('[data-aktion="vorlesen"]');
  var synth = window.speechSynthesis;
  if (vorlesen && !synth) vorlesen.hidden = true;
  function stopVorlesen() { if (synth) synth.cancel(); if (vorlesen) vorlesen.setAttribute("aria-pressed", "false"); }
  function startVorlesen() {
    var main = document.getElementById("inhalt");
    if (!main || !synth) return;
    var text = main.innerText.replace(/\s+\n/g, "\n");
    var saetze = text.match(/[^.!?\n]+[.!?]*/g) || [];
    synth.cancel();
    saetze.forEach(function (s, i) {
      s = s.trim();
      if (!s) return;
      var u = new SpeechSynthesisUtterance(s);
      u.lang = en ? "en-GB" : "de-DE";
      u.rate = 0.95;
      if (i === saetze.length - 1) u.onend = function () { vorlesen.setAttribute("aria-pressed", "false"); };
      synth.speak(u);
    });
    vorlesen.setAttribute("aria-pressed", "true");
  }

  document.addEventListener("click", function (e) {
    var w = e.target.closest("[data-aktion]");
    if (!w) return;
    var a = w.getAttribute("data-aktion");
    if (a === "groesser") setzeSchrift(stufe + 1);
    else if (a === "kleiner") setzeSchrift(stufe - 1);
    else if (a === "kontrast") setzeKontrast(doc.getAttribute("data-kontrast") !== "hoch");
    else if (a === "vorlesen") { if (w.getAttribute("aria-pressed") === "true") stopVorlesen(); else startVorlesen(); }
  });

  /* ---------------- Anzeigezeitraum (Anzeigen ab / Anzeigen bis) ---------------- */
  var heute = new Date();
  document.querySelectorAll("[data-anzeigen-ab], [data-anzeigen-bis]").forEach(function (el) {
    var ab = el.getAttribute("data-anzeigen-ab");
    var bis = el.getAttribute("data-anzeigen-bis");
    var sichtbar = (!ab || new Date(ab + "T00:00:00") <= heute) && (!bis || new Date(bis + "T23:59:59") >= heute);
    if (!sichtbar) el.hidden = true;
  });

  /* ---------------- Hinweis vor externen Seiten ---------------- */
  var dialog = document.getElementById("extern-dialog");
  document.addEventListener("click", function (e) {
    var link = e.target.closest("a[data-extern]");
    if (!link || !dialog || typeof dialog.showModal !== "function") return;
    e.preventDefault();
    var demo = link.hasAttribute("data-extern-demo");
    var weiter = document.getElementById("extern-weiter");
    document.getElementById("extern-ziel").textContent = demo ? "" : link.href;
    document.getElementById("extern-demo").hidden = !demo;
    weiter.hidden = demo;
    if (!demo) weiter.href = link.href;
    dialog.showModal();
  });
  if (dialog) {
    dialog.addEventListener("click", function (e) {
      if (e.target.closest("[data-dialog-schliessen]") || e.target === dialog) dialog.close();
      if (e.target.closest("#extern-weiter")) dialog.close();
    });
  }

  /* ---------------- Zwei-Klick-Video ---------------- */
  document.querySelectorAll("[data-video-laden]").forEach(function (k) {
    k.addEventListener("click", function () {
      var huelle = k.closest(".videohuelle");
      huelle.innerHTML = "<p>" + (en ? "In the demonstrator there is no video yet. In the project, the video would now be loaded from the platform." : "Im Demonstrator ist noch kein Video hinterlegt. Im Projekt würde das Video erst jetzt von der Plattform geladen.") + "</p>";
      huelle.setAttribute("tabindex", "-1");
      huelle.focus();
    });
  });

  /* ---------------- Formulare ohne Versand ---------------- */
  document.querySelectorAll("form[data-demo-formular]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!f.checkValidity()) { f.reportValidity(); return; }
      var ok = f.querySelector(".formular__ok");
      if (ok) { ok.hidden = false; ok.setAttribute("tabindex", "-1"); ok.focus(); }
    });
  });
})();
