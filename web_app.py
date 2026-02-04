#!/usr/bin/env python3
"""Web UI για υπενθυμίσεις υποχρεώσεων λογιστικού γραφείου."""
from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, redirect, render_template, request, url_for

import app as cli_app

DATA_FILE = Path(os.environ.get("DATA_FILE", "data.json"))


def ensure_data_file() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        data = cli_app._load_data(DATA_FILE)
        cli_app._save_data(DATA_FILE, data)
    return cli_app._load_data(DATA_FILE)


def add_client(name: str, email: str, phone: str) -> None:
    data = ensure_data_file()
    client_id = data["meta"]["next_client_id"]
    data["meta"]["next_client_id"] += 1
    data["clients"].append(
        {
            "id": client_id,
            "name": name,
            "email": email,
            "phone": phone,
        }
    )
    cli_app._save_data(DATA_FILE, data)


def add_obligation(client_id: int, title: str, due_date: date, notes: str) -> None:
    data = ensure_data_file()
    obligation_id = data["meta"]["next_obligation_id"]
    data["meta"]["next_obligation_id"] += 1
    data["obligations"].append(
        {
            "id": obligation_id,
            "client_id": client_id,
            "title": title,
            "due_date": due_date.isoformat(),
            "notes": notes,
            "status": "open",
            "created_at": cli_app.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
    )
    cli_app._save_data(DATA_FILE, data)


def mark_complete(obligation_id: int) -> None:
    data = ensure_data_file()
    for obligation in data["obligations"]:
        if obligation["id"] == obligation_id:
            obligation["status"] = "complete"
            break
    cli_app._save_data(DATA_FILE, data)


def get_upcoming(obligations: List[Dict[str, Any]], days: int = 7) -> List[Dict[str, Any]]:
    today = date.today()
    due_before = today + timedelta(days=days)
    filtered = []
    for obligation in obligations:
        due_date = date.fromisoformat(obligation["due_date"])
        if obligation["status"] == "open" and today <= due_date <= due_before:
            filtered.append(obligation)
    return filtered


app = Flask(__name__)


@app.route("/")
def index() -> str:
    data = ensure_data_file()
    upcoming = get_upcoming(data["obligations"], days=7)
    client_lookup = {client["id"]: client["name"] for client in data["clients"]}
    return render_template(
        "index.html",
        clients=data["clients"],
        obligations=data["obligations"],
        upcoming=upcoming,
        client_lookup=client_lookup,
    )


@app.route("/clients", methods=["GET", "POST"])
def clients() -> str:
    data = ensure_data_file()
    if request.method == "POST":
        add_client(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip(),
            phone=request.form.get("phone", "").strip(),
        )
        return redirect(url_for("clients"))
    return render_template("clients.html", clients=data["clients"])


@app.route("/obligations", methods=["GET", "POST"])
def obligations() -> str:
    data = ensure_data_file()
    if request.method == "POST":
        due_date_value = request.form.get("due_date", "")
        if due_date_value:
            due_date = cli_app._parse_date(due_date_value)
            add_obligation(
                client_id=int(request.form.get("client_id", "0")),
                title=request.form.get("title", "").strip(),
                due_date=due_date,
                notes=request.form.get("notes", "").strip(),
            )
        return redirect(url_for("obligations"))
    client_lookup = {client["id"]: client["name"] for client in data["clients"]}
    return render_template(
        "obligations.html",
        obligations=data["obligations"],
        clients=data["clients"],
        client_lookup=client_lookup,
    )


@app.post("/obligations/<int:obligation_id>/complete")
def complete_obligation(obligation_id: int) -> str:
    mark_complete(obligation_id)
    return redirect(url_for("obligations"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
