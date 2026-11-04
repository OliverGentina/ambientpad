// Offline-Speicher für AmbientPad Live.
// Bei jeder neuen Version VERSION erhöhen.
const VERSION = "3.0.1";
const CACHE = "ambientpad-" + VERSION;
const PADCACHE = "ambientpad-pads-v1";   // Standard-Pads: bleiben über App-Updates hinweg erhalten
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png", "anleitung.html",
  "anleitung/anordnen.webp", "anleitung/auswahl.webp", "anleitung/ebenen.webp", "anleitung/ebenen_haupt.webp", "anleitung/ebenen_menu.webp", "anleitung/einstellungen.webp", "anleitung/ipad.webp", "anleitung/klick_einstellungen.webp", "anleitung/klick_haupt.webp", "anleitung/kopfzeile.webp", "anleitung/onedrive.webp", "anleitung/pco_laden.webp", "anleitung/pco_liste.webp", "anleitung/pco_menu.webp", "anleitung/pco_seite.webp", "anleitung/pco_setlist.webp", "anleitung/pedal.webp", "anleitung/pedal2.webp", "anleitung/spielen.webp", "anleitung/start.webp", "anleitung/symbole.webp", "anleitung/team.webp", "anleitung/tempo.webp", "anleitung/zuweisen.webp"];

self.addEventListener("install", e => {
  // cache:"reload" umgeht den Browser-Zwischenspeicher → wirklich die neuen Dateien
  e.waitUntil(caches.open(CACHE)
    .then(c => c.addAll(FILES.map(u => new Request(u, { cache: "reload" }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith("ambientpad-") && k !== CACHE && k !== PADCACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const withTimeout = (p, ms) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms))]);

self.addEventListener("fetch", e => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;

  // Pads: nur aus dem Cache bzw. einmal aus dem Netz – nie bei jedem Start neu laden
  if (url.pathname.includes("/pads/")) {
    e.respondWith(caches.open(PADCACHE).then(async c => {
      const hit = await c.match(req, { ignoreSearch: true });
      if (hit) return hit;
      const res = await fetch(req);
      if (res && res.ok) c.put(req, res.clone());
      return res;
    }));
    return;
  }

  // Die App selbst (HTML): zuerst aus dem Netz (max. 4 s), sonst offline aus dem Speicher
  // → Updates sind beim nächsten Start sofort da.
  // Weitere Seiten (Anleitung) und Bilder der Anleitung: ebenso zuerst aus dem Netz, offline aus dem Speicher
  const isGuide = url.pathname.endsWith("/anleitung.html") || url.pathname.includes("/anleitung/");
  if (isGuide) {
    e.respondWith((async () => {
      const c = await caches.open(CACHE);
      try {
        const res = await withTimeout(fetch(req, { cache: "no-store" }), 4000);
        if (res && res.ok) { c.put(req, res.clone()); return res; }
        throw new Error("HTTP " + (res && res.status));
      } catch (err) {
        return (await c.match(req, { ignoreSearch: true })) || Response.error();
      }
    })());
    return;
  }
  if (req.mode === "navigate" || url.pathname.endsWith("/") || url.pathname.endsWith("/index.html")) {
    e.respondWith((async () => {
      const c = await caches.open(CACHE);
      try {
        const res = await withTimeout(fetch(req, { cache: "no-store" }), 4000);
        if (res && res.ok) { c.put("index.html", res.clone()); return res; }
        throw new Error("HTTP " + (res && res.status));
      } catch (err) {
        return (await c.match("index.html")) || (await c.match("./")) || Response.error();
      }
    })());
    return;
  }

  // Übrige Dateien (Symbole, Manifest): aus dem Speicher, im Hintergrund aktualisieren
  e.respondWith(caches.open(CACHE).then(async c => {
    const cached = await c.match(req, { ignoreSearch: true });
    const network = fetch(req).then(res => { if (res && res.ok) c.put(req, res.clone()); return res; }).catch(() => cached);
    return cached || network;
  }));
});
