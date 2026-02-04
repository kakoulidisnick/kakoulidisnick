#!/usr/bin/env python3
"""Υπενθύμιση υποχρεώσεων για λογιστικό γραφείο.

Απλό CLI που αποθηκεύει πελάτες και υποχρεώσεις σε JSON αρχείο.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DATA_FILE = Path("data.json")


def _default_data() -> Dict[str, Any]:
    return {
        "clients": [],
        "obligations": [],
        "users": [],
        "meta": {
            "next_client_id": 1,
            "next_obligation_id": 1,
            "next_user_id": 1,
        },
    }


def _ensure_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    defaults = _default_data()
    for key, value in defaults.items():
        if key not in data:
            data[key] = value
    meta = data.setdefault("meta", {})
    for key, value in defaults["meta"].items():
        meta.setdefault(key, value)
    return data


def _load_data(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return _default_data()
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return _ensure_defaults(data)


def _save_data(path: Path, data: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Η ημερομηνία πρέπει να είναι στη μορφή YYYY-MM-DD.") from exc


def init_command(args: argparse.Namespace) -> None:
    path = Path(args.data_file)
    if path.exists():
        print(f"Το αρχείο {path} υπάρχει ήδη.")
        return
    data = _load_data(path)
    _save_data(path, data)
    print(f"Δημιουργήθηκε το αρχείο {path}.")


def add_client(args: argparse.Namespace) -> None:
    path = Path(args.data_file)
    data = _load_data(path)
    client_id = data["meta"]["next_client_id"]
    data["meta"]["next_client_id"] += 1
    client = {
        "id": client_id,
        "name": args.name,
        "email": args.email,
        "phone": args.phone,
    }
    data["clients"].append(client)
    _save_data(path, data)
    print(f"Προστέθηκε πελάτης #{client_id}: {args.name}")


def list_clients(args: argparse.Namespace) -> None:
    data = _load_data(Path(args.data_file))
    if not data["clients"]:
        print("Δεν υπάρχουν πελάτες.")
        return
    for client in data["clients"]:
        print(f"#{client['id']} {client['name']} | {client.get('email','-')} | {client.get('phone','-')}")


def add_obligation(args: argparse.Namespace) -> None:
    path = Path(args.data_file)
    data = _load_data(path)
    client_ids = {client["id"] for client in data["clients"]}
    if args.client_id not in client_ids:
        raise SystemExit("Το client_id δεν υπάρχει. Προσθέστε πρώτα τον πελάτη.")
    obligation_id = data["meta"]["next_obligation_id"]
    data["meta"]["next_obligation_id"] += 1
    obligation = {
        "id": obligation_id,
        "client_id": args.client_id,
        "assigned_user_id": args.assigned_user_id,
        "title": args.title,
        "due_date": args.due_date.isoformat(),
        "notes": args.notes,
        "status": "open",
        "priority": args.priority,
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    data["obligations"].append(obligation)
    _save_data(path, data)
    print(f"Προστέθηκε υποχρέωση #{obligation_id} για πελάτη #{args.client_id}.")


def _matches_query(obligation: Dict[str, Any], query: str) -> bool:
    haystack = " ".join(
        [
            str(obligation.get("title", "")),
            str(obligation.get("notes", "")),
        ]
    ).lower()
    return query.lower() in haystack


def _filter_obligations(obligations: List[Dict[str, Any]], args: argparse.Namespace) -> List[Dict[str, Any]]:
    result = obligations
    if args.client_id is not None:
        result = [o for o in result if o["client_id"] == args.client_id]
    if args.assigned_user_id is not None:
        result = [o for o in result if o.get("assigned_user_id") == args.assigned_user_id]
    if args.status:
        result = [o for o in result if o["status"] == args.status]
    if args.priority:
        result = [o for o in result if o.get("priority") == args.priority]
    if args.due_before:
        result = [o for o in result if date.fromisoformat(o["due_date"]) <= args.due_before]
    if args.due_after:
        result = [o for o in result if date.fromisoformat(o["due_date"]) >= args.due_after]
    if args.query:
        result = [o for o in result if _matches_query(o, args.query)]
    return result


def list_obligations(args: argparse.Namespace) -> None:
    data = _load_data(Path(args.data_file))
    obligations = _filter_obligations(data["obligations"], args)
    if not obligations:
        print("Δεν υπάρχουν υποχρεώσεις για τα κριτήρια που δώσατε.")
        return
    client_lookup = {client["id"]: client["name"] for client in data["clients"]}
    user_lookup = {user["id"]: user["name"] for user in data.get("users", [])}
    for obligation in obligations:
        client_name = client_lookup.get(obligation["client_id"], "Άγνωστος πελάτης")
        user_name = user_lookup.get(obligation.get("assigned_user_id"), "-")
        print(
            f"#{obligation['id']} | {client_name} | {obligation['title']} | {obligation['due_date']} | "
            f"{obligation['status']} | {obligation.get('priority','normal')} | Υπεύθυνος: {user_name}"
        )
        if obligation.get("notes"):
            print(f"  Σημειώσεις: {obligation['notes']}")


def add_user(args: argparse.Namespace) -> None:
    path = Path(args.data_file)
    data = _load_data(path)
    user_id = data["meta"]["next_user_id"]
    data["meta"]["next_user_id"] += 1
    user = {
        "id": user_id,
        "name": args.name,
        "email": args.email,
        "role": args.role,
    }
    data["users"].append(user)
    _save_data(path, data)
    print(f"Προστέθηκε χρήστης #{user_id}: {args.name}")


def list_users(args: argparse.Namespace) -> None:
    data = _load_data(Path(args.data_file))
    if not data.get("users"):
        print("Δεν υπάρχουν χρήστες.")
        return
    for user in data["users"]:
        print(f"#{user['id']} {user['name']} | {user.get('email','-')} | {user.get('role','staff')}")


def export_obligations(args: argparse.Namespace) -> None:
    data = _load_data(Path(args.data_file))
    obligations = _filter_obligations(data["obligations"], args)
    output_path = Path(args.output)
    client_lookup = {client["id"]: client["name"] for client in data["clients"]}
    user_lookup = {user["id"]: user["name"] for user in data.get("users", [])}
    lines = [
        "id,client,assigned_user,title,due_date,status,priority,notes",
    ]
    for obligation in obligations:
        client_name = client_lookup.get(obligation["client_id"], "")
        user_name = user_lookup.get(obligation.get("assigned_user_id"), "")
        notes = (obligation.get("notes") or "").replace("\"", "\"\"")
        title = str(obligation.get("title", "")).replace("\"", "\"\"")
        line = (
            f"{obligation['id']},\"{client_name}\",\"{user_name}\",\"{title}\",{obligation['due_date']},"
            f"{obligation['status']},{obligation.get('priority','normal')},\"{notes}\""
        )
        lines.append(line)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Εξήχθησαν {len(obligations)} υποχρεώσεις στο {output_path}")


def mark_complete(args: argparse.Namespace) -> None:
    path = Path(args.data_file)
    data = _load_data(path)
    for obligation in data["obligations"]:
        if obligation["id"] == args.obligation_id:
            obligation["status"] = "complete"
            _save_data(path, data)
            print(f"Η υποχρέωση #{args.obligation_id} ολοκληρώθηκε.")
            return
    raise SystemExit("Δεν βρέθηκε υποχρέωση με αυτό το ID.")


def due_within(args: argparse.Namespace) -> None:
    today = date.today()
    due_before = today + timedelta(days=args.days)
    args.due_after = today
    args.due_before = due_before
    args.status = "open"
    list_obligations(args)


def due_today(args: argparse.Namespace) -> None:
    args.days = 0
    due_within(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Υπενθυμίσεις υποχρεώσεων λογιστικού γραφείου",
    )
    parser.add_argument("--data-file", default=str(DEFAULT_DATA_FILE), help="Διαδρομή JSON αρχείου δεδομένων")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Δημιουργία αρχείου δεδομένων")
    init_parser.set_defaults(func=init_command)

    add_client_parser = subparsers.add_parser("add-client", help="Προσθήκη πελάτη")
    add_client_parser.add_argument("--name", required=True)
    add_client_parser.add_argument("--email", default="")
    add_client_parser.add_argument("--phone", default="")
    add_client_parser.set_defaults(func=add_client)

    list_clients_parser = subparsers.add_parser("list-clients", help="Λίστα πελατών")
    list_clients_parser.set_defaults(func=list_clients)

    add_obligation_parser = subparsers.add_parser("add-obligation", help="Προσθήκη υποχρέωσης")
    add_obligation_parser.add_argument("--client-id", type=int, required=True)
    add_obligation_parser.add_argument("--assigned-user-id", type=int)
    add_obligation_parser.add_argument("--title", required=True)
    add_obligation_parser.add_argument("--due-date", type=_parse_date, required=True)
    add_obligation_parser.add_argument("--notes", default="")
    add_obligation_parser.add_argument("--priority", choices=["low", "normal", "critical"], default="normal")
    add_obligation_parser.set_defaults(func=add_obligation)

    list_obligations_parser = subparsers.add_parser("list-obligations", help="Λίστα υποχρεώσεων")
    list_obligations_parser.add_argument("--client-id", type=int)
    list_obligations_parser.add_argument("--assigned-user-id", type=int)
    list_obligations_parser.add_argument("--status", choices=["open", "complete"])
    list_obligations_parser.add_argument("--priority", choices=["low", "normal", "critical"])
    list_obligations_parser.add_argument("--due-before", type=_parse_date)
    list_obligations_parser.add_argument("--due-after", type=_parse_date)
    list_obligations_parser.add_argument("--query")
    list_obligations_parser.set_defaults(func=list_obligations)

    add_user_parser = subparsers.add_parser("add-user", help="Προσθήκη χρήστη")
    add_user_parser.add_argument("--name", required=True)
    add_user_parser.add_argument("--email", default="")
    add_user_parser.add_argument("--role", choices=["admin", "staff"], default="staff")
    add_user_parser.set_defaults(func=add_user)

    list_users_parser = subparsers.add_parser("list-users", help="Λίστα χρηστών")
    list_users_parser.set_defaults(func=list_users)

    mark_complete_parser = subparsers.add_parser("mark-complete", help="Ολοκλήρωση υποχρέωσης")
    mark_complete_parser.add_argument("--obligation-id", type=int, required=True)
    mark_complete_parser.set_defaults(func=mark_complete)

    due_within_parser = subparsers.add_parser("due-within", help="Υποχρεώσεις που λήγουν εντός ημερών")
    due_within_parser.add_argument("--days", type=int, required=True)
    due_within_parser.set_defaults(func=due_within)

    due_today_parser = subparsers.add_parser("due-today", help="Υποχρεώσεις που λήγουν σήμερα")
    due_today_parser.set_defaults(func=due_today)

    export_parser = subparsers.add_parser("export-obligations", help="Εξαγωγή υποχρεώσεων σε CSV")
    export_parser.add_argument("--output", required=True)
    export_parser.add_argument("--client-id", type=int)
    export_parser.add_argument("--assigned-user-id", type=int)
    export_parser.add_argument("--status", choices=["open", "complete"])
    export_parser.add_argument("--priority", choices=["low", "normal", "critical"])
    export_parser.add_argument("--due-before", type=_parse_date)
    export_parser.add_argument("--due-after", type=_parse_date)
    export_parser.add_argument("--query")
    export_parser.set_defaults(func=export_obligations)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
