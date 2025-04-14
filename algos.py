import random

solvers = {}


def register_solver(name):
    def wrapper(func):
        solvers[name] = func
        return func

    return wrapper


def find_empty_cell(grid):
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                return row, col
    return None


def is_valid(grid, row, col, num, stats=None):
    if stats:
        for i in range(9):
            stats.check_constraint()
            if grid[row][i] == num or grid[i][col] == num:
                return False
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                stats.check_constraint()
                if grid[r][c] == num:
                    return False
    else:
        for i in range(9):
            if grid[row][i] == num or grid[i][col] == num:
                return False
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                if grid[r][c] == num:
                    return False
    return True


@register_solver("Backtracking Solver")
def solve_backtracking(grid, stats=None):
    if stats:
        stats.enter_call()
    empty = find_empty_cell(grid)
    if not empty:
        if stats:
            stats.exit_call()
        return True  # Puzzle solved
    row, col = empty
    for num in range(1, 10):
        if is_valid(grid, row, col, num, stats):
            grid[row][col] = num
            if solve_backtracking(grid, stats):
                if stats:
                    stats.exit_call()
                return True
            grid[row][col] = 0  # Backtrack
    if stats:
        stats.exit_call()
    return False


rows = cols = range(9)
digits = set(range(1, 10))
cells = [(r, c) for r in rows for c in cols]


# Build peers for each cell
def build_peers():
    peers = {}
    for r, c in cells:
        row_peers = {(r, j) for j in cols if j != c}
        col_peers = {(i, c) for i in rows if i != r}
        block_peers = {
            (i, j)
            for i in range(r // 3 * 3, r // 3 * 3 + 3)
            for j in range(c // 3 * 3, c // 3 * 3 + 3)
            if (i, j) != (r, c)
        }
        peers[(r, c)] = row_peers | col_peers | block_peers
    return peers


PEERS = build_peers()


def solve_constraint_propagation(grid, stats=None, use_mrv=False):
    def initialize_domains(grid):
        domains = {cell: set(digits) for cell in cells}
        for r in rows:
            for c in cols:
                val = grid[r][c]
                if val != 0:
                    if not assign(domains, (r, c), val):
                        return None
        return domains

    def assign(domains, cell, value):
        """Assign a value and propagate constraints. Return False if contradiction."""
        other_vals = domains[cell] - {value}
        for val in other_vals:
            if not eliminate(domains, cell, val):
                return False
        return True

    def eliminate(domains, cell, value):
        """Eliminate value from cell's domain, propagate if needed."""
        if value not in domains[cell]:
            return True  # Already gone

        domains[cell].remove(value)
        if stats:
            stats.check_constraint()

        # If no possible values → contradiction
        if len(domains[cell]) == 0:
            return False

        # If only one value remains → eliminate from peers
        elif len(domains[cell]) == 1:
            v = next(iter(domains[cell]))
            for peer in PEERS[cell]:
                if not eliminate(domains, peer, v):
                    return False

        # If a value can only go in one place in a unit → assign it
        for unit in get_units(cell):
            places = [c for c in unit if value in domains[c]]
            if len(places) == 0:
                return False
            elif len(places) == 1:
                if not assign(domains, places[0], value):
                    return False
        return True

    def get_units(cell):
        r, c = cell
        row_unit = [(r, j) for j in cols]
        col_unit = [(i, c) for i in rows]
        block_unit = [
            (i, j)
            for i in range(r // 3 * 3, r // 3 * 3 + 3)
            for j in range(c // 3 * 3, c // 3 * 3 + 3)
        ]
        return [row_unit, col_unit, block_unit]

    def backtrack(domains, use_mrv=False):
        if stats:
            stats.enter_call()

        # Finished
        if all(len(domains[cell]) == 1 for cell in cells):
            if stats:
                stats.exit_call()
            return domains

        # --- Variable selection ---
        unassigned = [c for c in cells if len(domains[c]) > 1]
        if use_mrv:
            cell = min(unassigned, key=lambda c: len(domains[c]))
        else:
            cell = random.choice(unassigned)

        for val in sorted(domains[cell]):
            new_domains = {c: set(domains[c]) for c in cells}
            if assign(new_domains, cell, val):
                result = backtrack(new_domains, use_mrv)
                if result:
                    if stats:
                        stats.exit_call()
                    return result

        if stats:
            stats.exit_call()
        return None

    domains = initialize_domains(grid)
    if not domains:
        return False

    result = backtrack(domains, use_mrv)
    if not result:
        return False

    # Fill grid with solution
    for (r, c), valset in result.items():
        grid[r][c] = next(iter(valset))
    return True


@register_solver("Constraint Propagation + MRV")
def solver_mrv(grid, stats=None):
    return solve_constraint_propagation(grid, stats=stats, use_mrv=True)


@register_solver("Constraint Propagation + Random")
def solver_random(grid, stats=None):
    return solve_constraint_propagation(grid, stats=stats, use_mrv=False)
