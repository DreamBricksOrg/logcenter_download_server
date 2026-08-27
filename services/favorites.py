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
