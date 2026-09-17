#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atelier social — serveur local.

Sert l'interface et tient le fichier de posts. Rien ne sort d'ici : aucune
publication automatique, aucun appel réseau. Ce serveur ne parle qu'à ton
navigateur, sur 127.0.0.1.

    python3 serveur.py              # http://localhost:8790
    python3 serveur.py --port 9100
"""

import argparse
import json
import os
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DOSSIER = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(DOSSIER, "public")
IMAGES = os.path.join(PUBLIC, "images")
POSTS = os.path.join(DOSSIER, "posts.json")

EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png",
              "image/gif": ".gif", "image/webp": ".webp"}


def charger():
    if not os.path.exists(POSTS):
        return []
    with open(POSTS, encoding="utf-8") as fh:
        return json.load(fh)


def sauver(posts):
    tmp = POSTS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(posts, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, POSTS)


class Poste(BaseHTTPRequestHandler):

    def _rep(self, code, corps, ctype="application/json; charset=utf-8"):
        d = corps.encode("utf-8") if isinstance(corps, str) else corps
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(d)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(d)

    def do_GET(self):
        chemin = self.path.split("?")[0]
        if chemin == "/api/posts":
            return self._rep(200, json.dumps(charger(), ensure_ascii=False))
        fichier = "index.html" if chemin in ("/", "") else chemin.lstrip("/")
        cible = os.path.normpath(os.path.join(PUBLIC, fichier))
        if not cible.startswith(PUBLIC) or not os.path.isfile(cible):
            return self._rep(404, '{"erreur":"introuvable"}')
        types = {".html": "text/html; charset=utf-8",
                 ".css": "text/css; charset=utf-8",
                 ".js": "text/javascript; charset=utf-8",
                 ".jpg": "image/jpeg", ".png": "image/png",
                 ".gif": "image/gif", ".webp": "image/webp"}
        ext = os.path.splitext(cible)[1]
        with open(cible, "rb") as fh:
            self._rep(200, fh.read(), types.get(ext, "application/octet-stream"))

    def do_POST(self):
        chemin = self.path.split("?")[0]
        if chemin == "/api/image":
            return self._image()
        if chemin != "/api/posts":
            return self._rep(404, '{"erreur":"introuvable"}')
        taille = int(self.headers.get("Content-Length") or 0)
        if taille > 5_000_000:
            return self._rep(413, '{"erreur":"trop gros"}')
        try:
            corps = json.loads(self.rfile.read(taille).decode("utf-8") or "[]")
        except ValueError:
            return self._rep(400, '{"erreur":"json invalide"}')
        if not isinstance(corps, list):
            return self._rep(400, '{"erreur":"liste attendue"}')
        sauver(corps)
        self._rep(200, json.dumps({"enregistres": len(corps)}))

    def _image(self):
        """Reçoit une image brute et l'écrit dans public/images/.

        Pas de multipart : le navigateur envoie les octets tels quels, le type
        arrive dans Content-Type et le nom d'origine dans X-Nom. Plus simple à
        lire, et rien à parser.
        """
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if ctype not in EXTENSIONS:
            return self._rep(415, '{"erreur":"format non accepté"}')
        taille = int(self.headers.get("Content-Length") or 0)
        if taille > 15_000_000:
            return self._rep(413, '{"erreur":"image trop lourde (15 Mo max)"}')

        os.makedirs(IMAGES, exist_ok=True)
        base = re.sub(r"[^a-zA-Z0-9._-]", "-",
                      (self.headers.get("X-Nom") or "image"))[:40]
        base = os.path.splitext(base)[0] or "image"
        nom = "%s-%d%s" % (base, int(time.time()), EXTENSIONS[ctype])
        with open(os.path.join(IMAGES, nom), "wb") as fh:
            fh.write(self.rfile.read(taille))
        self._rep(200, json.dumps({"chemin": "/images/" + nom}))

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser(description="Atelier social (local)")
    ap.add_argument("--port", type=int, default=8790)
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Poste)
    print("Atelier social : http://localhost:%d" % args.port)
    print("Ctrl+C pour arrêter.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêté.")


if __name__ == "__main__":
    main()
