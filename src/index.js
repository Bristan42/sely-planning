// Planning social SELY — Worker unique.
//
// Sert l'interface statique et les trois routes de données. On passe par un
// Worker plutôt qu'un projet Pages parce que Cloudflare refuse la création de
// projets Pages tant que l'adresse du compte n'est pas vérifiée.

const EXTENSIONS = {
  "image/jpeg": "jpg", "image/png": "png",
  "image/gif": "gif", "image/webp": "webp",
};
const TYPES = { jpg: "image/jpeg", png: "image/png",
                gif: "image/gif", webp: "image/webp" };
const POIDS_MAX = 20 * 1024 * 1024;

const CHAMPS = ["id", "reseau", "portee", "titre", "texte", "cible",
                "date", "heure", "etat", "images", "cree"];

const json = (donnees, code = 200) =>
  new Response(JSON.stringify(donnees), {
    status: code,
    headers: { "Content-Type": "application/json; charset=utf-8",
               "Cache-Control": "no-store" },
  });

async function lirePosts(env) {
  const { results } = await env.DB
    .prepare("SELECT * FROM posts ORDER BY date, heure").all();
  return json(results.map((r) => ({
    ...r, images: r.images ? JSON.parse(r.images) : [],
  })));
}

async function ecrirePosts(request, env) {
  let posts;
  try { posts = await request.json(); }
  catch { return json({ erreur: "json invalide" }, 400); }
  if (!Array.isArray(posts)) return json({ erreur: "liste attendue" }, 400);
  if (posts.length > 2000) return json({ erreur: "trop de posts" }, 413);

  const insert = env.DB.prepare(
    `INSERT INTO posts (${CHAMPS.join(",")})
     VALUES (${CHAMPS.map(() => "?").join(",")})`);

  const lots = [env.DB.prepare("DELETE FROM posts")];
  for (const p of posts) {
    lots.push(insert.bind(
      String(p.id || ""), p.reseau || "", p.portee || "sely",
      p.titre || "", p.texte || "", p.cible || "",
      p.date || "", p.heure || "", p.etat || "brouillon",
      JSON.stringify(Array.isArray(p.images) ? p.images
                     : (p.image ? [p.image] : [])),
      p.cree || ""));
  }
  // batch() est atomique : jamais de planning à moitié effacé.
  await env.DB.batch(lots);
  return json({ enregistres: posts.length });
}

async function deposerImage(request, env) {
  const type = (request.headers.get("Content-Type") || "").split(";")[0].trim();
  const ext = EXTENSIONS[type];
  if (!ext) return json({ erreur: "format non accepté" }, 415);

  const octets = await request.arrayBuffer();
  if (octets.byteLength > POIDS_MAX)
    return json({ erreur: "image trop lourde (20 Mo max)" }, 413);

  const base = (request.headers.get("X-Nom") || "image")
    .replace(/[^a-zA-Z0-9._-]/g, "-").replace(/\.[^.]*$/, "").slice(0, 40) || "image";
  const cle = `${base}-${Date.now()}-${crypto.randomUUID().slice(0, 8)}.${ext}`;

  await env.MEDIAS.put(cle, octets, { metadata: { type } });
  return json({ chemin: `/images/${cle}` });
}

async function servirImage(cle, env) {
  const { value, metadata } = await env.MEDIAS.getWithMetadata(cle, "arrayBuffer");
  if (!value) return new Response("introuvable", { status: 404 });
  const ext = cle.split(".").pop().toLowerCase();
  return new Response(value, {
    headers: {
      "Content-Type": (metadata && metadata.type) || TYPES[ext] || "application/octet-stream",
      // La clé porte un horodatage : le contenu ne change jamais pour une clé
      // donnée, on peut cacher sans limite.
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const chemin = url.pathname;

    if (chemin === "/api/posts") {
      if (request.method === "GET") return lirePosts(env);
      if (request.method === "POST") return ecrirePosts(request, env);
      return json({ erreur: "méthode non gérée" }, 405);
    }
    if (chemin === "/api/image" && request.method === "POST")
      return deposerImage(request, env);
    if (chemin.startsWith("/images/"))
      return servirImage(decodeURIComponent(chemin.slice("/images/".length)), env);

    // Tout le reste : l'interface statique.
    return env.ASSETS.fetch(request);
  },
};
