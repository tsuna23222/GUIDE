"""
Election System - Capstone Project 2 Skills Test
Python + tkinter (UI) + sqlite3 (database). No pip installs needed.

Run:  python crud2_app.py
The database file (election.db) is created next to this script on first run.
"""
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "election.db")


# ----------------------------------------------------------------------
# 1. DATABASE LAYER
# ----------------------------------------------------------------------
def run(sql, params=(), fetch=False):
    """Open -> execute -> commit -> close. Returns rows if fetch=True."""
    con = sqlite3.connect(DB)
    try:
        cur = con.execute(sql, params)
        rows = cur.fetchall() if fetch else None
        con.commit()
        return rows
    finally:
        con.close()


def init_db():
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS positions (
        posID          INTEGER PRIMARY KEY AUTOINCREMENT,
        posName        TEXT NOT NULL,
        numOfPositions INTEGER NOT NULL DEFAULT 1,
        posStat        INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS voters (
        voterID    TEXT PRIMARY KEY,
        voterPass  TEXT NOT NULL,
        voterFName TEXT NOT NULL,
        voterMName TEXT,
        voterLName TEXT NOT NULL,
        voterStat  INTEGER NOT NULL DEFAULT 1,
        voted      INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS candidates (
        candID    INTEGER PRIMARY KEY AUTOINCREMENT,
        candFName TEXT NOT NULL,
        candMName TEXT,
        candLName TEXT NOT NULL,
        posID     INTEGER NOT NULL,
        candStat  INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (posID) REFERENCES positions(posID)
    );
    CREATE TABLE IF NOT EXISTS votes (
        posID   INTEGER NOT NULL,
        voterID TEXT    NOT NULL,
        candID  INTEGER NOT NULL
    );
    """)
    con.commit()
    con.close()


def check_voter(voter_id, password):
    """Returns (first_name, None) if allowed, else (None, error_message)."""
    row = run("SELECT voterFName, voterStat, voted FROM voters WHERE voterID=? AND voterPass=?",
              (voter_id, password), fetch=True)
    if not row:
        return None, "Wrong voter ID or password."
    fname, stat, voted = row[0]
    if stat != 1:
        return None, "Your voter account is not active."
    if voted == 1:
        return None, "You have already voted."
    return fname, None


def seed_if_empty():
    """Small sample data so you can test right away."""
    if run("SELECT COUNT(*) FROM positions", fetch=True)[0][0] > 0:
        return
    for name, n in [("President", 1), ("Vice President", 1), ("Senator", 3)]:
        run("INSERT INTO positions (posName, numOfPositions) VALUES (?,?)", (name, n))
    cands = [("Ana", "", "Reyes", 1), ("Ben", "", "Cruz", 1),
             ("Cara", "", "Lopez", 2), ("Dan", "", "Tan", 2),
             ("Eli", "", "Sy", 3), ("Faye", "", "Go", 3),
             ("Gio", "", "Lim", 3), ("Hana", "", "Uy", 3)]
    for c in cands:
        run("INSERT INTO candidates (candFName,candMName,candLName,posID) VALUES (?,?,?,?)", c)
    for i in range(1, 4):
        run("INSERT INTO voters (voterID,voterPass,voterFName,voterLName) VALUES (?,?,?,?)",
            (f"v{i:03d}", "1234", f"Voter{i}", "Test"))


# ----------------------------------------------------------------------
# 2. REUSABLE CRUD TAB (used for Positions, Candidates, Voters)
# ----------------------------------------------------------------------
class CrudTab(ttk.Frame):
    """
    fields: list of dicts
      col       -> column name in the table
      label     -> text shown on the form
      kind      -> 'entry' (default), 'int', or 'combo'
      optional  -> True if it may be left blank
      pk        -> True if it is the (user-typed) primary key: editable on Add only
      values    -> function returning combobox values (for kind='combo')
    auto_pk: name of an AUTOINCREMENT pk column (not typed by the user), or None
    """

    def __init__(self, parent, table, fields, status_col, auto_pk=None, extra_cols=()):
        super().__init__(parent, padding=10)
        self.table, self.fields = table, fields
        self.status_col, self.auto_pk = status_col, auto_pk
        self.extra_cols = list(extra_cols)          # shown in table, not in form
        self.selected_key = None
        self.widgets = {}

        # --- form ---
        form = ttk.LabelFrame(self, text=f"{table.title()} Form", padding=10)
        form.pack(fill="x")
        for i, f in enumerate(fields):
            ttk.Label(form, text=f["label"]).grid(row=i, column=0, sticky="w", pady=2)
            if f.get("kind") == "combo":
                w = ttk.Combobox(form, state="readonly", width=34)
            else:
                w = ttk.Entry(form, width=37)
            w.grid(row=i, column=1, padx=8, pady=2, sticky="w")
            self.widgets[f["col"]] = w

        # --- buttons ---
        bar = ttk.Frame(form)
        bar.grid(row=len(fields), column=0, columnspan=2, pady=(8, 0), sticky="w")
        for text, cmd in [("Add", self.add), ("Update", self.update),
                          ("Deactivate", lambda: self.set_status(0)),
                          ("Activate", lambda: self.set_status(1)),
                          ("Clear", self.clear)]:
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=3)

        # --- table ---
        key_cols = [auto_pk] if auto_pk else []
        self.cols = key_cols + [f["col"] for f in fields if f["col"] != auto_pk] \
            + self.extra_cols + [status_col]
        self.tree = ttk.Treeview(self, columns=self.cols, show="headings", height=12)
        for c in self.cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=95, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(10, 0))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.refresh()

    # ----- helpers -----
    def pk_col(self):
        if self.auto_pk:
            return self.auto_pk
        return next(f["col"] for f in self.fields if f.get("pk"))

    def read_form(self):
        data = {}
        for f in self.fields:
            val = self.widgets[f["col"]].get().strip()
            if f.get("kind") == "combo" and val:
                val = val.split(" - ")[0]          # "2 - Vice President" -> "2"
            if not val and not f.get("optional"):
                messagebox.showwarning("Missing data", f"{f['label']} is required.")
                return None
            if f.get("kind") == "int" or f.get("kind") == "combo":
                if not val.isdigit() or int(val) < 1:
                    messagebox.showwarning("Invalid", f"{f['label']} must be a whole number >= 1.")
                    return None
            data[f["col"]] = val
        return data

    def refresh_combos(self):
        for f in self.fields:
            if f.get("kind") == "combo":
                self.widgets[f["col"]]["values"] = f["values"]()

    def refresh(self):
        self.refresh_combos()
        self.tree.delete(*self.tree.get_children())
        for row in run(f"SELECT {', '.join(self.cols)} FROM {self.table}", fetch=True):
            self.tree.insert("", "end", values=row)
        # status shown as 1/0 -> keep grey for inactive rows
        self.tree.tag_configure("off", foreground="gray")
        for item in self.tree.get_children():
            if str(self.tree.set(item, self.status_col)) == "0":
                self.tree.item(item, tags=("off",))

    def clear(self):
        self.selected_key = None
        for w in self.widgets.values():
            w.config(state="normal") if isinstance(w, ttk.Entry) else None
            w.set("") if isinstance(w, ttk.Combobox) else w.delete(0, "end")
        self.tree.selection_remove(self.tree.selection())

    def on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        row = dict(zip(self.cols, self.tree.item(sel[0], "values")))
        self.selected_key = row[self.pk_col()]
        for f in self.fields:
            w, v = self.widgets[f["col"]], row[f["col"]]
            if isinstance(w, ttk.Combobox):
                match = [x for x in w["values"] if x.split(" - ")[0] == v]
                w.set(match[0] if match else "")
            else:
                w.config(state="normal")
                w.delete(0, "end")
                w.insert(0, v)
                if f.get("pk"):
                    w.config(state="disabled")      # can't change a primary key

    # ----- CRUD -----
    def add(self):
        data = self.read_form()
        if data is None:
            return
        cols = ", ".join(data)
        marks = ", ".join("?" for _ in data)
        try:
            run(f"INSERT INTO {self.table} ({cols}) VALUES ({marks})", tuple(data.values()))
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate", "That ID already exists.")
            return
        self.clear()
        self.refresh()

    def update(self):
        if self.selected_key is None:
            messagebox.showinfo("Select", "Click a row in the table first.")
            return
        # disabled entries can't be read reliably, so re-enable briefly
        for f in self.fields:
            if f.get("pk"):
                self.widgets[f["col"]].config(state="normal")
        data = self.read_form()
        if data is None:
            return
        pk = self.pk_col()
        data.pop(pk, None)                          # never SET the primary key
        sets = ", ".join(f"{c}=?" for c in data)
        run(f"UPDATE {self.table} SET {sets} WHERE {pk}=?",
            tuple(data.values()) + (self.selected_key,))
        self.clear()
        self.refresh()

    def set_status(self, value):
        if self.selected_key is None:
            messagebox.showinfo("Select", "Click a row in the table first.")
            return
        run(f"UPDATE {self.table} SET {self.status_col}=? WHERE {self.pk_col()}=?",
            (value, self.selected_key))
        self.clear()
        self.refresh()


# ----------------------------------------------------------------------
# 3. VOTING TAB
# ----------------------------------------------------------------------
class VotingTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.voter = None
        self.lists = {}     # posID -> (Listbox, [candIDs], limit, last_selection)

        self.login = ttk.LabelFrame(self, text="Voter Login", padding=15)
        ttk.Label(self.login, text="Voter ID").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Label(self.login, text="Password").grid(row=1, column=0, sticky="w", pady=3)
        self.e_id = ttk.Entry(self.login, width=25)
        self.e_pw = ttk.Entry(self.login, width=25, show="*")
        self.e_id.grid(row=0, column=1, padx=8)
        self.e_pw.grid(row=1, column=1, padx=8)
        ttk.Button(self.login, text="Login", command=self.do_login).grid(row=2, column=1, sticky="e", pady=8)

        self.ballot = ttk.Frame(self)
        self.show_login()

    def show_login(self):
        self.voter = None
        self.ballot.pack_forget()
        self.e_id.delete(0, "end")
        self.e_pw.delete(0, "end")
        self.login.pack(pady=40)

    def do_login(self):
        vid, pw = self.e_id.get().strip(), self.e_pw.get()
        fname, error = check_voter(vid, pw)
        if error:
            return messagebox.showerror("Login failed", error)
        self.voter = vid
        self.build_ballot(fname)

    def build_ballot(self, fname):
        self.login.pack_forget()
        for w in self.ballot.winfo_children():
            w.destroy()
        self.lists.clear()
        self.ballot.pack(fill="both", expand=True)
        ttk.Label(self.ballot, text=f"Welcome, {fname}! Select your candidates.",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")

        holder = ttk.Frame(self.ballot)
        holder.pack(fill="both", expand=True, pady=8)
        positions = run("SELECT posID, posName, numOfPositions FROM positions WHERE posStat=1", fetch=True)
        for pid, pname, limit in positions:
            cands = run("SELECT candID, candFName||' '||candLName FROM candidates "
                        "WHERE posID=? AND candStat=1", (pid,), fetch=True)
            box = ttk.LabelFrame(holder, text=f"{pname} (vote up to {limit})", padding=6)
            box.pack(side="left", fill="both", expand=True, padx=4)
            lb = tk.Listbox(box, selectmode="multiple", exportselection=False, height=12)
            for _, name in cands:
                lb.insert("end", name)
            lb.pack(fill="both", expand=True)
            state = {"last": ()}
            lb.bind("<<ListboxSelect>>", lambda e, lb=lb, lim=limit, st=state, pn=pname:
                    self.enforce_limit(lb, lim, st, pn))
            self.lists[pid] = (lb, [c[0] for c in cands], limit)

        bar = ttk.Frame(self.ballot)
        bar.pack(anchor="e")
        ttk.Button(bar, text="Cancel", command=self.show_login).pack(side="left", padx=4)
        ttk.Button(bar, text="Submit Vote", command=self.submit).pack(side="left", padx=4)

    def enforce_limit(self, lb, limit, state, pname):
        sel = lb.curselection()
        if len(sel) > limit:                       # too many -> undo the last click
            for i in sel:
                if i not in state["last"]:
                    lb.selection_clear(i)
            messagebox.showwarning("Limit reached", f"You can only vote for {limit} {pname}(s).")
        state["last"] = lb.curselection()

    def submit(self):
        picks = []
        for pid, (lb, cand_ids, limit) in self.lists.items():
            chosen = [cand_ids[i] for i in lb.curselection()]
            if len(chosen) > limit:
                return messagebox.showwarning("Too many", "Too many selections.")
            picks += [(pid, self.voter, cid) for cid in chosen]
        if not picks and not messagebox.askyesno("No selection", "Submit an empty ballot?"):
            return
        if not messagebox.askyesno("Confirm", "Submit your vote? You cannot vote again."):
            return
        con = sqlite3.connect(DB)
        try:                                       # one transaction: all or nothing
            con.executemany("INSERT INTO votes (posID, voterID, candID) VALUES (?,?,?)", picks)
            con.execute("UPDATE voters SET voted=1 WHERE voterID=?", (self.voter,))
            con.commit()
        finally:
            con.close()
        messagebox.showinfo("Thank you", "Your vote has been recorded.")
        self.show_login()

    def refresh(self):
        pass


# ----------------------------------------------------------------------
# 4. RESULTS + WINNERS
# ----------------------------------------------------------------------
def get_tally():
    """Returns {posID: {'name':..., 'slots':..., 'cands':[(name, votes), ...]}}"""
    out = {}
    pos = run("SELECT posID, posName, numOfPositions FROM positions WHERE posStat=1 ORDER BY posID", fetch=True)
    for pid, pname, slots in pos:
        rows = run("""SELECT c.candFName||' '||c.candLName, COUNT(v.candID)
                      FROM candidates c
                      LEFT JOIN votes v ON v.candID = c.candID
                      WHERE c.posID=? AND c.candStat=1
                      GROUP BY c.candID
                      ORDER BY COUNT(v.candID) DESC, c.candID""", (pid,), fetch=True)
        out[pid] = {"name": pname, "slots": slots, "cands": rows}
    return out


class ResultsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        cols = ("Candidate", "Total Votes", "Voting %")
        self.tree = ttk.Treeview(self, columns=cols, show="tree headings", height=18)
        self.tree.heading("#0", text="Position")
        self.tree.column("#0", width=200)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("pos", font=("Segoe UI", 10, "bold"))

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for data in get_tally().values():
            total = sum(v for _, v in data["cands"])
            parent = self.tree.insert("", "end", text=data["name"], open=True, tags=("pos",))
            for name, votes in data["cands"]:
                pct = f"{votes / total * 100:.2f}" if total else "0.00"
                self.tree.insert(parent, "end", values=(name, votes, pct))


class WinnersTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        cols = ("Elective Position", "Winner", "Total Votes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=200, anchor="center")
        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for data in get_tally().values():
            # cands is already sorted by votes DESC; take the top N slots
            for name, votes in data["cands"][:data["slots"]]:
                if votes > 0:                       # no votes = no winner
                    self.tree.insert("", "end", values=(data["name"], name, votes))


# ----------------------------------------------------------------------
# 5. MAIN WINDOW
# ----------------------------------------------------------------------
def position_choices():
    return [f"{i} - {n}" for i, n in
            run("SELECT posID, posName FROM positions WHERE posStat=1", fetch=True)]


def main():
    init_db()
    seed_if_empty()

    root = tk.Tk()
    root.title("Election System")
    root.geometry("900x560")

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=6, pady=6)

    tabs = {
        "Positions": CrudTab(nb, "positions", [
            {"col": "posName", "label": "Position Name"},
            {"col": "numOfPositions", "label": "No. of Positions", "kind": "int"},
        ], status_col="posStat", auto_pk="posID"),

        "Candidates": CrudTab(nb, "candidates", [
            {"col": "candFName", "label": "First Name"},
            {"col": "candMName", "label": "Middle Name", "optional": True},
            {"col": "candLName", "label": "Last Name"},
            {"col": "posID", "label": "Position", "kind": "combo", "values": position_choices},
        ], status_col="candStat", auto_pk="candID"),

        "Voters": CrudTab(nb, "voters", [
            {"col": "voterID", "label": "Voter ID", "pk": True},
            {"col": "voterPass", "label": "Password"},
            {"col": "voterFName", "label": "First Name"},
            {"col": "voterMName", "label": "Middle Name", "optional": True},
            {"col": "voterLName", "label": "Last Name"},
        ], status_col="voterStat", extra_cols=["voted"]),

        "Voting": VotingTab(nb),
        "Results": ResultsTab(nb),
        "Winners": WinnersTab(nb),
    }
    for name, frame in tabs.items():
        nb.add(frame, text=name)

    # refresh a tab each time it is opened so data is never stale
    nb.bind("<<NotebookTabChanged>>",
            lambda e: nb.nametowidget(nb.select()).refresh())

    root.mainloop()


if __name__ == "__main__":
    main()