# 1. Grammar: Non-Terminal -> list of productions (each production is a tuple of symbols)
# Represent an epsilon production as an empty tuple: ()
grammar = {
    'S': [('L', '=', 'R'), ('R',)],
    'L': [('*', 'R'), ('id',)],
    'R': [('L',)],
}
start_symbol = 'S'
AUGMENTED_START = "S'"

aug_grammar = {AUGMENTED_START: [(start_symbol,)], **grammar}
non_terminals = set(aug_grammar.keys())


# --- Phase 1: FIRST sets (CLR(1) does not need FOLLOW sets) ---
def first_of_sequence(seq, first):
    result = set()
    for sym in seq:
        if sym not in non_terminals:  # Terminal (including '$')
            result.add(sym)
            return result
        result.update(first[sym] - {''})
        if '' not in first[sym]:
            return result
    result.add('')
    return result


def compute_first():
    first = {nt: set() for nt in non_terminals}
    changed = True
    while changed:
        changed = False
        for nt, prods in aug_grammar.items():
            for prod in prods:
                before = len(first[nt])
                first[nt].update(first_of_sequence(prod, first))
                if len(first[nt]) > before:
                    changed = True
    return first


# --- Phase 2: LR(1) Automaton ---
# An LR(1) item is a 4-tuple: (lhs, rhs, dot_pos, lookahead)
def closure(items, first):
    items = set(items)
    changed = True
    while changed:
        changed = False
        new_items = set()
        for lhs, rhs, dot, la in items:
            if dot < len(rhs) and rhs[dot] in non_terminals:
                next_nt = rhs[dot]
                # Compute FIRST(βa), where β is everything after next_nt and a is la
                lookaheads = first_of_sequence(rhs[dot + 1:] + (la,), first) - {''}
                for prod in aug_grammar[next_nt]:
                    for b in lookaheads:
                        item = (next_nt, prod, 0, b)
                        if item not in items:
                            new_items.add(item)
        if new_items:
            items.update(new_items)
            changed = True
    return frozenset(items)


def goto(items, symbol, first):
    moved = {
        (lhs, rhs, dot + 1, la)
        for lhs, rhs, dot, la in items
        if dot < len(rhs) and rhs[dot] == symbol
    }
    return closure(moved, first) if moved else frozenset()


def build_lr1_automaton(first):
    start_state = closure({(AUGMENTED_START, (start_symbol,), 0, '$')}, first)
    states = [start_state]
    state_to_id = {start_state: 0}
    transitions = {}

    i = 0
    while i < len(states):
        state = states[i]
        next_symbols = sorted({rhs[dot] for _, rhs, dot, _ in state if dot < len(rhs)})

        for sym in next_symbols:
            target = goto(state, sym, first)
            if target not in state_to_id:
                state_to_id[target] = len(states)
                states.append(target)
            transitions[(i, sym)] = state_to_id[target]
        i += 1

    return states, transitions


# --- Phase 3: CLR(1) ACTION and GOTO Tables ---
def build_clr1_tables(states, transitions):
    action = {}
    goto_table = {}

    def set_action(state_id, term, act):
        if (state_id, term) in action and action[(state_id, term)] != act:
            raise ValueError(
                f"CLR(1) Conflict in state {state_id} on '{term}': "
                f"{action[(state_id, term)]} vs {act}"
            )
        action[(state_id, term)] = act

    for state_id, state in enumerate(states):
        for lhs, rhs, dot, la in state:
            if dot < len(rhs):
                sym = rhs[dot]
                target = transitions[(state_id, sym)]
                if sym in non_terminals:
                    goto_table[(state_id, sym)] = target
                else:
                    set_action(state_id, sym, ('SHIFT', target))
            else:
                if lhs == AUGMENTED_START and la == '$':
                    set_action(state_id, '$', ('ACCEPT',))
                else:
                    # Reduce ONLY on this item's exact lookahead 'la'
                    set_action(state_id, la, ('REDUCE', (lhs, rhs)))

    return action, goto_table


# --- Phase 4: Shift-Reduce Parser (Identical to LR(0) & SLR(1)) ---
def parse(tokens, action, goto_table):
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
            rhs_str = ' '.join(rhs) if rhs else 'ε'
            print(f"{states_str:<20} {syms_str:<15} {inp_str:<18} Reduce {lhs} -> {rhs_str}")
            for _ in range(len(rhs)):
                symbol_stack.pop()
                state_stack.pop()
            symbol_stack.append(lhs)
            state_stack.append(goto_table[(state_stack[-1], lhs)])

        elif kind == 'ACCEPT':
            print(f"{states_str:<20} {syms_str:<15} {inp_str:<18} ACCEPT")
            return True


# --- Run the Full Pipeline ---
first_sets = compute_first()
states, transitions = build_lr1_automaton(first_sets)
action_table, goto_table = build_clr1_tables(states, transitions)

print(f"Total CLR(1) states: {len(states)}\n")
sample_tokens = ['*', 'id', '=', 'id']
parse(sample_tokens, action_table, goto_table)