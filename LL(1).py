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


def first_of_sequence(seq, first, non_terminals):
    """Returns FIRST(α) for any sequence of symbols α."""
    result = set()
    for sym in seq:
        if sym == EPSILON:
            continue
        if sym not in non_terminals:  # Terminal
            result.add(sym)
            return result
        result.update(first[sym] - {EPSILON})
        if EPSILON not in first[sym]:
            return result
    result.add(EPSILON)  # All symbols were nullable (or seq was empty)
    return result


def compute_first(grammar):
    non_terminals = set(grammar.keys())
    first = {nt: set() for nt in non_terminals}

    changed = True
    while changed:
        changed = False
        for nt, productions in grammar.items():
            for prod in productions:
                before = len(first[nt])
                first[nt].update(first_of_sequence(prod, first, non_terminals))
                if len(first[nt]) > before:
                    changed = True
    return first


def compute_follow(grammar, first, start):
    non_terminals = set(grammar.keys())
    follow = {nt: set() for nt in non_terminals}
    follow[start].add('$')

    changed = True
    while changed:
        changed = False
        for nt, productions in grammar.items():
            for prod in productions:
                for i, sym in enumerate(prod):
                    if sym not in non_terminals:
                        continue
                    before = len(follow[sym])
                    trailer_first = first_of_sequence(prod[i + 1:], first, non_terminals)
                    follow[sym].update(trailer_first - {EPSILON})
                    if EPSILON in trailer_first:
                        follow[sym].update(follow[nt])
                    if len(follow[sym]) > before:
                        changed = True
    return follow


def build_ll1_table(grammar, first, follow):
    """Builds the LL(1) parsing table as {(non_terminal, terminal): production}."""
    non_terminals = set(grammar.keys())
    table = {}

    def add_entry(nt, terminal, prod):
        if (nt, terminal) in table and table[(nt, terminal)] != prod:
            raise ValueError(
                f"LL(1) Conflict at ({nt}, {terminal}): "
                f"{table[(nt, terminal)]} vs {prod}"
            )
        table[(nt, terminal)] = prod

    for nt, productions in grammar.items():
        for prod in productions:
            prod_first = first_of_sequence(prod, first, non_terminals)
            for terminal in prod_first - {EPSILON}:
                add_entry(nt, terminal, prod)
            if EPSILON in prod_first:
                for terminal in follow[nt]:
                    add_entry(nt, terminal, prod)

    return table


def parse(tokens, table, start, non_terminals):
    """Stack-based LL(1) predictive parser."""
    stack = ['$', start]
    inp = tokens + ['$']
    idx = 0

    print(f"{'STACK':<25} {'INPUT':<25} ACTION")
    print("-" * 70)

    while stack:
        top = stack.pop()
        lookahead = inp[idx]
        stack_str = ' '.join(stack + [top])
        input_str = ' '.join(inp[idx:])

        if top == lookahead == '$':
            print(f"{stack_str:<25} {input_str:<25} ACCEPT")
            return True

        if top not in non_terminals:  # Terminal on top of stack
            if top == lookahead:
                print(f"{stack_str:<25} {input_str:<25} Match '{lookahead}'")
                idx += 1
            else:
                print(f"{stack_str:<25} {input_str:<25} ERROR: expected '{top}', got '{lookahead}'")
                return False
        else:  # Non-terminal on top of stack
            prod = table.get((top, lookahead))
            if prod is None:
                print(f"{stack_str:<25} {input_str:<25} ERROR: no rule for ({top}, '{lookahead}')")
                return False

            print(f"{stack_str:<25} {input_str:<25} {top} -> {' '.join(prod)}")
            if prod != [EPSILON]:
                stack.extend(reversed(prod))  # Push in reverse so leftmost symbol is on top

    return False


# --- Run the Full Pipeline ---
first_sets = compute_first(grammar)
follow_sets = compute_follow(grammar, first_sets, start_symbol)
ll1_table = build_ll1_table(grammar, first_sets, follow_sets)

# Test with tokenized input: id + id * id
sample_tokens = ['id', '+', 'id', '*', 'id']
parse(sample_tokens, ll1_table, start_symbol, set(grammar.keys()))