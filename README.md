# Planning social SELY

En ligne : https://sely-planning.sely-app.workers.dev (accès libre, sans mot de passe)

Worker Cloudflare unique (compte SELY) : interface statique + routes de données.

- `GET  /api/posts` — liste complète
- `POST /api/posts` — remplace la liste (écriture atomique D1)
- `POST /api/image` — dépose une image (octets bruts, type dans Content-Type)
- `GET  /images/<clé>` — ressert l'image

Stockage : base D1 `sely-planning` (posts, schéma dans `schema.sql`), namespace KV `MEDIAS` (images).

## Déployer

    npx wrangler@4 deploy

## Local

    python3 serveur.py   # http://localhost:8790 — utilise posts.json et public/images/, pas D1
