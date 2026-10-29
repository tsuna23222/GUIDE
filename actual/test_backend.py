import actual.backend as backend

print(backend.get_positions())
print(backend.check_login("V001", "wrong"))                   # error message
print(backend.check_login("V001", "pass1"))                   # None = allowed
print(backend.submit_votes("V001", {1: [1], 2: [3], 3: [5, 6]}))   # None = saved
print(backend.check_login("V001", "pass1"))                   # "You have already voted."
print(backend.submit_votes("V002", {3: [5, 6, 7, 8]}))        # too many votes
print(backend.get_results())
print(backend.get_winners())