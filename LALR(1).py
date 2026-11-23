# 1. Grammar: Non-Terminal -> list of productions (each production is a tuple of symbols)
grammar = {
    'S': [('L', '=', 'R'), ('R',)],
    'L': [('*', 'R'), ('id',)],
    'R': [('L',)],
}
start_symbol = 'S'
AUGMENTED_START = "S'"

aug_grammar = {AUGMENTED_START: [(start_symbol,)], **grammar}
non_terminals = set(aug_grammar.keys())


# --- Phase 1: FIRST sets ---
def first_of_sequence(seq, first):
    result = set()
    for sym in seq:
        if sym not in non_terminals:
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


# --- Phase 2: CLR(1) Automaton ---
def closure(items, first):
    items = set(items)
    changed = True
    while changed:
        changed = False
        new_items = set()
        for lhs, rhs, dot, la in items:
            if dot < len(rhs) and rhs[dot] in non_terminals:
                next_nt = rhs[dot]
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


# --- Phase 3: Merge CLR(1) States into LALR(1) States ---
def merge_to_lalr(clr_states, clr_transitions):
    """Merges CLR(1) states that share the exact same LR(0) core."""
    core_to_new_id = {}
    old_to_new = {}
    lalr_states = []

    for old_id, state in enumerate(clr_states):
        # Strip lookaheads to get the LR(0) core
        core = frozenset((lhs, rhs, dot) for lhs, rhs, dot, _ in state)

        if core not in core_to_new_id:
            new_id = len(lalr_states)
            core_to_new_id[core] = new_id
            lalr_states.append(set(state))
        else:
            new_id = core_to_new_id[core]
            lalr_states[new_id].update(state)  # Union the LR(1) items (merging lookaheads)

        old_to_new[old_id] = new_id

    # Remap transitions to the new merged state IDs
    lalr_transitions = {
        (old_to_new[src], sym): old_to_new[dst]
        for (src, sym), dst in clr_transitions.items()
    }

    return [frozenset(s) for s in lalr_states], lalr_transitions


# --- Phase 4: LALR(1) ACTION and GOTO Tables ---
def build_lalr1_tables(states, transitions):
    action = {}
    goto_table = {}

    def set_action(state_id, term, act):
        if (state_id, term) in action and action[(state_id, term)] != act:
            raise ValueError(
                f"LALR(1) Conflict in state {state_id} on '{term}': "
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
                    set_action(state_id, la, ('REDUCE', (lhs, rhs)))

    return action, goto_table


# --- Phase 5: Shift-Reduce Parser (Identical across all LR parsers) ---
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
clr_states, clr_transitions = build_lr1_automaton(first_sets)
lalr_states, lalr_transitions = merge_to_lalr(clr_states, clr_transitions)
action_table, goto_table = build_lalr1_tables(lalr_states, lalr_transitions)

print(f"CLR(1) states: {len(clr_states)}  ->  LALR(1) states: {len(lalr_states)}\n")
sample_tokens = ['*', 'id', '=', 'id']
parse(sample_tokens, action_table, goto_table)