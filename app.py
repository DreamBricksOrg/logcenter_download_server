import datetime
import logging

from bson import json_util
from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for

import config
from auth import login_required, verify_credentials
from services import favorites as favorites_service
from services.export import to_csv_bytes, to_json_bytes, to_xlsx_bytes
from services.mongo_client import MongoConnectionError, run_aggregation
from services.pipeline_parser import PipelineParseError, parse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

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


def _extract_columns(rows):
    columns = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def _json_safe(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, (dict, list)):
        return json_util.dumps(value, ensure_ascii=False)
    return str(value)


def _stringify_rows(rows, columns):
    stringified = []
    for row in rows:
        record = {}
        for col in columns:
            record[col] = _json_safe(row.get(col, ""))
        stringified.append(record)
    return stringified


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


@app.route("/api/run", methods=["POST"])
@login_required
def api_run():
    payload = request.get_json(silent=True) or {}
    pipeline_text = payload.get("pipeline", "")
    logger.info("api_run: received pipeline text (%d chars)", len(pipeline_text))
    logger.debug("api_run: raw pipeline text:\n%s", pipeline_text)
    try:
        stages = parse(pipeline_text)
        logger.info("api_run: parsed %d stage(s): %s", len(stages), json_util.dumps(stages))
        rows = run_aggregation(stages)
        logger.info("api_run: aggregation returned %d row(s)", len(rows))
    except PipelineParseError as exc:
        logger.warning("api_run: pipeline parse error: %s", exc)
        return jsonify({"error": str(exc)}), 400
    except MongoConnectionError as exc:
        logger.error("api_run: MongoDB connection error: %s", exc, exc_info=True)
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
    logger.info("download_file(%s): received pipeline text (%d chars)", fmt, len(pipeline_text))
    try:
        stages = parse(pipeline_text)
        rows = run_aggregation(stages)
        logger.info("download_file(%s): aggregation returned %d row(s)", fmt, len(rows))
    except PipelineParseError as exc:
        logger.warning("download_file(%s): pipeline parse error: %s", fmt, exc)
        return jsonify({"error": str(exc)}), 400
    except MongoConnectionError as exc:
        logger.error("download_file(%s): MongoDB connection error: %s", fmt, exc, exc_info=True)
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


if __name__ == "__main__":
    app.run(debug=True)
