EPSILON = 'ε'

# Grammar: Non-Terminal -> list of productions (each production is a list of symbols)
grammar = {
    'E':  [['T', "E'"]],
    "E'": [['+', 'T', "E'"], [EPSILON]],
    'T':  [['F', "T'"]],
    "T'": [['*', 'F', "T'"], [EPSILON]],
    'F':  [['(', 'E', ')'], ['id']],
}

start_symbol = 'E'
non_terminals = set(grammar.keys())


def compute_first(grammar):
    first = {nt: set() for nt in non_terminals}

    changed = True
    while changed:
        changed = False
        for nt, productions in grammar.items():
            for prod in productions:
                before = len(first[nt])
                all_nullable = True

                for sym in prod:
                    if sym == EPSILON:
                        continue
                    elif sym not in non_terminals:  # Terminal
                        first[nt].add(sym)
                        all_nullable = False
                        break
                    else:  # Non-terminal
                        first[nt].update(first[sym] - {EPSILON})
                        if EPSILON not in first[sym]:
                            all_nullable = False
                            break

                if all_nullable:
                    first[nt].add(EPSILON)

                if len(first[nt]) > before:
                    changed = True

    return first


def compute_follow(grammar, first, start_symbol):
    follow = {nt: set() for nt in non_terminals}
    follow[start_symbol].add('$')  # End-of-input marker

    changed = True
    while changed:
        changed = False
        for nt, productions in grammar.items():
            for prod in productions:
                for i, sym in enumerate(prod):
                    if sym not in non_terminals:
                        continue

                    before = len(follow[sym])
                    trailer = prod[i + 1:]  # Everything after 'sym'
                    trailer_nullable = True

                    for next_sym in trailer:
                        if next_sym == EPSILON:
                            continue
                        elif next_sym not in non_terminals:  # Terminal
                            follow[sym].add(next_sym)
                            trailer_nullable = False
                            break
                        else:  # Non-terminal
                            follow[sym].update(first[next_sym] - {EPSILON})
                            if EPSILON not in first[next_sym]:
                                trailer_nullable = False
                                break

                    # If nothing follows sym (or everything after it can derive ε)
                    if trailer_nullable:
                        follow[sym].update(follow[nt])

                    if len(follow[sym]) > before:
                        changed = True

    return follow


# --- Run and Display ---
first_sets = compute_first(grammar)
follow_sets = compute_follow(grammar, first_sets, start_symbol)

print("FIRST Sets:")
for nt, s in first_sets.items():
    print(f"  FIRST({nt}) = {s}")

print("\nFOLLOW Sets:")
for nt, s in follow_sets.items():
    print(f"  FOLLOW({nt}) = {s}")