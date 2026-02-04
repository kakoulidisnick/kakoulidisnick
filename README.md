# Υπενθυμίσεις Υποχρεώσεων Λογιστικού Γραφείου

Μια απλή εφαρμογή γραμμής εντολών (CLI) που βοηθά ένα λογιστικό γραφείο να καταγράφει πελάτες και να παρακολουθεί τις υποχρεώσεις τους (π.χ. προθεσμίες δηλώσεων, πληρωμές, αρχεία).

## Χαρακτηριστικά
- Καταχώριση πελατών.
- Καταχώριση υποχρεώσεων με ημερομηνία λήξης.
- Φίλτρα για λίστα υποχρεώσεων.
- Γρήγορη προβολή υποχρεώσεων που λήγουν σήμερα ή μέσα σε Χ ημέρες.

## Γρήγορη εκκίνηση

```bash
python3 app.py init
python3 app.py add-client --name "Acme A.E." --email "info@acme.gr" --phone "2100000000"
python3 app.py add-obligation --client-id 1 --title "ΦΠΑ Q1" --due-date 2024-06-30 --notes "Υποβολή περιοδικής δήλωσης"
python3 app.py list-obligations
```

## Web περιβάλλον

Για να χρησιμοποιήσετε το γραφικό περιβάλλον, εγκαταστήστε το Flask και τρέξτε την εφαρμογή:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 web_app.py
```

Έπειτα ανοίξτε το `http://localhost:5000`.

### Οδηγίες για Windows

Σε Windows μπορείτε να χρησιμοποιήσετε τον Python Launcher (`py`) και την ενεργοποίηση του virtual environment:

```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
py web_app.py
```

## Διαθέσιμες εντολές

- `init`: Δημιουργεί το αρχείο δεδομένων (προεπιλογή: `data.json`).
- `add-client`: Προσθήκη πελάτη.
- `list-clients`: Λίστα πελατών.
- `add-obligation`: Προσθήκη υποχρέωσης.
- `list-obligations`: Λίστα υποχρεώσεων με φίλτρα.
- `mark-complete`: Σήμανση υποχρέωσης ως ολοκληρωμένη.
- `due-today`: Υποχρεώσεις που λήγουν σήμερα.
- `due-within`: Υποχρεώσεις που λήγουν μέσα σε Χ ημέρες.

### Παράδειγμα φίλτρων

```bash
python3 app.py list-obligations --client-id 1 --status open
python3 app.py due-within --days 7
```

## Αποθήκευση δεδομένων
Τα δεδομένα αποθηκεύονται σε JSON αρχείο (`data.json`) στον ίδιο φάκελο. Μπορείτε να αλλάξετε τη διαδρομή με το `--data-file`.

```bash
python3 app.py list-clients --data-file /path/to/office-data.json
```

Για το web περιβάλλον μπορείτε να ορίσετε διαφορετικό αρχείο με μεταβλητή περιβάλλοντος:

```bash
DATA_FILE=/path/to/office-data.json python3 web_app.py
```

## Πώς βλέπω άμεσα τις αλλαγές μου;

### Στον κώδικα (Git)

```bash
git status -sb
git diff
git diff --staged
```

### Στο web περιβάλλον

Όταν τρέχετε το `web_app.py`, η Flask είναι σε `debug` mode, οπότε κάνει αυτόματα reload όταν αποθηκεύετε αλλαγές. Αρκεί να κάνετε refresh στο browser.

## Επόμενα βήματα (ιδέες)
- Αποστολή email/SMS υπενθυμίσεων.
- Web interface για ευκολότερη χρήση.
- Ρόλοι χρηστών και ιστορικό ενεργειών.
