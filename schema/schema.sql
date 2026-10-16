-- Schema for the working database. The CSVs in data/ are canonical; this
-- file defines table and column order for both load and export.
-- Every table has a stable text id. Columns ending in _id refer to another table.
-- Order matters: referenced tables come before the tables that refer to them.

-- Provenance
CREATE TABLE source (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  citation TEXT,
  url TEXT,
  license TEXT,
  allows_bulk_reuse TEXT CHECK (allows_bulk_reuse IN ('yes','no','unknown')),
  notes TEXT
);
CREATE TABLE contributor (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  github TEXT
);

-- Reference
CREATE TABLE language (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  iso_code TEXT,
  parent_id TEXT REFERENCES language(id),  -- immediate parent: a family, or the language a variety belongs to
  period TEXT,
  notes TEXT
);
CREATE TABLE script (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  notes TEXT
);
CREATE TABLE semantic_field (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  notes TEXT
);

-- Script evidence
CREATE TABLE sign (
  id TEXT PRIMARY KEY,
  script_id TEXT NOT NULL REFERENCES script(id),
  label TEXT NOT NULL,          -- conventional sign number or name, e.g. AB01
  unicode TEXT,                 -- the character, if encoded
  notes TEXT
);
CREATE TABLE sign_value (
  id TEXT PRIMARY KEY,
  sign_id TEXT NOT NULL REFERENCES sign(id),
  value TEXT NOT NULL,          -- proposed sound, e.g. da
  certainty TEXT CHECK (certainty IN ('certain','assumed','proposed','disputed')),
  source_id TEXT NOT NULL REFERENCES source(id),
  page_ref TEXT
);
CREATE TABLE word_form (
  id TEXT PRIMARY KEY,
  script_id TEXT NOT NULL REFERENCES script(id),
  notes TEXT
);
CREATE TABLE word_form_sign (
  id TEXT PRIMARY KEY,
  word_form_id TEXT NOT NULL REFERENCES word_form(id),
  position INTEGER NOT NULL,
  sign_id TEXT NOT NULL REFERENCES sign(id)
);
CREATE TABLE inscription (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,           -- standard designation, e.g. HT 13
  site TEXT,
  script_id TEXT NOT NULL REFERENCES script(id),
  source_id TEXT NOT NULL REFERENCES source(id),
  page_ref TEXT,
  notes TEXT
);
CREATE TABLE token (
  id TEXT PRIMARY KEY,
  inscription_id TEXT NOT NULL REFERENCES inscription(id),
  line INTEGER NOT NULL,
  position INTEGER NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('word','ideogram','number','other')),
  word_form_id TEXT REFERENCES word_form(id),
  notes TEXT
);
CREATE TABLE token_sign (
  id TEXT PRIMARY KEY,
  token_id TEXT NOT NULL REFERENCES token(id),
  position INTEGER NOT NULL,
  sign_id TEXT NOT NULL REFERENCES sign(id),
  certainty TEXT CHECK (certainty IN ('clear','damaged','uncertain','restored'))
);

-- Words and claims about them
CREATE TABLE lexeme (
  id TEXT PRIMARY KEY,
  language_id TEXT NOT NULL REFERENCES language(id),
  form TEXT NOT NULL,
  pos TEXT,                     -- part of speech, e.g. noun, verb
  word_form_id TEXT REFERENCES word_form(id),
  obtained TEXT NOT NULL CHECK (obtained IN ('copied','extracted','derived','contributed')),
  source_id TEXT NOT NULL REFERENCES source(id),
  page_ref TEXT,
  contributor_id TEXT REFERENCES contributor(id)
);
CREATE TABLE pronunciation (
  id TEXT PRIMARY KEY,
  lexeme_id TEXT NOT NULL REFERENCES lexeme(id),
  ipa TEXT NOT NULL,
  variety TEXT,                 -- which pronunciation system, e.g. Classical, Ecclesiastical
  source_id TEXT NOT NULL REFERENCES source(id),
  page_ref TEXT
);
CREATE TABLE meaning (
  id TEXT PRIMARY KEY,
  lexeme_id TEXT NOT NULL REFERENCES lexeme(id),
  gloss TEXT NOT NULL,          -- short; may be taken from the source, under its license
  semantic_field_id TEXT REFERENCES semantic_field(id),
  status TEXT NOT NULL CHECK (status IN ('attested','proposed','disputed','rejected')),
  source_id TEXT NOT NULL REFERENCES source(id),
  page_ref TEXT
);
CREATE TABLE etymology (
  id TEXT PRIMARY KEY,
  lexeme_id TEXT NOT NULL REFERENCES lexeme(id),
  relation TEXT NOT NULL,       -- free text, e.g. inherited, borrowed, cognate, calque
  source_lexeme_id TEXT REFERENCES lexeme(id),
  source_language_id TEXT REFERENCES language(id),
  source_form TEXT,             -- the source word as text, when it has no lexeme row
  source_id TEXT NOT NULL REFERENCES source(id),
  page_ref TEXT,
  notes TEXT,
  CHECK (source_lexeme_id IS NOT NULL OR source_language_id IS NOT NULL)
);
