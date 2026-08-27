# LogCenter Download App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Flask app with Login + Download screens that lets a user paste a MongoDB aggregation pipeline (Compass/shell syntax), apply a custom timestamp datepicker, run it against a fixed MongoDB Atlas collection, preview the results, favorite pipelines to static JSON files, and download results as CSV/Excel/JSON.

**Architecture:** Server-rendered Flask app (Jinja2 templates + vanilla JS, no build step). Visual style ports the DreamBricks design system tokens (`design_system/tokens/*.css`, logos) into plain CSS classes. A lenient parser (`services/pipeline_parser.py`) converts Compass/shell-style pipeline text into a real PyMongo pipeline via `bson.json_util`. Favorites are stored as individual JSON files on disk (`favorites/`).

**Tech Stack:** Python 3, Flask, PyMongo, python-dotenv, openpyxl, pytest.

---

## Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `config.py`
- Create: `services/__init__.py`
- Create: `favorites/.gitkeep`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `requirements.txt`**

```
Flask==3.0.3
pymongo==4.8.0
dnspython==2.6.1
python-dotenv==1.0.1
openpyxl==3.1.5
pytest==8.3.2
```

- [ ] **Step 2: Create `.env.example`**

```
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net
DB_NAME=logcenter
COLLECTION_NAME=events
APP_USERNAME=admin
APP_PASSWORD=change-me
SECRET_KEY=change-me-too
```

- [ ] **Step 3: Create `.gitignore`**

```
.env
__pycache__/
*.pyc
.venv/
venv/
favorites/*.json
```

- [ ] **Step 4: Create `pytest.ini`** (so `tests/` can import the `services` package without install)

```
[pytest]
pythonpath = .
```

- [ ] **Step 5: Create `config.py`**

```python
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

MONGODB_URI = os.environ.get("MONGODB_URI", "")
DB_NAME = os.environ.get("DB_NAME", "")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "")

APP_USERNAME = os.environ.get("APP_USERNAME", "")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")

FAVORITES_DIR = BASE_DIR / "favorites"
```

- [ ] **Step 6: Create empty package/marker files**

```bash
mkdir -p services templates static/css/tokens static/js static/img favorites tests
touch services/__init__.py tests/__init__.py favorites/.gitkeep
```

- [ ] **Step 7: Create a local `.env` from the example (not committed) and install dependencies**

```bash
cp .env.example .env
python -m venv .venv
```

On Windows (git bash), activate with:

```bash
source .venv/Scripts/activate
pip install -r requirements.txt
```

Expected: dependencies install without errors.

- [ ] **Step 8: Commit**

```bash
git add requirements.txt .env.example .gitignore pytest.ini config.py services/__init__.py tests/__init__.py favorites/.gitkeep
git commit -m "Scaffold Flask project structure and config"
```

---

## Task 2: Design tokens & base stylesheet

**Files:**
- Create: `static/css/tokens/fonts.css` (copied)
- Create: `static/css/tokens/colors.css` (copied)
- Create: `static/css/tokens/typography.css` (copied)
- Create: `static/css/tokens/spacing.css` (copied)
- Create: `static/img/dreambricks-horizontal-onlight.svg` (copied)
- Create: `static/img/dreambricks-mark-blue.svg` (copied)
- Create: `static/css/app.css`

- [ ] **Step 1: Copy design system tokens and logo assets**

```bash
cp design_system/tokens/fonts.css static/css/tokens/fonts.css
cp design_system/tokens/colors.css static/css/tokens/colors.css
cp design_system/tokens/typography.css static/css/tokens/typography.css
cp design_system/tokens/spacing.css static/css/tokens/spacing.css
cp design_system/assets/logos/dreambricks-horizontal-onlight.svg static/img/dreambricks-horizontal-onlight.svg
cp design_system/assets/logos/dreambricks-mark-blue.svg static/img/dreambricks-mark-blue.svg
```

- [ ] **Step 2: Create `static/css/app.css`**

```css
* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: var(--font-body);
  background: var(--surface-page);
  color: var(--text-primary);
}

.card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-body);
  font-weight: var(--weight-semibold);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  height: 40px;
  padding: 0 var(--space-4);
  font-size: var(--text-base);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-standard), transform var(--duration-fast) var(--ease-standard);
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn:active:not(:disabled) { transform: scale(0.98); }

.btn-sm { height: 32px; padding: 0 var(--space-3); font-size: var(--text-sm); }
.btn-lg { height: 48px; padding: 0 var(--space-6); font-size: var(--text-md); }

.btn-primary { background: var(--db-blue-500); color: var(--text-on-brand); }
.btn-primary:hover:not(:disabled) { background: var(--db-blue-600); }

.btn-secondary { background: var(--surface-card); color: var(--text-primary); border-color: var(--border-default); }
.btn-secondary:hover:not(:disabled) { background: var(--db-slate-50); }

.btn-ghost { background: transparent; color: var(--text-primary); }
.btn-ghost:hover:not(:disabled) { background: var(--db-slate-50); }

.field { display: flex; flex-direction: column; gap: 6px; font-family: var(--font-body); }
.field-label { font-size: var(--text-sm); font-weight: var(--weight-medium); color: var(--text-primary); }

.input {
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 0 var(--space-3);
  height: 40px;
  font-size: var(--text-base);
  color: var(--text-primary);
  background: var(--surface-card);
  font-family: inherit;
  width: 100%;
}
.input:focus { outline: none; border-color: var(--border-brand); box-shadow: var(--shadow-focus); }

.form-error { color: var(--db-danger-500); font-size: var(--text-sm); margin: 0; }

.tag {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--space-3);
  border-radius: var(--radius-pill);
  background: var(--db-blue-50);
  color: var(--text-brand);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
}

/* Auth screen */
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
}
.auth-card { width: 100%; max-width: 380px; display: flex; flex-direction: column; gap: var(--space-4); align-items: center; text-align: center; }
.auth-logo { height: 32px; }
.auth-title { font-size: var(--text-xl); font-weight: var(--weight-bold); margin: 0; }
.auth-subtitle { color: var(--text-secondary); font-size: var(--text-sm); margin: 0; }
.auth-form { width: 100%; display: flex; flex-direction: column; gap: var(--space-4); text-align: left; }

/* App shell */
.app-shell { min-height: 100vh; display: flex; flex-direction: column; }
.app-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-6);
  background: var(--surface-card);
  border-bottom: 1px solid var(--border-subtle);
}
.app-logo { height: 24px; }
.app-header-title { font-size: var(--text-md); font-weight: var(--weight-semibold); margin: 0; flex: 1; }

.app-main {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: var(--space-6);
  padding: var(--space-6);
  align-items: start;
}
@media (max-width: 900px) {
  .app-main { grid-template-columns: 1fr; }
}

.editor-column { display: flex; flex-direction: column; gap: var(--space-6); }

.datepicker-card { display: flex; flex-direction: column; gap: var(--space-4); }
.datepicker-toggle { display: flex; gap: var(--space-2); }
.datepicker-fields { display: flex; align-items: end; gap: var(--space-4); flex-wrap: wrap; }
.datepicker-fields .field { width: 180px; }

.editor-card { display: flex; flex-direction: column; gap: var(--space-3); }
.pipeline-editor {
  width: 100%;
  min-height: 260px;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  resize: vertical;
}
.pipeline-editor:focus { outline: none; border-color: var(--border-brand); box-shadow: var(--shadow-focus); }
.editor-actions { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; }
.download-group { display: inline-flex; gap: var(--space-2); margin-left: auto; }

.preview-card { display: flex; flex-direction: column; gap: var(--space-4); }
.preview-header { display: flex; align-items: center; justify-content: space-between; }
.preview-title { font-size: var(--text-md); font-weight: var(--weight-semibold); margin: 0; }
.preview-table-wrap { overflow: auto; max-height: 480px; }
.empty-state { color: var(--text-tertiary); font-size: var(--text-sm); text-align: center; padding: var(--space-8) 0; margin: 0; }

.table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
.table th, .table td { text-align: left; padding: var(--space-2) var(--space-3); border-bottom: 1px solid var(--border-subtle); white-space: nowrap; }
.table th { background: var(--db-slate-50); font-weight: var(--weight-semibold); position: sticky; top: 0; }

.favorites-column { display: flex; flex-direction: column; gap: var(--space-6); }
.favorites-card { display: flex; flex-direction: column; gap: var(--space-4); }
.favorites-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-2); }
.favorite-item { display: flex; align-items: center; gap: var(--space-2); }
.favorite-load {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  cursor: pointer;
  text-align: left;
}
.favorite-load:hover { background: var(--db-slate-50); }
.favorite-name { font-size: var(--text-sm); font-weight: var(--weight-medium); }
.favorite-date { font-size: var(--text-xs); color: var(--text-tertiary); }
.favorite-delete {
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: var(--space-2);
  border-radius: var(--radius-sm);
}
.favorite-delete:hover { background: var(--db-danger-100); color: var(--db-danger-500); }

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: var(--surface-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
  z-index: 10;
}
.dialog { width: 100%; max-width: 400px; display: flex; flex-direction: column; gap: var(--space-4); }
.dialog-actions { display: flex; justify-content: flex-end; gap: var(--space-3); }
```

- [ ] **Step 3: Commit**

```bash
git add static/css static/img
git commit -m "Add DreamBricks tokens, logos, and app stylesheet"
```

---

## Task 3: Pipeline parser (TDD)

**Files:**
- Create: `services/pipeline_parser.py`
- Test: `tests/test_pipeline_parser.py`

- [ ] **Step 1: Write the failing tests — `tests/test_pipeline_parser.py`**

```python
import pytest

from services.pipeline_parser import PipelineParseError, parse
from bson import ObjectId


EXAMPLE_PIPELINE = '''
[
  {
    $match: {
      project_id: ObjectId("6a864051a4efbe696698bb61"),
      message: "retirada_registrada_no_cadastro",
      //timestamp: { $gt: "2026-08-10" }
      timestamp: {
        $regex: "^2026-08-23"
      }
    }
  },
  {
    $project: {
      _id: 0,
      horario: "$timestamp",
      email: "$data.email",
      userId: "$data.id",
      session: "$data.session_id",
      // productsPicked: "$data.products_picked",
      recall: {
        $ifNull: ["$data.recalled", false]
      }
    }
  },
  {
    $sort: {
      horario: 1
    }
  }
]
'''


def test_parses_example_pipeline_with_comments_and_objectid():
    stages = parse(EXAMPLE_PIPELINE)
    assert len(stages) == 3
    assert stages[0]["$match"]["project_id"] == ObjectId("6a864051a4efbe696698bb61")
    assert stages[0]["$match"]["message"] == "retirada_registrada_no_cadastro"
    assert stages[0]["$match"]["timestamp"] == {"$regex": "^2026-08-23"}
    assert "productsPicked" not in stages[1]["$project"]
    assert stages[2]["$sort"] == {"horario": 1}


def test_parses_isodate_range():
    text = '''[
      { $match: { timestamp: { $gte: ISODate("2026-08-23T00:00:00Z"), $lt: ISODate("2026-08-25T00:00:00Z") } } }
    ]'''
    stages = parse(text)
    clause = stages[0]["$match"]["timestamp"]
    assert clause["$gte"].strftime("%Y-%m-%d") == "2026-08-23"
    assert clause["$lt"].strftime("%Y-%m-%d") == "2026-08-25"


def test_parses_strict_json_pipeline():
    stages = parse('[{"$match": {"status": "ok"}}]')
    assert stages == [{"$match": {"status": "ok"}}]


def test_rejects_malformed_json():
    with pytest.raises(PipelineParseError):
        parse('[{ $match: { status: } }]')


def test_rejects_non_list_pipeline():
    with pytest.raises(PipelineParseError):
        parse('{ "$match": { "status": "ok" } }')


def test_rejects_out_stage():
    with pytest.raises(PipelineParseError):
        parse('[{ $match: { status: "ok" } }, { $out: "other_collection" }]')


def test_rejects_merge_stage():
    with pytest.raises(PipelineParseError):
        parse('[{ $merge: { into: "other_collection" } }]')


def test_rejects_empty_text():
    with pytest.raises(PipelineParseError):
        parse('   ')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_pipeline_parser.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'services.pipeline_parser'`

- [ ] **Step 3: Write `services/pipeline_parser.py`**

```python
import re

from bson import json_util

_OBJECT_ID_RE = re.compile(r'ObjectId\(\s*"([a-fA-F0-9]{24})"\s*\)')
_ISO_DATE_RE = re.compile(r'ISODate\(\s*"([^"]+)"\s*\)')
_UNQUOTED_KEY_RE = re.compile(r'([{,]\s*)([A-Za-z_$][A-Za-z0-9_$]*)(\s*:)')

FORBIDDEN_STAGES = {"$out", "$merge"}


class PipelineParseError(ValueError):
    pass


def _strip_comments(text):
    """Removes // line comments, respecting string literals."""
    result = []
    in_string = False
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        if in_string:
            result.append(ch)
            if ch == '\\' and i + 1 < length:
                result.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            result.append(ch)
            i += 1
            continue
        if ch == '/' and i + 1 < length and text[i + 1] == '/':
            while i < length and text[i] != '\n':
                i += 1
            continue
        result.append(ch)
        i += 1
    return ''.join(result)


def _quote_keys(text):
    return _UNQUOTED_KEY_RE.sub(r'\1"\2"\3', text)


def parse(raw_text):
    """Converts a Compass/shell-style aggregation pipeline (unquoted keys,
    ObjectId(...), ISODate(...), // comments) into a list of stage dicts
    usable with pymongo's Collection.aggregate()."""
    if not raw_text or not raw_text.strip():
        raise PipelineParseError("O pipeline está vazio.")

    text = _strip_comments(raw_text)
    text = _OBJECT_ID_RE.sub(r'{"$oid": "\1"}', text)
    text = _ISO_DATE_RE.sub(r'{"$date": "\1"}', text)
    text = _quote_keys(text)

    try:
        stages = json_util.loads(text)
    except Exception as exc:
        raise PipelineParseError(f"Pipeline com sintaxe inválida: {exc}") from exc

    if not isinstance(stages, list) or not all(isinstance(stage, dict) for stage in stages):
        raise PipelineParseError("O pipeline precisa ser uma lista de estágios (objetos).")

    for stage in stages:
        forbidden = FORBIDDEN_STAGES.intersection(stage.keys())
        if forbidden:
            raise PipelineParseError(
                f"Estágio {', '.join(sorted(forbidden))} não é permitido — esta ferramenta é somente leitura."
            )

    return stages
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_pipeline_parser.py -v`
Expected: PASS — 8 passed

- [ ] **Step 5: Commit**

```bash
git add services/pipeline_parser.py tests/test_pipeline_parser.py
git commit -m "Add lenient Compass/shell pipeline parser with tests"
```

---

## Task 4: MongoDB client service

**Files:**
- Create: `services/mongo_client.py`

- [ ] **Step 1: Create `services/mongo_client.py`**

```python
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import config

_client = None


class MongoConnectionError(RuntimeError):
    pass


def get_client():
    global _client
    if _client is None:
        if not config.MONGODB_URI:
            raise MongoConnectionError("MONGODB_URI não configurado.")
        _client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client


def run_aggregation(stages):
    try:
        client = get_client()
        collection = client[config.DB_NAME][config.COLLECTION_NAME]
        return list(collection.aggregate(stages))
    except PyMongoError as exc:
        raise MongoConnectionError(
            "Não foi possível conectar ao MongoDB Atlas. Verifique MONGODB_URI."
        ) from exc
```

- [ ] **Step 2: Sanity-check the module imports cleanly**

Run: `python -c "import services.mongo_client"`
Expected: no output, exit code 0

- [ ] **Step 3: Commit**

```bash
git add services/mongo_client.py
git commit -m "Add MongoDB Atlas client and run_aggregation service"
```

---

## Task 5: Export service

**Files:**
- Create: `services/export.py`

- [ ] **Step 1: Create `services/export.py`**

```python
import csv
import io

from bson import json_util
from openpyxl import Workbook


def _collect_columns(rows):
    columns = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def _cell_value(value):
    if isinstance(value, (dict, list)):
        return json_util.dumps(value, ensure_ascii=False)
    return value


def to_csv_bytes(rows):
    columns = _collect_columns(rows)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        writer.writerow({col: _cell_value(row.get(col, "")) for col in columns})
    return buffer.getvalue().encode("utf-8-sig")


def to_xlsx_bytes(rows):
    columns = _collect_columns(rows)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "resultado"
    sheet.append(columns)
    for row in rows:
        sheet.append([str(_cell_value(row.get(col, ""))) for col in columns])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def to_json_bytes(rows):
    return json_util.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")
```

- [ ] **Step 2: Sanity-check with a quick manual run**

Run:
```bash
python -c "from services.export import to_csv_bytes, to_xlsx_bytes, to_json_bytes; rows=[{'a':1,'b':'x'}]; print(to_csv_bytes(rows)); print(len(to_xlsx_bytes(rows))); print(to_json_bytes(rows))"
```
Expected: prints CSV bytes, an xlsx byte length > 0, and JSON bytes — no exceptions.

- [ ] **Step 3: Commit**

```bash
git add services/export.py
git commit -m "Add CSV/Excel/JSON export service"
```

---

## Task 6: Auth module

**Files:**
- Create: `auth.py`

- [ ] **Step 1: Create `auth.py`**

```python
import secrets
from functools import wraps

from flask import redirect, session, url_for

import config


def verify_credentials(username, password):
    valid_user = secrets.compare_digest(username or "", config.APP_USERNAME)
    valid_pass = secrets.compare_digest(password or "", config.APP_PASSWORD)
    return valid_user and valid_pass


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped
```

- [ ] **Step 2: Sanity-check the module imports cleanly**

Run: `python -c "import auth"`
Expected: no output, exit code 0

- [ ] **Step 3: Commit**

```bash
git add auth.py
git commit -m "Add single-user auth (env credentials, session-based)"
```

---

## Task 7: Favorites service

**Files:**
- Create: `services/favorites.py`

- [ ] **Step 1: Create `services/favorites.py`**

```python
import json
import re
import time
from pathlib import Path

import config

_SLUG_RE = re.compile(r'[^a-z0-9]+')


def _slugify(name):
    slug = _SLUG_RE.sub('-', name.strip().lower()).strip('-')
    return slug or "favorito"


def _ensure_dir():
    config.FAVORITES_DIR.mkdir(parents=True, exist_ok=True)


def _safe_path(filename):
    safe_name = Path(filename).name
    return config.FAVORITES_DIR / safe_name


def list_favorites():
    _ensure_dir()
    items = []
    for path in config.FAVORITES_DIR.glob("*.json"):
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        items.append({
            "filename": path.name,
            "name": data.get("name", path.stem),
            "created_at": data.get("created_at", ""),
        })
    items.sort(key=lambda item: item["created_at"], reverse=True)
    return items


def save_favorite(name, pipeline):
    _ensure_dir()
    created_at = time.strftime("%Y-%m-%dT%H:%M:%S")
    filename = f"{_slugify(name)}-{int(time.time() * 1000)}.json"
    path = config.FAVORITES_DIR / filename
    with path.open("w", encoding="utf-8") as fh:
        json.dump(
            {"name": name, "pipeline": pipeline, "created_at": created_at},
            fh,
            ensure_ascii=False,
            indent=2,
        )
    return {"filename": filename, "name": name, "created_at": created_at}


def load_favorite(filename):
    _ensure_dir()
    path = _safe_path(filename)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def delete_favorite(filename):
    _ensure_dir()
    path = _safe_path(filename)
    if path.exists():
        path.unlink()
        return True
    return False
```

- [ ] **Step 2: Sanity-check with a quick manual run**

Run:
```bash
python -c "
from services import favorites
fav = favorites.save_favorite('Teste', '[{\"\$match\": {}}]')
print(fav)
print(favorites.list_favorites())
print(favorites.load_favorite(fav['filename']))
print(favorites.delete_favorite(fav['filename']))
print(favorites.list_favorites())
"
```
Expected: prints the saved favorite dict, a one-item list, the loaded favorite, `True`, then an empty list — no exceptions.

- [ ] **Step 3: Commit**

```bash
git add services/favorites.py
git commit -m "Add favorites service (static JSON file storage)"
```

---

## Task 8: Flask app — page routes (login/logout/download)

**Files:**
- Create: `app.py`

- [ ] **Step 1: Create `app.py` with the app skeleton and page routes**

```python
from flask import Flask, redirect, render_template, request, session, url_for

import config
from auth import login_required, verify_credentials

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

EXAMPLE_PIPELINE = """[
  {
    $match: {
      project_id: ObjectId("000000000000000000000000"),
      message: "retirada_registrada_no_cadastro",
      timestamp: {
        $regex: "^2026-08-23"
      }
    }
  },
  {
    $project: {
      _id: 0,
      horario: "$timestamp",
      email: "$data.email",
      userId: "$data.id",
      session: "$data.session_id",
      recall: {
        $ifNull: ["$data.recalled", false]
      }
    }
  },
  {
    $sort: {
      horario: 1
    }
  }
]"""


@app.route("/", methods=["GET"])
def index():
    if session.get("logged_in"):
        return redirect(url_for("download_page"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if verify_credentials(username, password):
            session["logged_in"] = True
            return redirect(url_for("download_page"))
        error = "Usuário ou senha inválidos."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/download", methods=["GET"])
@login_required
def download_page():
    return render_template("download.html", example_pipeline=EXAMPLE_PIPELINE)


if __name__ == "__main__":
    app.run(debug=True)
```

- [ ] **Step 2: Sanity-check the app boots**

Run: `python -c "import app; print(sorted(r.rule for r in app.app.url_map.iter_rules()))"`
Expected: a list including `/`, `/login`, `/logout`, `/download`, `/static/<path:filename>` — no exceptions. (Templates don't exist yet, so `flask run` and visiting a page will 500 until Tasks 10–11 — that's expected at this point.)

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "Add Flask app skeleton with login/logout/download page routes"
```

---

## Task 9: Flask app — API routes (run, download, favorites)

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace the entire import block at the top of `app.py`**

`app.py` currently starts with these 4 lines (from Task 8):

```python
from flask import Flask, redirect, render_template, request, session, url_for

import config
from auth import login_required, verify_credentials
```

Replace that whole block with:

```python
import datetime

from bson import json_util
from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for

import config
from auth import login_required, verify_credentials
from services import favorites as favorites_service
from services.export import to_csv_bytes, to_json_bytes, to_xlsx_bytes
from services.mongo_client import MongoConnectionError, run_aggregation
from services.pipeline_parser import PipelineParseError, parse
```

The rest of the file (starting at `app = Flask(__name__)`) stays unchanged.

- [ ] **Step 2: Add column-extraction helpers below `EXAMPLE_PIPELINE`**

```python
def _extract_columns(rows):
    columns = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def _stringify_rows(rows, columns):
    stringified = []
    for row in rows:
        record = {}
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, (dict, list)):
                record[col] = json_util.dumps(value, ensure_ascii=False)
            else:
                record[col] = value
        stringified.append(record)
    return stringified
```

- [ ] **Step 3: Add the API routes at the end of `app.py`, before `if __name__ == "__main__":`**

```python
@app.route("/api/run", methods=["POST"])
@login_required
def api_run():
    payload = request.get_json(silent=True) or {}
    pipeline_text = payload.get("pipeline", "")
    try:
        stages = parse(pipeline_text)
        rows = run_aggregation(stages)
    except PipelineParseError as exc:
        return jsonify({"error": str(exc)}), 400
    except MongoConnectionError as exc:
        return jsonify({"error": str(exc)}), 502

    columns = _extract_columns(rows)
    return jsonify({
        "columns": columns,
        "rows": _stringify_rows(rows, columns),
        "count": len(rows),
    })


@app.route("/download/<fmt>", methods=["POST"])
@login_required
def download_file(fmt):
    payload = request.get_json(silent=True) or {}
    pipeline_text = payload.get("pipeline", "")
    try:
        stages = parse(pipeline_text)
        rows = run_aggregation(stages)
    except PipelineParseError as exc:
        return jsonify({"error": str(exc)}), 400
    except MongoConnectionError as exc:
        return jsonify({"error": str(exc)}), 502

    filename_base = f"logcenter_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if fmt == "csv":
        body = to_csv_bytes(rows)
        mimetype = "text/csv"
        filename = f"{filename_base}.csv"
    elif fmt == "xlsx":
        body = to_xlsx_bytes(rows)
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{filename_base}.xlsx"
    elif fmt == "json":
        body = to_json_bytes(rows)
        mimetype = "application/json"
        filename = f"{filename_base}.json"
    else:
        return jsonify({"error": "Formato inválido."}), 400

    return Response(
        body,
        mimetype=mimetype,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.route("/api/favorites", methods=["GET"])
@login_required
def api_list_favorites():
    return jsonify(favorites_service.list_favorites())


@app.route("/api/favorites", methods=["POST"])
@login_required
def api_save_favorite():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    pipeline = payload.get("pipeline", "")
    if not name:
        return jsonify({"error": "Informe um nome para o favorito."}), 400
    if not pipeline.strip():
        return jsonify({"error": "O pipeline está vazio."}), 400
    favorite = favorites_service.save_favorite(name, pipeline)
    return jsonify(favorite), 201


@app.route("/api/favorites/<path:filename>", methods=["GET"])
@login_required
def api_get_favorite(filename):
    favorite = favorites_service.load_favorite(filename)
    if favorite is None:
        return jsonify({"error": "Favorito não encontrado."}), 404
    return jsonify(favorite)


@app.route("/api/favorites/<path:filename>", methods=["DELETE"])
@login_required
def api_delete_favorite(filename):
    deleted = favorites_service.delete_favorite(filename)
    if not deleted:
        return jsonify({"error": "Favorito não encontrado."}), 404
    return jsonify({"deleted": True})
```

- [ ] **Step 4: Sanity-check the app still boots and lists the new routes**

Run: `python -c "import app; print(sorted(r.rule for r in app.app.url_map.iter_rules()))"`
Expected: list now also includes `/api/run`, `/download/<fmt>`, `/api/favorites`, `/api/favorites/<path:filename>` — no exceptions.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "Add API routes for running aggregations, downloads, and favorites"
```

---

## Task 10: Templates — base layout and login page

**Files:**
- Create: `templates/base.html`
- Create: `templates/login.html`

- [ ] **Step 1: Create `templates/base.html`**

```html
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}LogCenter Download{% endblock %}</title>
  <link rel="icon" href="{{ url_for('static', filename='img/dreambricks-mark-blue.svg') }}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/tokens/fonts.css') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/tokens/colors.css') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/tokens/typography.css') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/tokens/spacing.css') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/app.css') }}">
  <script src="https://unpkg.com/lucide@latest"></script>
  {% block head %}{% endblock %}
</head>
<body>
  {% block body %}{% endblock %}
  <script>
    if (window.lucide) { window.lucide.createIcons(); }
  </script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: Create `templates/login.html`**

```html
{% extends "base.html" %}
{% block title %}Entrar — LogCenter Download{% endblock %}
{% block body %}
<main class="auth-page">
  <div class="card auth-card">
    <img class="auth-logo" src="{{ url_for('static', filename='img/dreambricks-horizontal-onlight.svg') }}" alt="DreamBricks">
    <h1 class="auth-title">LogCenter Download</h1>
    <p class="auth-subtitle">Entre para rodar aggregations e baixar resultados.</p>
    <form method="post" class="auth-form">
      <label class="field">
        <span class="field-label">Usuário</span>
        <input class="input" type="text" name="username" autocomplete="username" required autofocus>
      </label>
      <label class="field">
        <span class="field-label">Senha</span>
        <input class="input" type="password" name="password" autocomplete="current-password" required>
      </label>
      {% if error %}
        <p class="form-error">{{ error }}</p>
      {% endif %}
      <button class="btn btn-primary btn-lg" type="submit" style="width: 100%;">Entrar</button>
    </form>
  </div>
</main>
{% endblock %}
```

- [ ] **Step 3: Manually verify the login page renders**

Run: `python -m flask --app app run --debug` (leave running), then in another shell:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/login
```

Expected: `200`. Stop the server with Ctrl+C when done.

- [ ] **Step 4: Commit**

```bash
git add templates/base.html templates/login.html
git commit -m "Add base layout and login page templates"
```

---

## Task 11: Template — download page

**Files:**
- Create: `templates/download.html`

- [ ] **Step 1: Create `templates/download.html`**

```html
{% extends "base.html" %}
{% block title %}Download — LogCenter{% endblock %}
{% block body %}
<div class="app-shell">
  <header class="app-header">
    <img class="app-logo" src="{{ url_for('static', filename='img/dreambricks-horizontal-onlight.svg') }}" alt="DreamBricks">
    <h1 class="app-header-title">LogCenter Download</h1>
    <a class="btn btn-ghost" href="{{ url_for('logout') }}"><i data-lucide="log-out"></i> Sair</a>
  </header>

  <main class="app-main">
    <section class="editor-column">
      <div class="card datepicker-card">
        <div class="datepicker-toggle">
          <button type="button" class="btn btn-secondary btn-sm" id="mode-single">Dia único</button>
          <button type="button" class="btn btn-ghost btn-sm" id="mode-range">Intervalo</button>
        </div>
        <div class="datepicker-fields">
          <label class="field">
            <span class="field-label" id="date-start-label">Data</span>
            <input class="input" type="date" id="date-start">
          </label>
          <label class="field" id="date-end-field" hidden>
            <span class="field-label">Até</span>
            <input class="input" type="date" id="date-end">
          </label>
          <button type="button" class="btn btn-primary btn-sm" id="apply-date">Aplicar data</button>
        </div>
        <p class="form-error" id="datepicker-error" hidden></p>
      </div>

      <div class="card editor-card">
        <label class="field-label" for="pipeline-editor">Aggregation pipeline</label>
        <textarea id="pipeline-editor" class="pipeline-editor" spellcheck="false">{{ example_pipeline }}</textarea>
        <p class="form-error" id="run-error" hidden></p>
        <div class="editor-actions">
          <button type="button" class="btn btn-primary" id="run-btn"><i data-lucide="play"></i> Executar</button>
          <button type="button" class="btn btn-secondary" id="favorite-btn"><i data-lucide="star"></i> Favoritar</button>
          <span class="download-group">
            <button type="button" class="btn btn-ghost" id="download-csv" disabled>CSV</button>
            <button type="button" class="btn btn-ghost" id="download-xlsx" disabled>Excel</button>
            <button type="button" class="btn btn-ghost" id="download-json" disabled>JSON</button>
          </span>
        </div>
      </div>

      <div class="card preview-card">
        <div class="preview-header">
          <h2 class="preview-title">Resultado</h2>
          <span class="tag" id="result-count">0 linhas</span>
        </div>
        <div class="preview-table-wrap" id="preview-table-wrap">
          <p class="empty-state">Rode uma aggregation para ver o resultado aqui.</p>
        </div>
      </div>
    </section>

    <aside class="favorites-column">
      <div class="card favorites-card">
        <h2 class="preview-title">Favoritos</h2>
        <ul class="favorites-list" id="favorites-list"></ul>
      </div>
    </aside>
  </main>
</div>

<div class="dialog-overlay" id="favorite-dialog-overlay" hidden>
  <div class="dialog card">
    <h2 class="preview-title">Favoritar aggregation</h2>
    <label class="field">
      <span class="field-label">Nome</span>
      <input class="input" type="text" id="favorite-name" placeholder="Ex: Retiradas do dia">
    </label>
    <p class="form-error" id="favorite-error" hidden></p>
    <div class="dialog-actions">
      <button type="button" class="btn btn-ghost" id="favorite-cancel">Cancelar</button>
      <button type="button" class="btn btn-primary" id="favorite-save">Salvar</button>
    </div>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
<script src="{{ url_for('static', filename='js/datepicker.js') }}"></script>
<script src="{{ url_for('static', filename='js/favorites.js') }}"></script>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add templates/download.html
git commit -m "Add download page template (editor, datepicker, preview, favorites, dialog)"
```

(This page depends on `static/js/app.js`, `datepicker.js`, `favorites.js` from Tasks 12–14 — it will show a broken layout until those exist, which is expected at this point.)

---

## Task 12: JS — run aggregation, preview table, downloads

**Files:**
- Create: `static/js/app.js`

- [ ] **Step 1: Create `static/js/app.js`**

```javascript
(function () {
  const editor = document.getElementById('pipeline-editor');
  const runBtn = document.getElementById('run-btn');
  const runError = document.getElementById('run-error');
  const tableWrap = document.getElementById('preview-table-wrap');
  const resultCount = document.getElementById('result-count');
  const downloadButtons = {
    csv: document.getElementById('download-csv'),
    xlsx: document.getElementById('download-xlsx'),
    json: document.getElementById('download-json'),
  };

  function setRunError(message) {
    if (message) {
      runError.textContent = message;
      runError.hidden = false;
    } else {
      runError.hidden = true;
    }
  }

  function setDownloadsEnabled(enabled) {
    Object.values(downloadButtons).forEach((btn) => { btn.disabled = !enabled; });
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function renderTable(columns, rows) {
    if (rows.length === 0) {
      tableWrap.innerHTML = '<p class="empty-state">Nenhum resultado encontrado.</p>';
      return;
    }
    const thead = `<thead><tr>${columns.map((c) => `<th>${escapeHtml(c)}</th>`).join('')}</tr></thead>`;
    const tbody = `<tbody>${rows.map((row) => `<tr>${columns.map((c) => `<td>${escapeHtml(row[c] ?? '')}</td>`).join('')}</tr>`).join('')}</tbody>`;
    tableWrap.innerHTML = `<table class="table">${thead}${tbody}</table>`;
  }

  async function runPipeline() {
    setRunError(null);
    setDownloadsEnabled(false);
    runBtn.disabled = true;
    try {
      const response = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pipeline: editor.value }),
      });
      const data = await response.json();
      if (!response.ok) {
        setRunError(data.error || 'Erro ao executar a aggregation.');
        resultCount.textContent = '0 linhas';
        tableWrap.innerHTML = '<p class="empty-state">Rode uma aggregation para ver o resultado aqui.</p>';
        return;
      }
      resultCount.textContent = `${data.count} linha${data.count === 1 ? '' : 's'}`;
      renderTable(data.columns, data.rows);
      setDownloadsEnabled(data.count > 0);
    } catch (err) {
      setRunError('Erro de rede ao executar a aggregation.');
    } finally {
      runBtn.disabled = false;
    }
  }

  async function downloadFormat(fmt) {
    setRunError(null);
    try {
      const response = await fetch(`/download/${fmt}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pipeline: editor.value }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setRunError(data.error || 'Erro ao gerar o arquivo.');
        return;
      }
      const blob = await response.blob();
      const disposition = response.headers.get('Content-Disposition') || '';
      const match = disposition.match(/filename="([^"]+)"/);
      const filename = match ? match[1] : `logcenter.${fmt}`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setRunError('Erro de rede ao baixar o arquivo.');
    }
  }

  runBtn.addEventListener('click', runPipeline);
  downloadButtons.csv.addEventListener('click', () => downloadFormat('csv'));
  downloadButtons.xlsx.addEventListener('click', () => downloadFormat('xlsx'));
  downloadButtons.json.addEventListener('click', () => downloadFormat('json'));

  window.LogCenter = {
    getPipelineText: () => editor.value,
    setPipelineText: (text) => { editor.value = text; },
  };
})();
```

- [ ] **Step 2: Commit**

```bash
git add static/js/app.js
git commit -m "Add app.js: run aggregation, render preview table, download files"
```

---

## Task 13: JS — custom timestamp datepicker

**Files:**
- Create: `static/js/datepicker.js`

- [ ] **Step 1: Create `static/js/datepicker.js`**

```javascript
(function () {
  const modeButtons = {
    single: document.getElementById('mode-single'),
    range: document.getElementById('mode-range'),
  };
  const endField = document.getElementById('date-end-field');
  const startLabel = document.getElementById('date-start-label');
  const applyBtn = document.getElementById('apply-date');
  const errorEl = document.getElementById('datepicker-error');
  let mode = 'single';

  function setMode(newMode) {
    mode = newMode;
    endField.hidden = mode === 'single';
    startLabel.textContent = mode === 'single' ? 'Data' : 'De';
    modeButtons.single.className = mode === 'single' ? 'btn btn-secondary btn-sm' : 'btn btn-ghost btn-sm';
    modeButtons.range.className = mode === 'range' ? 'btn btn-secondary btn-sm' : 'btn btn-ghost btn-sm';
  }

  modeButtons.single.addEventListener('click', () => setMode('single'));
  modeButtons.range.addEventListener('click', () => setMode('range'));

  function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = false;
  }

  function clearError() {
    errorEl.hidden = true;
  }

  function nextDay(dateStr) {
    const d = new Date(`${dateStr}T00:00:00Z`);
    d.setUTCDate(d.getUTCDate() + 1);
    return d.toISOString().slice(0, 10);
  }

  function buildClause() {
    const start = document.getElementById('date-start').value;
    if (!start) {
      showError('Escolha uma data.');
      return null;
    }
    if (mode === 'single') {
      return `timestamp: { $regex: "^${start}" }`;
    }
    const end = document.getElementById('date-end').value;
    if (!end) {
      showError('Escolha a data final do intervalo.');
      return null;
    }
    const endExclusive = nextDay(end);
    return `timestamp: { $gte: ISODate("${start}T00:00:00Z"), $lt: ISODate("${endExclusive}T00:00:00Z") }`;
  }

  function applyToEditor(clause) {
    const editor = document.getElementById('pipeline-editor');
    const lines = editor.value.split('\n');
    const timestampLineRe = /^\s*\/{0,2}\s*timestamp\s*:/;
    const matchLineRe = /\$match\s*:\s*\{/;

    const lineIndex = lines.findIndex((line) => timestampLineRe.test(line));
    if (lineIndex !== -1) {
      const indentMatch = lines[lineIndex].match(/^\s*/);
      const indent = indentMatch ? indentMatch[0] : '      ';
      lines[lineIndex] = `${indent}${clause},`;
      editor.value = lines.join('\n');
      return true;
    }

    const matchIndex = lines.findIndex((line) => matchLineRe.test(line));
    if (matchIndex === -1) {
      showError('Não encontrei um estágio $match no pipeline.');
      return false;
    }
    const indentMatch = lines[matchIndex].match(/^\s*/);
    const indent = `${indentMatch ? indentMatch[0] : ''}  `;
    lines.splice(matchIndex + 1, 0, `${indent}${clause},`);
    editor.value = lines.join('\n');
    return true;
  }

  applyBtn.addEventListener('click', () => {
    clearError();
    const clause = buildClause();
    if (!clause) return;
    applyToEditor(clause);
  });

  setMode('single');
})();
```

- [ ] **Step 2: Commit**

```bash
git add static/js/datepicker.js
git commit -m "Add custom timestamp datepicker (single day / range)"
```

---

## Task 14: JS — favorites sidebar and dialog

**Files:**
- Create: `static/js/favorites.js`

- [ ] **Step 1: Create `static/js/favorites.js`**

```javascript
(function () {
  const listEl = document.getElementById('favorites-list');
  const favoriteBtn = document.getElementById('favorite-btn');
  const overlay = document.getElementById('favorite-dialog-overlay');
  const nameInput = document.getElementById('favorite-name');
  const saveBtn = document.getElementById('favorite-save');
  const cancelBtn = document.getElementById('favorite-cancel');
  const errorEl = document.getElementById('favorite-error');

  function setError(message) {
    if (message) {
      errorEl.textContent = message;
      errorEl.hidden = false;
    } else {
      errorEl.hidden = true;
    }
  }

  function openDialog() {
    nameInput.value = '';
    setError(null);
    overlay.hidden = false;
    nameInput.focus();
  }

  function closeDialog() {
    overlay.hidden = true;
  }

  async function loadFavorites() {
    const response = await fetch('/api/favorites');
    const favorites = await response.json();
    renderFavorites(favorites);
  }

  function renderFavorites(favorites) {
    if (favorites.length === 0) {
      listEl.innerHTML = '<li class="empty-state">Nenhum favorito salvo ainda.</li>';
      return;
    }
    listEl.innerHTML = favorites.map((fav) => `
      <li class="favorite-item" data-filename="${fav.filename}">
        <button type="button" class="favorite-load" data-filename="${fav.filename}">
          <span class="favorite-name">${fav.name}</span>
          <span class="favorite-date">${fav.created_at}</span>
        </button>
        <button type="button" class="favorite-delete" data-filename="${fav.filename}" aria-label="Excluir favorito">
          <i data-lucide="trash-2"></i>
        </button>
      </li>
    `).join('');
    if (window.lucide) { window.lucide.createIcons(); }
  }

  listEl.addEventListener('click', async (event) => {
    const loadBtn = event.target.closest('.favorite-load');
    const deleteBtn = event.target.closest('.favorite-delete');
    if (loadBtn) {
      const response = await fetch(`/api/favorites/${encodeURIComponent(loadBtn.dataset.filename)}`);
      if (response.ok) {
        const favorite = await response.json();
        window.LogCenter.setPipelineText(favorite.pipeline);
      }
    } else if (deleteBtn) {
      await fetch(`/api/favorites/${encodeURIComponent(deleteBtn.dataset.filename)}`, { method: 'DELETE' });
      loadFavorites();
    }
  });

  favoriteBtn.addEventListener('click', openDialog);
  cancelBtn.addEventListener('click', closeDialog);

  saveBtn.addEventListener('click', async () => {
    const name = nameInput.value.trim();
    if (!name) {
      setError('Informe um nome.');
      return;
    }
    const response = await fetch('/api/favorites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, pipeline: window.LogCenter.getPipelineText() }),
    });
    const data = await response.json();
    if (!response.ok) {
      setError(data.error || 'Erro ao salvar favorito.');
      return;
    }
    closeDialog();
    loadFavorites();
  });

  loadFavorites();
})();
```

- [ ] **Step 2: Commit**

```bash
git add static/js/favorites.js
git commit -m "Add favorites sidebar: list, load, save via dialog, delete"
```

---

## Task 15: End-to-end manual verification

**Files:** none (verification only — fix forward in the relevant file if something breaks)

- [ ] **Step 1: Fill in real credentials in `.env`**

Edit `.env` (created in Task 1, gitignored) with a real `MONGODB_URI`, `DB_NAME`, `COLLECTION_NAME`, and a chosen `APP_USERNAME`/`APP_PASSWORD`/`SECRET_KEY`.

- [ ] **Step 2: Run the automated test suite**

Run: `python -m pytest -v`
Expected: all `tests/test_pipeline_parser.py` tests pass.

- [ ] **Step 3: Start the app and verify login**

Run: `python -m flask --app app run --debug`

In a browser, open `http://127.0.0.1:5000/` — confirm it redirects to `/login`. Try an incorrect password (expect inline error, stays on `/login`), then the correct credentials (expect redirect to `/download`).

- [ ] **Step 4: Verify the datepicker**

On `/download`, with the pre-filled example pipeline: pick a single day and click "Aplicar data" — confirm the `timestamp` line in the editor updates to `{ $regex: "^YYYY-MM-DD" }` and the previously-commented `// timestamp: { $gt: ... }` line is untouched. Switch to "Intervalo", pick a start/end date, click "Aplicar data" — confirm the line updates to the `$gte`/`$lt` `ISODate(...)` form.

- [ ] **Step 5: Verify run + preview**

Edit `project_id` in the editor to a real `ObjectId` from your Atlas collection, click "Executar" — confirm the preview table renders with the expected columns/rows and the row count badge updates. Test an intentionally broken pipeline (e.g. delete a closing brace) — confirm an inline error appears without crashing the page.

- [ ] **Step 6: Verify favorites**

Click "Favoritar", give it a name, save — confirm it appears in the sidebar and a `.json` file shows up under `favorites/`. Edit the editor to something else, click the saved favorite — confirm it reloads the original pipeline text. Delete the favorite — confirm it disappears from the sidebar and the file is removed from `favorites/`.

- [ ] **Step 7: Verify downloads**

With a successful run showing results, click CSV, then Excel, then JSON — confirm each triggers a file download and the files open correctly with the expected columns/rows.

- [ ] **Step 8: Verify logout and session protection**

Click "Sair" — confirm redirect to `/login`. Try visiting `/download` directly while logged out — confirm redirect to `/login` instead of showing the page.

- [ ] **Step 9: Final commit (only if fixes were needed in Steps 3–8)**

```bash
git add -A
git commit -m "Fix issues found during end-to-end verification"
```
