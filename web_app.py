#!/usr/bin/env python3
"""Web UI για υπενθυμίσεις υποχρεώσεων λογιστικού γραφείου."""
from __future__ import annotations

import csv
import io
import os
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, Response, redirect, render_template, request, url_for

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


def add_obligation(
    client_id: int,
    title: str,
    due_date: date,
    notes: str,
    priority: str,
    assigned_user_id: int | None,
) -> None:
    data = ensure_data_file()
    obligation_id = data["meta"]["next_obligation_id"]
    data["meta"]["next_obligation_id"] += 1
    data["obligations"].append(
        {
            "id": obligation_id,
            "client_id": client_id,
            "assigned_user_id": assigned_user_id,
            "title": title,
            "due_date": due_date.isoformat(),
            "notes": notes,
            "status": "open",
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
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


def add_user(name: str, email: str, role: str) -> None:
    data = ensure_data_file()
    user_id = data["meta"]["next_user_id"]
    data["meta"]["next_user_id"] += 1
    data["users"].append(
        {
            "id": user_id,
            "name": name,
            "email": email,
            "role": role,
        }
    )
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


def filter_obligations(
    obligations: List[Dict[str, Any]],
    client_id: int | None = None,
    assigned_user_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    due_from: date | None = None,
    due_to: date | None = None,
    query: str | None = None,
) -> List[Dict[str, Any]]:
    results = obligations
    if client_id is not None:
        results = [o for o in results if o["client_id"] == client_id]
    if assigned_user_id is not None:
        results = [o for o in results if o.get("assigned_user_id") == assigned_user_id]
    if status:
        results = [o for o in results if o["status"] == status]
    if priority:
        results = [o for o in results if o.get("priority") == priority]
    if due_from:
        results = [o for o in results if date.fromisoformat(o["due_date"]) >= due_from]
    if due_to:
        results = [o for o in results if date.fromisoformat(o["due_date"]) <= due_to]
    if query:
        q = query.lower()
        results = [
            o
            for o in results
            if q in str(o.get("title", "")).lower() or q in str(o.get("notes", "")).lower()
        ]
    return results


def build_calendar(year: int, month: int, obligations: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    first_weekday, days_in_month = monthrange(year, month)
    day_lookup: Dict[int, List[Dict[str, Any]]] = {}
    for obligation in obligations:
        due_date = date.fromisoformat(obligation["due_date"])
        if due_date.year == year and due_date.month == month:
            day_lookup.setdefault(due_date.day, []).append(obligation)
    weeks: List[List[Dict[str, Any]]] = []
    week: List[Dict[str, Any]] = []
    for _ in range(first_weekday):
        week.append({"day": None, "items": []})
    for day in range(1, days_in_month + 1):
        week.append({"day": day, "items": day_lookup.get(day, [])})
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append({"day": None, "items": []})
        weeks.append(week)
    return weeks


app = Flask(__name__)


@app.route("/")
def index() -> str:
    data = ensure_data_file()
    upcoming = get_upcoming(data["obligations"], days=7)
    client_lookup = {client["id"]: client["name"] for client in data["clients"]}
    user_lookup = {user["id"]: user["name"] for user in data.get("users", [])}
    return render_template(
        "index.html",
        clients=data["clients"],
        obligations=data["obligations"],
        upcoming=upcoming,
        client_lookup=client_lookup,
        user_lookup=user_lookup,
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


@app.route("/users", methods=["GET", "POST"])
def users() -> str:
    data = ensure_data_file()
    if request.method == "POST":
        add_user(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip(),
            role=request.form.get("role", "staff"),
        )
        return redirect(url_for("users"))
    return render_template("users.html", users=data.get("users", []))


@app.route("/obligations", methods=["GET", "POST"])
def obligations() -> str:
    data = ensure_data_file()
    if request.method == "POST":
        due_date_value = request.form.get("due_date", "")
        if due_date_value:
            due_date = cli_app._parse_date(due_date_value)
            add_obligation(
                client_id=int(request.form.get("client_id", "0")),
                assigned_user_id=int(request.form.get("assigned_user_id", "0") or 0) or None,
                title=request.form.get("title", "").strip(),
                due_date=due_date,
                notes=request.form.get("notes", "").strip(),
                priority=request.form.get("priority", "normal"),
            )
        return redirect(url_for("obligations"))
    filters = {
        "client_id": request.args.get("client_id", type=int),
        "assigned_user_id": request.args.get("assigned_user_id", type=int),
        "status": request.args.get("status"),
        "priority": request.args.get("priority"),
        "due_from": request.args.get("due_from", type=cli_app._parse_date),
        "due_to": request.args.get("due_to", type=cli_app._parse_date),
        "query": request.args.get("query"),
    }
    obligations_filtered = filter_obligations(data["obligations"], **filters)
    export_params = {key: value for key, value in filters.items() if value not in (None, "")}
    client_lookup = {client["id"]: client["name"] for client in data["clients"]}
    user_lookup = {user["id"]: user["name"] for user in data.get("users", [])}
    return render_template(
        "obligations.html",
        obligations=obligations_filtered,
        clients=data["clients"],
        client_lookup=client_lookup,
        users=data.get("users", []),
        user_lookup=user_lookup,
        filters=filters,
        export_params=export_params,
    )


@app.post("/obligations/<int:obligation_id>/complete")
def complete_obligation(obligation_id: int) -> str:
    mark_complete(obligation_id)
    return redirect(url_for("obligations"))


@app.get("/reminders")
def reminders() -> str:
    data = ensure_data_file()
    days = request.args.get("days", default=7, type=int)
    upcoming = get_upcoming(data["obligations"], days=days)
    client_lookup = {client["id"]: client["name"] for client in data["clients"]}
    user_lookup = {user["id"]: user["name"] for user in data.get("users", [])}
    return render_template(
        "reminders.html",
        upcoming=upcoming,
        days=days,
        client_lookup=client_lookup,
        user_lookup=user_lookup,
    )


@app.get("/calendar")
def calendar_view() -> str:
    data = ensure_data_file()
    today = date.today()
    year = request.args.get("year", default=today.year, type=int)
    month = request.args.get("month", default=today.month, type=int)
    calendar_weeks = build_calendar(year, month, data["obligations"])
    client_lookup = {client["id"]: client["name"] for client in data["clients"]}
    return render_template(
        "calendar.html",
        weeks=calendar_weeks,
        year=year,
        month=month,
        client_lookup=client_lookup,
    )


@app.get("/export/obligations.csv")
def export_obligations() -> Response:
    data = ensure_data_file()
    filters = {
        "client_id": request.args.get("client_id", type=int),
        "assigned_user_id": request.args.get("assigned_user_id", type=int),
        "status": request.args.get("status"),
        "priority": request.args.get("priority"),
        "due_from": request.args.get("due_from", type=cli_app._parse_date),
        "due_to": request.args.get("due_to", type=cli_app._parse_date),
        "query": request.args.get("query"),
    }
    obligations_filtered = filter_obligations(data["obligations"], **filters)
    client_lookup = {client["id"]: client["name"] for client in data["clients"]}
    user_lookup = {user["id"]: user["name"] for user in data.get("users", [])}
    output = []
    output.append(["id", "client", "assigned_user", "title", "due_date", "status", "priority", "notes"])
    for obligation in obligations_filtered:
        output.append(
            [
                obligation["id"],
                client_lookup.get(obligation["client_id"], ""),
                user_lookup.get(obligation.get("assigned_user_id"), ""),
                obligation.get("title", ""),
                obligation.get("due_date", ""),
                obligation.get("status", ""),
                obligation.get("priority", "normal"),
                obligation.get("notes", ""),
            ]
        )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(output)
    csv_content = buffer.getvalue()
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=obligations.csv"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
