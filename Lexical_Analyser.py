import re

# Keywords in our mini-language
KEYWORDS = {'if', 'else', 'while', 'return', 'int', 'float'}

# 1. Define token rules: (Token Name, Regex Pattern)
# Note: Multi-character operators (==, !=) MUST come before single ones (=, !)
TOKEN_RULES = [
    ('COMMENT',   r'#.*'),                  # Comments starting with #
    ('FLOAT',     r'\d+\.\d+'),             # Decimal numbers (e.g., 3.14)
    ('INT',       r'\d+'),                  # Whole numbers (e.g., 42)
    ('STRING',    r'"[^"]*"'),              # Text inside double quotes
    ('ID',        r'[A-Za-z_][A-Za-z0-9_]*'), # Identifiers & Keywords
    ('OP',        r'==|!=|<=|>=|[+\-*/=<>]'), # Operators
    ('DELIM',     r'[(){};,]'),             # Brackets, semicolons, commas
    ('SKIP',      r'[ \t\n]+'),             # Spaces, tabs, newlines
    ('MISMATCH',  r'.'),                    # Any other single character (error)
]

# 2. Combine all rules into one master regex: (?P<COMMENT>#.*)|(?P<FLOAT>\d+\.\d+)|...
MASTER_REGEX = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_RULES))

def tokenize(source_code):
    tokens = []

    # 3. re.finditer() automatically scans left-to-right and yields each match
    for match in MASTER_REGEX.finditer(source_code):
        kind = match.lastgroup   # Gets the name of the rule that matched
        value = match.group()    # Gets the actual matched text

        if kind == 'SKIP' or kind == 'COMMENT':
            continue
        elif kind == 'ID' and value in KEYWORDS:
            kind = 'KEYWORD'     # Upgrade ID to KEYWORD if it's in our set
        elif kind == 'MISMATCH':
            raise RuntimeError(f"Unexpected character {value!r} at index {match.start()}")

        tokens.append((kind, value))

    return tokens


code = '''
# Calculate bonus
int score = 95;
if (score >= 90.5) {
    return "Pass";
}
'''

for token in tokenize(code):
    print(token)