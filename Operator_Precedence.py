# 1. Operator Precedence Table: (top_terminal, lookahead) -> '<', '>', or '='
# '<' (yields to) / '=' (equal) -> SHIFT
# '>' (takes precedence over)   -> REDUCE
PRECEDENCE = {
    ('id', '+'): '>', ('id', '*'): '>', ('id', ')'): '>', ('id', '$'): '>',
    ('+', 'id'): '<', ('+', '+'): '>', ('+', '*'): '<', ('+', '('): '<', ('+', ')'): '>', ('+', '$'): '>',
    ('*', 'id'): '<', ('*', '+'): '>', ('*', '*'): '>', ('*', '('): '<', ('*', ')'): '>', ('*', '$'): '>',
    ('(', 'id'): '<', ('(', '+'): '<', ('(', '*'): '<', ('(', '('): '<', ('(', ')'): '=',
    (')', '+'): '>', (')', '*'): '>', (')', ')'): '>', (')', '$'): '>',
    ('$', 'id'): '<', ('$', '+'): '<', ('$', '*'): '<', ('$', '('): '<',
}

# 2. Valid handles (right-hand sides) that reduce to 'E'
HANDLES = {
    ('id',),
    ('E', '+', 'E'),
    ('E', '*', 'E'),
    ('(', 'E', ')'),
}

TERMINALS = {'id', '+', '*', '(', ')', '$'}


def top_terminal(stack):
    """Returns the topmost terminal symbol on the stack (ignoring non-terminals like 'E')."""
    for sym in reversed(stack):
        if sym in TERMINALS:
            return sym
    return '$'


def reduce_handle(stack):
    """Finds and reduces a valid handle at the top of the stack to 'E'."""
    for length in (3, 1):  # Check 3-symbol handles (E+E, E*E, (E)) before 1-symbol (id)
        if len(stack) >= length:
            candidate = tuple(stack[-length:])
            if candidate in HANDLES:
                del stack[-length:]
                stack.append('E')
                return ' '.join(candidate)
    return None


def parse(tokens):
    stack = ['$']
    inp = tokens + ['$']
    idx = 0

    print(f"{'STACK':<22} {'REL':<5} {'INPUT':<25} ACTION")
    print("-" * 72)

    while True:
        top_t = top_terminal(stack)
        lookahead = inp[idx]
        stack_str = ' '.join(stack)
        input_str = ' '.join(inp[idx:])

        # Accept condition: only $ and start symbol E on stack, and input is at $
        if top_t == '$' and lookahead == '$':
            if stack == ['$', 'E']:
                print(f"{stack_str:<22} {'':<5} {input_str:<25} ACCEPT")
                return True
            print(f"{stack_str:<22} {'':<5} {input_str:<25} ERROR: invalid final stack")
            return False

        rel = PRECEDENCE.get((top_t, lookahead))

        if rel in ('<', '='):
            print(f"{stack_str:<22} {rel:<5} {input_str:<25} Shift '{lookahead}'")
            stack.append(lookahead)
            idx += 1
        elif rel == '>':
            reduced = reduce_handle(stack)
            if reduced is None:
                print(f"{stack_str:<22} {rel:<5} {input_str:<25} ERROR: no valid handle")
                return False
            print(f"{stack_str:<22} {rel:<5} {input_str:<25} Reduce E -> {reduced}")
        else:
            print(f"{stack_str:<22} {'err':<5} {input_str:<25} ERROR: unexpected '{lookahead}' after '{top_t}'")
            return False


# --- Test it ---
sample_tokens = ['id', '+', 'id', '*', 'id']
parse(sample_tokens)