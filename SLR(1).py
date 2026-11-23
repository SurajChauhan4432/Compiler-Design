# 1. Grammar: Non-Terminal -> list of productions (each production is a tuple of symbols)
# Represent an epsilon production as an empty tuple: ()
grammar = {
    'E': [('E', '+', 'T'), ('T',)],
    'T': [('T', '*', 'F'), ('F',)],
    'F': [('(', 'E', ')'), ('id',)],
}
start_symbol = 'E'
AUGMENTED_START = "S'"

aug_grammar = {AUGMENTED_START: [(start_symbol,)], **grammar}
non_terminals = set(aug_grammar.keys())


# --- Phase 1: FIRST and FOLLOW sets ---
def first_of_sequence(seq, first):
    result = set()
    for sym in seq:
        if sym not in non_terminals:  # Terminal
            result.add(sym)
            return result
        result.update(first[sym] - {''})
        if '' not in first[sym]:
            return result
    result.add('')  # Sequence is nullable
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


def compute_follow(first):
    follow = {nt: set() for nt in non_terminals}
    follow[AUGMENTED_START].add('$')
    changed = True
    while changed:
        changed = False
        for nt, prods in aug_grammar.items():
            for prod in prods:
                for i, sym in enumerate(prod):
                    if sym not in non_terminals:
                        continue
                    before = len(follow[sym])
                    trailer_first = first_of_sequence(prod[i + 1:], first)
                    follow[sym].update(trailer_first - {''})
                    if '' in trailer_first:
                        follow[sym].update(follow[nt])
                    if len(follow[sym]) > before:
                        changed = True
    return follow


# --- Phase 2: LR(0) Automaton ---
def closure(items):
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
    moved = {
        (lhs, rhs, dot + 1)
        for lhs, rhs, dot in items
        if dot < len(rhs) and rhs[dot] == symbol
    }
    return closure(moved) if moved else frozenset()


def build_lr0_automaton():
    start_state = closure({(AUGMENTED_START, (start_symbol,), 0)})
    states = [start_state]
    state_to_id = {start_state: 0}
    transitions = {}

    i = 0
    while i < len(states):
        state = states[i]
        next_symbols = sorted({rhs[dot] for _, rhs, dot in state if dot < len(rhs)})

        for sym in next_symbols:
            target = goto(state, sym)
            if target not in state_to_id:
                state_to_id[target] = len(states)
                states.append(target)
            transitions[(i, sym)] = state_to_id[target]
        i += 1

    return states, transitions


# --- Phase 3: SLR(1) ACTION and GOTO Tables ---
def build_slr1_tables(states, transitions, follow):
    action = {}
    goto_table = {}

    def set_action(state_id, term, act):
        if (state_id, term) in action and action[(state_id, term)] != act:
            raise ValueError(
                f"SLR(1) Conflict in state {state_id} on '{term}': "
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
                if lhs == AUGMENTED_START:
                    set_action(state_id, '$', ('ACCEPT',))
                else:
                    # The ONLY difference from LR(0): reduce only on FOLLOW(lhs)
                    for term in follow[lhs]:
                        set_action(state_id, term, ('REDUCE', (lhs, rhs)))

    return action, goto_table


# --- Phase 4: Shift-Reduce Parser ---
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
follow_sets = compute_follow(first_sets)
states, transitions = build_lr0_automaton()
action_table, goto_table = build_slr1_tables(states, transitions, follow_sets)

sample_tokens = ['id', '+', 'id', '*', 'id']
parse(sample_tokens, action_table, goto_table)