-- Planning social SELY — schéma D1.
-- Un post = une ligne. « portee » distingue ce qui relève de l'app de ce qui
-- relève de la marque personnelle de Bristan, puisque les deux passent par les
-- mêmes comptes sociaux.

CREATE TABLE IF NOT EXISTS posts (
  id      TEXT PRIMARY KEY,
  reseau  TEXT NOT NULL,                     -- x | linkedin | facebook | reddit
  portee  TEXT NOT NULL DEFAULT 'sely',      -- sely | perso
  titre   TEXT DEFAULT '',                   -- Reddit uniquement
  texte   TEXT DEFAULT '',
  cible   TEXT DEFAULT '',                   -- subreddit, nom du groupe…
  date    TEXT DEFAULT '',                   -- AAAA-MM-JJ
  heure   TEXT DEFAULT '',                   -- HH:MM
  etat    TEXT DEFAULT 'brouillon',          -- brouillon | pret | publie
  images  TEXT DEFAULT '[]',                 -- tableau JSON de chemins
  cree    TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date, heure);
CREATE INDEX IF NOT EXISTS idx_posts_portee ON posts(portee);
