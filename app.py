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
