import pymysql

CONFIG = {"host": "localhost", "user": "root", "password": "Election123", "database": "election"}

def connect():
    return pymysql.connect(**CONFIG)

def run(sql, params=()):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.fetchall
    finally:
        conn.close()

# Positions
def get_positions(active_only=False):
    sql = "SELECT posID, posName, numOfPositions, posStat FROM positions"
    if active_only:
        sql += " WHERE posStat = 'Active'"
    return run(sql)

def add_position(name, seats):
    run("INSERT INTO positions (posName, numOfPositions) VALUES (%s, %s)", (name, seats))

def update_position_status(pos_id, name, seats):
    run("UPDATE positions SET posName = %s, numOfPositions = %s WHERE posID = %s",
        (name, seats, pos_id))

def set_position_status(pos_id, status):
    run("UPDATE positions SET posStat = %s WHERE posID = %s", (status, pos_id))

# candidates
def get_candidates():
    return run("""SELECT c.candID, c.candFName, c.candMName, c.candLName, p.posName, c.candStat
                FROM candidates c JOIN positions p ON p.posID = c.posID""")
def get_candidate(cand_id):
    return run("""SELECT c.candFName, c.candMName, c.candLName, p.posID, p.posName
                FROM candidates c JOIN positions p ON p.posID = c.posID
                WHERE c.candID = %s""", (cand_id,))[0]

def get_candidates_for_position(pos_id):
    return run("""SELECT candID, candFName, candLName FROM candidates
                  WHERE posID = %s AND candStat = 'Acitve'""", (pos_id))

def add_candidate(first, mid, last, pos_id):
    run("""INSERT INTO candidates (candFName, candMName, candLName, posID)
           VALUES (%s, %s, %s, %s)""", (first, mid, last, pos_id))

def update_candidate(cand_id, first, mid, last, pos_id):
    run("""UPDATE candidates SET candFName = %s, candMName = %s, candLName = %s, posID = %s
           WHERE candID = %s""", (first, mid, last, pos_id, cand_id))

def set_candidate_status(cand_id, status):
    run("UPDATE candidates SET candStat = %s WHERE candID = %s", (status, cand_id))

# voters
def get_voters():
    return run("""SELECT voterID, voterFName, voterMName, voterLName, voterStat, voted
                  FROM voters""")
    
def get_voter(voter_id):
    return run("""SELECT voterPass, voterFName, voterMName, voterLName
                  FROM voters WHERE voterID = %s""", (voter_id))[0]

def add_voter(voter_id, password, first, mid, last):
    # raiises pymysql.err.integrityerror if the id already exists
    run("""INSERT INTO voters (voterID, voterPass, voterFName, voterMName, voterLName
           VALUES (%s, %s, %s, %s, %s)""", (voter_id, password, first, mid, last))

def update_voter(voter_id, password, first, mid, last):
    run("""UPDATE voters SET voterPass = %s, voterFName = %s, voterMName = %s, voterLName = %s
           WHERE voterID = %s""", (password, first, mid, last, voter_id))

def set_voter_status(voter_id, status):
    run("UPDATE voters SET voterStat = %s WHERE voterID = %s", (status, voter_id))

# voting

def check_login(voter_id, password):
    """Returns None if the voter may vote, otherwise an error message."""
    rows = run("SELECT voterStat, voted FROM voters WHERE voterID = %s AND voterPass = %s",
               (voter_id, password))
    if not rows:
        return "Wrong voter ID or password."
    stat, voted = rows[0]
    if stat != "Active":
        return "This voter is not active."
    if voted == "Yes":
        return "You have already voted"
    return None

def submit_votes(voter_id, picks):
    """picks = {posID: [candID, ...]}. Returns None on success, else an error message."""
    seats = {r[0]: r[1] for r in get_positions(active_only=True)}
    total = 0
    for pos_id, cand_ids in picks.items():
        if pos_id not in seats:
            return "Invalid position."
        if len(cand_ids) > seats[pos_id]:
            return f"Too many votes for position {pos_id}. Maximum is {seats[pos_id]}."
        total += len(cand_ids)
    if total == 0:
        return "Select at least one candidate."

    conn = connect()
    try:
        cur = conn.cursor()
        # only succeeds if the voter is active AND haas not voted yet
        cur.execute("""UPDATE voters SET voted = 'Yes'
                       WHERE voterID = %s AND voted = 'No' AND voterStat = 'Active'""",
                    (voter_id,))
        if cur.rowcount == 0:
            conn.rollback()
            return "You are not allowed to vote."
        for pos_id, cand_ids in picks.items():
            for cand_id in cand_ids:
                cur.execute("INSERT INTO votes (posID, voterID, candID) VALUES (%s, %s, %s)",
                            (pos_id, voter_id, cand_id)) 
            conn.commit()
            return None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# results  
def get_results():
    """Return [(posName, seats, [(candidateName, votesm percent), ...]), ...]"""
    results = []
    for pos_id, pos_name, seats, stat in get_positions(active_only=True):
        rows = run("""SELECT CONCAT(c.candFName, ' ', c.candLName), COUNT(v.candID)
                      FROM candidates c LEFT JOIN votes v ON v.candID = c.candID
                      WHERE c.posID = %s AND c.candStat = 'Active'
                      GROUP BY c.candID, c.candFName, c.candLName
                      ORDER BY COUNT(v.candID) DESC""", (pos_id,))
        total = sum(n for name, n in rows)
        results.append((pos_name, seats,
                        [(name, n, (n / total * 100) if total else 0) for name, n in rows]))
    return results

def get_winners():
    """Return [(posName, candidateName, votes), ...] highest votes first per position."""
    winners = []
    for pos_name, seats, rows in get_results():
        for name, n, pct in rows[:seats]:
            if n > 0:
                winners.append((pos_name, name, n))
    return winners