#!/usr/bin/env python3
"""Υπενθύμιση υποχρεώσεων για λογιστικό γραφείο.

Απλό CLI που αποθηκεύει πελάτες και υποχρεώσεις σε JSON αρχείο.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_DATA_FILE = Path("data.json")


def _load_data(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"clients": [], "obligations": [], "meta": {"next_client_id": 1, "next_obligation_id": 1}}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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
        "title": args.title,
        "due_date": args.due_date.isoformat(),
        "notes": args.notes,
        "status": "open",
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    data["obligations"].append(obligation)
    _save_data(path, data)
    print(f"Προστέθηκε υποχρέωση #{obligation_id} για πελάτη #{args.client_id}.")


def _filter_obligations(obligations: List[Dict[str, Any]], args: argparse.Namespace) -> List[Dict[str, Any]]:
    result = obligations
    if args.client_id is not None:
        result = [o for o in result if o["client_id"] == args.client_id]
    if args.status:
        result = [o for o in result if o["status"] == args.status]
    if args.due_before:
        result = [o for o in result if date.fromisoformat(o["due_date"]) <= args.due_before]
    if args.due_after:
        result = [o for o in result if date.fromisoformat(o["due_date"]) >= args.due_after]
    return result


def list_obligations(args: argparse.Namespace) -> None:
    data = _load_data(Path(args.data_file))
    obligations = _filter_obligations(data["obligations"], args)
    if not obligations:
        print("Δεν υπάρχουν υποχρεώσεις για τα κριτήρια που δώσατε.")
        return
    client_lookup = {client["id"]: client["name"] for client in data["clients"]}
    for obligation in obligations:
        client_name = client_lookup.get(obligation["client_id"], "Άγνωστος πελάτης")
        print(
            f"#{obligation['id']} | {client_name} | {obligation['title']} | {obligation['due_date']} | {obligation['status']}"
        )
        if obligation.get("notes"):
            print(f"  Σημειώσεις: {obligation['notes']}")


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
    add_obligation_parser.add_argument("--title", required=True)
    add_obligation_parser.add_argument("--due-date", type=_parse_date, required=True)
    add_obligation_parser.add_argument("--notes", default="")
    add_obligation_parser.set_defaults(func=add_obligation)

    list_obligations_parser = subparsers.add_parser("list-obligations", help="Λίστα υποχρεώσεων")
    list_obligations_parser.add_argument("--client-id", type=int)
    list_obligations_parser.add_argument("--status", choices=["open", "complete"])
    list_obligations_parser.add_argument("--due-before", type=_parse_date)
    list_obligations_parser.add_argument("--due-after", type=_parse_date)
    list_obligations_parser.set_defaults(func=list_obligations)

    mark_complete_parser = subparsers.add_parser("mark-complete", help="Ολοκλήρωση υποχρέωσης")
    mark_complete_parser.add_argument("--obligation-id", type=int, required=True)
    mark_complete_parser.set_defaults(func=mark_complete)

    due_within_parser = subparsers.add_parser("due-within", help="Υποχρεώσεις που λήγουν εντός ημερών")
    due_within_parser.add_argument("--days", type=int, required=True)
    due_within_parser.set_defaults(func=due_within)

    due_today_parser = subparsers.add_parser("due-today", help="Υποχρεώσεις που λήγουν σήμερα")
    due_today_parser.set_defaults(func=due_today)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
