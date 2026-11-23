# 1. Grammar: Non-Terminal -> list of productions (each production is a tuple of symbols)
grammar = {
    'S': [('A', 'A')],
    'A': [('a', 'A'), ('b',)],
}
start_symbol = 'S'
AUGMENTED_START = "S'"

# Augment the grammar: S' -> S
aug_grammar = {AUGMENTED_START: [(start_symbol,)], **grammar}
non_terminals = set(aug_grammar.keys())
terminals = {
    sym
    for prods in aug_grammar.values()
    for prod in prods
    for sym in prod
    if sym not in non_terminals
} | {'$'}


def closure(items):
    """Expands a set of LR(0) items: (lhs, rhs, dot_pos)."""
    items = set(items)
    changed = True
    while changed:
        changed = False
        new_items = set()
        for lhs, rhs, dot in items:
            if dot < len(rhs) and rhs[dot] in non_terminals:
                next_nt = rhs[dot]
                for prod in aug_grammar[next_nt]:
                    item = (next_nt, prod, 0)
                    if item not in items:
                        new_items.add(item)
        if new_items:
            items.update(new_items)
            changed = True
    return frozenset(items)


def goto(items, symbol):
    """Advances the dot over 'symbol' for all matching items and takes closure."""
    moved = {
        (lhs, rhs, dot + 1)
        for lhs, rhs, dot in items
        if dot < len(rhs) and rhs[dot] == symbol
    }
    return closure(moved) if moved else frozenset()


def build_lr0_automaton():
    """Builds the canonical collection of LR(0) states and transitions."""
    start_state = closure({(AUGMENTED_START, (start_symbol,), 0)})
    states = [start_state]
    state_to_id = {start_state: 0}
    transitions = {}  # (state_id, symbol) -> next_state_id

    i = 0
    while i < len(states):
        state = states[i]
        # Collect all symbols immediately after a dot in this state
        next_symbols = {rhs[dot] for _, rhs, dot in state if dot < len(rhs)}

        for sym in next_symbols:
            target = goto(state, sym)
            if target not in state_to_id:
                state_to_id[target] = len(states)
                states.append(target)
            transitions[(i, sym)] = state_to_id[target]
        i += 1

    return states, transitions


def build_lr0_tables(states, transitions):
    """Builds ACTION and GOTO tables from the LR(0) automaton."""
    action = {}  # (state_id, terminal) -> ('SHIFT', j) | ('REDUCE', (lhs, rhs)) | ('ACCEPT',)
    goto_table = {}  # (state_id, non_terminal) -> next_state_id

    def set_action(state_id, term, act):
        if (state_id, term) in action and action[(state_id, term)] != act:
            raise ValueError(
                f"LR(0) Conflict in state {state_id} on '{term}': "
                f"{action[(state_id, term)]} vs {act}"
            )
        action[(state_id, term)] = act

    for state_id, state in enumerate(states):
        for lhs, rhs, dot in state:
            if dot < len(rhs):
                sym = rhs[dot]
                target = transitions[(state_id, sym)]
                if sym in non_terminals:
                    goto_table[(state_id, sym)] = target
                else:
                    set_action(state_id, sym, ('SHIFT', target))
            else:
                # Dot is at the end: ACCEPT or REDUCE
                if lhs == AUGMENTED_START:
                    set_action(state_id, '$', ('ACCEPT',))
                else:
                    # LR(0) reduces on ALL terminals (no lookahead check)
                    for term in terminals:
                        set_action(state_id, term, ('REDUCE', (lhs, rhs)))

    return action, goto_table


def parse(tokens, action, goto_table):
    """Stack-based LR(0) shift-reduce parser."""
    state_stack = [0]
    symbol_stack = []
    inp = tokens + ['$']
    idx = 0

    print(f"{'STATES':<20} {'SYMBOLS':<15} {'INPUT':<18} ACTION")
    print("-" * 72)

    while True:
        state = state_stack[-1]
        lookahead = inp[idx]
        act = action.get((state, lookahead))

        states_str = ' '.join(map(str, state_stack))
        syms_str = ' '.join(symbol_stack)
        inp_str = ' '.join(inp[idx:])

        if act is None:
            print(f"{states_str:<20} {syms_str:<15} {inp_str:<18} ERROR")
            return False

        kind = act[0]
        if kind == 'SHIFT':
            next_state = act[1]
            print(f"{states_str:<20} {syms_str:<15} {inp_str:<18} Shift {next_state}")
            symbol_stack.append(lookahead)
            state_stack.append(next_state)
            idx += 1

        elif kind == 'REDUCE':
            lhs, rhs = act[1]
            print(f"{states_str:<20} {syms_str:<15} {inp_str:<18} Reduce {lhs} -> {' '.join(rhs)}")
            for _ in range(len(rhs)):
                symbol_stack.pop()
                state_stack.pop()
            symbol_stack.append(lhs)
            state_stack.append(goto_table[(state_stack[-1], lhs)])

        elif kind == 'ACCEPT':
            print(f"{states_str:<20} {syms_str:<15} {inp_str:<18} ACCEPT")
            return True


# --- Run the Full Pipeline ---
states, transitions = build_lr0_automaton()
action_table, goto_table = build_lr0_tables(states, transitions)

sample_tokens = ['a', 'b', 'a', 'b']
parse(sample_tokens, action_table, goto_table)