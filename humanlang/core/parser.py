import re

def _starts_block(stripped: str) -> bool:
    """
    Returns True when the line should start a new nested block.
    Covers sync/async tasks, control-flow, classes, and try blocks.
    """
    return (
        stripped.startswith(('if', 'for', 'while', 'define a class', 'try to')) or
        re.match(r'define (an|a) (asynchronous )?task', stripped)
    )

def parse_code(lines):
    """Parses lines of code into a nested block structure."""
    stack = [[]]                      # root list

    for line in lines:
        stripped = line.strip().lower()

        if _starts_block(stripped):
            block = [line]            # head line is element 0
            stack[-1].append(block)   # add to current level
            stack.append(block)       # descend into the new block

        # Keywords that belong to an existing block
        elif stripped.startswith(('else', 'otherwise', 'on error')):
            stack[-1].append(line)

        # Keywords that close a block
        elif stripped.startswith(('end if', 'end for', 'end while',
                                   'end task', 'end class', 'end try')):
            if len(stack) > 1:
                stack.pop()

        # Plain statement
        else:
            stack[-1].append(line)

    return stack[0]