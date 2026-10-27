import sqlite3

DB = "election.db"

def run(sql, params=()):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    rows = cur.fetchall()
    conn.close()
    return rows

def setup_database():
    run("""CREATE TABLE IF NOT EXISTS positions(
        posID INTEGER PRIMARY KEY AUTOINCREMENT,
        posName TEXT NOT NULL,
        numOfPositions INTEGER NOT NULL,
        posStat TEXT NOT NULL DEFAULT 'Active')""")
    run("""CREATE TABLE IF NOT EXISTS candidates(
        candID INTEGER PRIMARY KEY AUTOINCREMENT,
        candFName TEXT NOT NULL,
        candMName TEXT,
        candLName TEXT NOT NULL,
        posID INTEGER NOT NULL,
        candStat TEXT NOT NULL DEFAULT 'Active')""")
    run("""CREATE TABLE IF NOT EXISTS voters(
        voterID TEXT PRIMARY KEY,
        voterPass TEXT NOT NULL,
        voterFName TEXT NOT NULL,
        voterMName TEXT,
        voterLName TEXT NOT NULL,
        voterStat TEXT NOT NULL DEFAULT 'Active')""")
    run("""CREATE TABLE IF NOT EXISTS votes(
        posID INTEGER NOT NULL,
        voterID TEXT NOT NULL,
        candID INTEGER NOT NULL)""")

    columns = {row[1] for row in run ("PRAGMA table_info(voters)")}
    if "voted" not in columns:
        run("ALTER TABLE VOTERS ADD COLUMN voted TEXT NOT NULL DEFAULT 'NO'")
        run("""UPDATE voters SET voted = 'Yes'
               WHERE voterID IN (SELECT voterID FROM votes)""")


import tkinter as tk
from tkinter import ttk, messagebox

# UI HELPERS
def make_table(parent, headings, row):
    table = ttk.Treeview(parent, columns=headings, show="headings", height=10)
    for h in headings:
        table.heading(h, text=h)
        table.column(h, width=100)
    table.grid(row=row, column=0, columnspan=6, padx=10, pady=10)
    return table

def clear_table(table):
    for item in table.get_children():
        table.delete(item)

def fill_table(table, rows):
    clear_table(table)
    for row in rows:
        table.insert("", tk.END, iid=str(row[0]), values=row)

def get_selected(table):
    sel = table.selection()
    if not sel:
        messagebox.showwarning("No selection", "Click a Row First")
        return None
    return sel[0]

# window with tabs
setup_database()
root = tk.Tk()
root.title("Election System")

tabs = ttk.Notebook(root)
tabs.pack(fill="both", expand=True)

tab_pos = ttk.Frame(tabs)
tab_cand = ttk.Frame(tabs)
tab_voter = ttk.Frame(tabs)
tab_vote = ttk.Frame(tabs)
tab_results = ttk.Frame(tabs)
tab_winners = ttk.Frame(tabs)

tabs.add(tab_pos, text="Positions")
tabs.add(tab_cand, text="Candidates")
tabs.add(tab_voter, text="Voters")
tabs.add(tab_vote, text="Vote")
tabs.add(tab_results, text="Results")
tabs.add(tab_winners, text="Winners")


# postions tab
tk.Label(tab_pos, text="Position name").grid(row=0, column=0, padx=5, pady=5)
pos_name = tk.Entry(tab_pos)
pos_name.grid(row=0, column=1)
tk.Label(tab_pos, text="Number of seats").grid(row=1, column=0, padx=5, pady=5)
pos_num = tk.Entry(tab_pos)
pos_num.grid(row=1, column=1)

pos_table = make_table(tab_pos, ("ID", "Position", "Seats", "Status"), row=3)

def pos_refresh():
    fill_table(pos_table, run("SELECT posID, posName, numOfPositions, posStat FROM positions"))

def pos_clear():
    pos_name.delete(0, tk.END)
    pos_num.delete(0, tk.END)

def pos_read_form():
    name = pos_name.get().strip()
    num = pos_num.get().strip()
    if not name or not num.isdigit() or int(num) < 1:
        messagebox.showwarning("Invalid", "Enter a name and a seat count of 1 or more.")
        return None
    return name, int(num)

def pos_add():
    data = pos_read_form()
    if data is None:
        return
    run("INSERT INTO positions (posName, numOfPositions) VALUES (?, ?)", data)
    pos_clear()
    pos_refresh()

def pos_pick(event):
    sel = pos_table.selection()
    if not sel:
        return
    row = run("SELECT posName, numOfPositions FROM positions WHERE posID = ?", (sel[0],))[0]
    pos_clear()
    pos_name.insert(0, row[0])
    pos_num.insert(0, row[1])

def pos_update():
    pid = get_selected(pos_table)
    data = pos_read_form()
    if pid is None or data is None:
        return
    run("UPDATE positions SET posName = ?, numOfPositions = ? WHERE posID = ?", data + (int(pid),))
    pos_clear()
    pos_refresh()

def pos_deactivate():
    pid = get_selected(pos_table)
    if pid is None:
        return
    if messagebox.askyesno("Confirm", "Deactivate This position"):
        run("UPDATE positions SET posStat = 'Inactive' WHERE posID =?", (int(pid),))
        pos_clear()
        pos_refresh()

tk.Button(tab_pos, text="Add", width=10, command=pos_add).grid(row=2, column=0, pady=5)
tk.Button(tab_pos, text="Update", width=10, command=pos_update).grid(row=2, column=1, pady=5)
tk.Button(tab_pos, text="Deactivate", width=10, command=pos_deactivate).grid(row=2, column=2, pady=5)
pos_table.bind("<<TreeviewSelect>>", pos_pick)


# CANDIDATES TAB
tk.Label(tab_cand, text="First name").grid(row=0, column=0, padx=5, pady=5)
cand_first = tk.Entry(tab_cand)
cand_first.grid(row=0, column=1)
tk.Label(tab_cand, text="Middle name").grid(row=1, column=0, padx=5, pady=5)
cand_mid = tk.Entry(tab_cand)
cand_mid.grid(row=1, column=1)
tk.Label(tab_cand, text="Last name").grid(row=0, column=2, padx=5)
cand_last = tk.Entry(tab_cand)
cand_last.grid(row=0, column=3)
tk.Label(tab_cand, text="Position").grid(row=1, column=2, padx=5)
cand_pos = ttk.Combobox(tab_cand, state="readonly")
cand_pos.grid(row=1, column=3)

cand_table = make_table(tab_cand, ("ID", "First", "Middle", "Last", "Position", "Status"), row=3)

def pos_choices():
    rows = run("SELECT posID, posName FROM positions WHERE posStat = 'Active'")
    return [f"{r[0]} - {r[1]}" for r in rows]

def cand_refresh():
    fill_table(cand_table,  run("""
    SELECT c.candID, c.candFName, c.candMName, c.candLName, p.posName, c.candStat
    FROM candidates c JOIN positions p ON p.posID = c.posID"""))

def cand_clear():
    for e in (cand_first, cand_mid, cand_last):
        e.delete(0, tk.END)
    cand_pos.set("")

def cand_read_form():
    first = cand_first.get().strip()
    mid = cand_mid.get().strip()
    last = cand_last.get().strip()
    pos = cand_pos.get()
    if not first or not last or not pos:
        messagebox.showwarning("Invalid", "First name, last name, and position are required.")
        return None
    return first, mid, last, int(pos.split(" - ")[0])

def cand_add():
    data = cand_read_form()
    if data is None:
        return
    run("INSERT INTO candidates (candFName, candMName, candLName, posID) VALUES (?, ?, ?, ?)", data)
    cand_clear()
    cand_refresh()

def cand_pick(event):
    sel = cand_table.selection()
    if not sel:
        return
    r = run(""" SELECT c.candFName, c.candMName, c.candLName, p.posID, p.posName
                FROM candidates c JOIN positions p ON p.posID = c.posID
                WHERE c.candID = ?""", (sel[0],))[0]
    cand_clear()
    cand_first.insert(0, r[0])
    cand_mid.insert(0, r[1] or "")
    cand_last.insert(0, r[2])
    cand_pos.set(f"{r[3]} - {r[4]}")

def cand_update():
    cid = get_selected(cand_table)
    data = cand_read_form()
    if cid is None or data is None:
        return
    run("""UPDATE candidates SET candFName = ?, candMName = ?, candLName = ?, posID = ?
            WHERE candID = ?""", data + (int(cid),))
    cand_clear()
    cand_refresh()

def cand_deactivate():
    cid = get_selected(cand_table)
    if cid is None:
        return
    if messagebox.askyesno("Confirm", "Deactivate this candidate?"):
        run("UPDATE candidates SDET candStat = 'Inactive' WHERE candID =?", (int(cid),))
        cand_clear()
        cand_refresh()

tk.Button(tab_cand, text="Add", width=10, command=cand_add).grid(row=2, column=0, pady=5)
tk.Button(tab_cand, text="Update", width=10, command=cand_update).grid(row=2, column=1, pady=5)
tk.Button(tab_cand, text="Deactivate", width=10, command=cand_deactivate).grid(row=2, column=2, pady=5)
cand_table.bind("<<TreeviewSelect>>", cand_pick)

# VOTERS TAB
tk.Label(tab_voter, text="Voter ID").grid(row=0, column=0, padx=5, pady=5)
voter_id = tk.Entry(tab_voter)
voter_id.grid(row=0, column=1)
tk.Label(tab_voter,text="Password").grid(row=1, column=0, padx=5, pady=5)
voter_pass = tk.Entry(tab_voter, show="*")
voter_pass.grid(row=1, column=1)
tk.Label(tab_voter, text="First name").grid(row=0, column=2, padx=5)
voter_first = tk.Entry(tab_voter)
voter_first.grid(row=0, column=3)
tk.Label(tab_voter, text="Middle name").grid(row=1, column=2, padx=5)
voter_mid = tk.Entry(tab_voter)
voter_mid.grid(row=1, column=3)
tk.Label(tab_voter, text="Last name").grid(row=2, column=2, padx=5, pady=5)
voter_last = tk.Entry(tab_voter)
voter_last.grid(row=2, column=3)

voter_table = make_table(tab_voter, ("ID", "First", "Middle", "Last", "Status", "Voted"), row=4)

def voter_refresh():
    fill_table(voter_table, run(
        "SELECT voterID, voterFName, voterMName, voterLName, voterStat, voted FROM voters"))

def voter_clear():
    for e in (voter_id, voter_pass, voter_first, voter_mid, voter_last):
        e.delete(0, tk.END)

def voter_read_form():
    vid = voter_id.get().strip()
    pw = voter_pass.get()
    first = voter_first.get().strip()
    mid = voter_mid.get().strip()
    last = voter_last.get().strip()
    if not vid or not pw or not first or not last:
        messagebox.showwarning("Invalid", "ID, password, first name, and last name are required.")
        return None
    return vid, pw, first, mid, last

def voter_add():
    data = voter_read_form()
    if data is None:
        return
    try:
        run("""INSERT INTO voters (voterID, voterPass, voterFName, voterMName, voterLName) VALUES (?, ?, ?, ?, ?)""", data)

    except sqlite3.IntegrityError:
        messagebox.showerror("Duplicate", "That voter ID already Exists.")
        return
    voter_clear()
    voter_refresh()

def voter_pick(event):
    sel = voter_table.selection()
    if not sel:
        return
    r = run("""SELECT voterPass, voterFName, voterMName, voterLName FROM voters WHERE voterID = ?""", (sel[0],))[0]
    voter_clear()
    voter_id.insert(0, sel[0])
    voter_pass.insert(0, r[0])
    voter_first.insert(0, r[1])
    voter_mid.insert(0, r[2] or "")
    voter_last.insert(0, r[3])

def voter_update():
    vid = get_selected(voter_table)
    data = voter_read_form()
    if vid is None or data is None:
        return
    # the id itself is not change we only use the selected rows id in where
    run("""UPDATE voters SET voterPass = ?, voterFName = ?, voterMName = ?, voterLName = ?
            WHERE voterID = ?""", data[1:] + (vid,))
    voter_clear()
    voter_refresh()

def voter_deactivate():
    vid = get_selected(voter_table)
    if vid is None:
        return
    if messagebox.askyesno("Confirm", "Deactivate this voter?"):
        run("UPDATE voters SET voterStat = 'Inactive' WHERE voterID =?", (vid,))
        voter_clear()
        voter_refresh()

tk.Button(tab_voter, text="Add", width=10, command=voter_add).grid(row=3, column=0, pady=5)
tk.Button(tab_voter, text="Update", width=10, command=voter_update).grid(row=3, column=1, pady=5)
tk.Button(tab_voter, text="Deactivate", width=10, command=voter_deactivate).grid(row=3, column=2, pady=5)
voter_table.bind("<<TreeviewSelect>>", voter_pick)

# vote tab
tk.Label(tab_vote, text="Voter ID").grid(row=0, column=0, padx=5, pady=5)
login_id = tk.Entry(tab_vote)
login_id.grid(row=0, column=1)
tk.Label(tab_vote, text="Password").grid(row=0, column=2, padx=5)
login_pass = tk.Entry(tab_vote, show="*")
login_pass.grid(row=0, column=3)

ballot_frame = tk.Frame(tab_vote)
ballot_frame.grid(row=1, column=0, columnspan=6, padx=10, pady=10)

current = {"voter" : None}
ballot = []

def vote_login():
    vid = login_id.get().strip()
    pw = login_pass.get()
    rows = run("SELECT voterStat, voted FROM voters WHERE voterID = ? AND voterPass = ?", (vid, pw))
    if not rows:
        messagebox.showerror("Login failed", "Wrong voter ID or password.")
        return
    stat, voted = rows[0]
    if stat != "Active":
        messagebox.showerror("NOT allowed", "This voter is not Active.")
        return
    
    if voted == "Yes":
        messagebox.showerror("Not allowed", "You have already voted.")
        return
    current["voter"] = vid
    build_ballot()

def build_ballot():
    for w in ballot_frame.winfo_children():
        w.destroy()
    ballot.clear()
    positions = run("SELECT posID, posName, numOfPositions FROM positions WHERE posStat = 'Active'")
    for col, (pid, pname, seats) in enumerate(positions):
        box = tk.LabelFrame(ballot_frame, text=f"{pname} (up to {seats})")
        box.grid(row=0, column=col, padx=5, sticky="n")
        lb = tk.Listbox(box, selectmode=tk.MULTIPLE, exportselection=False, width=22, height=12)
        lb.pack(padx=5, pady=5)
        cands = run("""SELECT candID, candFName, candLName FROM candidates
                        WHERE posID = ? AND candStat = 'Active'""",(pid,))
        for c in cands:
            lb.insert(tk.END, f"{c[1]} {c[2]}")
        ballot.append((pid, pname, seats, lb, [c[0] for c in cands]))
        submit_btn.config(state="normal")

def vote_submit():
    if current["voter"] is None:
        return
    picks = []
    for pid, pname, seats, lb, cand_ids in ballot:
        chosen = [cand_ids[i] for i in lb.curselection()]
        if len(chosen) > seats:
            messagebox.showwarning("Too many votes", f"{pname}: you may vote for at most {seats}.")
            return
        for cid in chosen:
            picks.append((pid, current["voter"], cid))
    if not picks:
        messagebox.showwarning("Empty ballot", "Select at least one candidate.")
        return
    if not messagebox.askyesno("Confirm", "Submit your votes? You cannot vote again."):
        return

    conn = sqlite3.connect(DB)
    conn.executemany("INSERT INTO votes (posID, voterID, candID) VALUES (?, ?, ?)", picks)
    conn.execute("UPDATE voters SET voted ='Yes' WHERE voterID =?", (current["voter"],))
    conn.commit()
    conn.close()

    current["voter"] = None
    for w in ballot_frame.winfo_children():
        w.destroy()
    ballot.clear()
    submit_btn.config(state="disabled")
    login_id.delete(0, tk.END)
    login_pass.delete(0, tk.END)
    messagebox.showinfo("Thank you", "your votes were recorded.")

tk.Button(tab_vote, text="Login", width=10, command=vote_login).grid(row=0, column=4, padx=5)
submit_btn = tk.Button(tab_vote, text="Submit Votes", state="disabled", command=vote_submit)
submit_btn.grid(row=2, column=0, columnspan=6, pady=5)

# results TAB
res_table = make_table(tab_results, ("Position / Candidate", "Total Votes", "Voting %"), row=0)
res_table.column("Position / Candidate", width=260)

def results_refresh():
    clear_table(res_table)
    for pid, pname in run("SELECT posID, posName FROM positions WHERE posStat = 'Active'"):
        rows = run("""SELECT c.candFName || ' ' || c.candLName, COUNT(v.candID)
                      FROM candidates c LEFT JOIN votes v ON v.candID = c.candID
                      WHERE c.posID = ? AND c.candStat = 'Active'
                      GROUP BY c.candID
                      ORDER BY COUNT(v.candID) DESC""", (pid,))
        total = sum(r[1] for r in rows)
        res_table.insert("", tk.END, values=(pname, "", ""))
        for name, n in rows:
            pct = (n / total * 100) if total else 0 
            res_table.insert("", tk.END, values=("      " + name, n, f"{pct:.2f}"))
# winners tab
win_table = make_table(tab_winners, ("Elective Position", "Winner", "Tota; Votes"), row=0)
win_table.column("Winner", width=200)

def winners_refresh():
    clear_table(win_table)
    for pid, pname, seats in run(
            "SELECT posID, posName, numOfPositions FROM positions WHERE posStat = 'Active'"):
        rows = run("""SELECT c.candFName || ' ' || c.candLName, COUNT(v.candID)
                      FROM candidates c LEFT JOIN votes v ON v.candID = c.candID
                      WHERE c.posID = ? AND c.candStat = 'Active'
                      GROUP BY c.candID
                      HAVING COUNT(v.candID) > 0
                      ORDER BY COUNT(v.candID) DESC
                      LIMIT ?""", (pid, seats))
        for name, n in rows:
            win_table.insert("", tk.END, values=(pname, name, n))


def refresh_all(event=None):
    pos_refresh()
    cand_pos["values"] = pos_choices()
    cand_refresh()
    voter_refresh()
    results_refresh()
    winners_refresh()

tabs.bind("<<NotebookTabChanged>>", refresh_all)
refresh_all()
root.mainloop()
    



