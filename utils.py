import random
import copy


def is_valid(grid, row, col, num):
    for i in range(9):
        if grid[row][i] == num or grid[i][col] == num:
            return False
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(start_row, start_row + 3):
        for c in range(start_col, start_col + 3):
            if grid[r][c] == num:
                return False
    return True


def fill_grid(grid):
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for num in nums:
                    if is_valid(grid, row, col, num):
                        grid[row][col] = num
                        if fill_grid(grid):
                            return True
                        grid[row][col] = 0
                return False
    return True


def remove_cells(grid, cells_to_remove=40):
    removed = 0
    while removed < cells_to_remove:
        row = random.randint(0, 8)
        col = random.randint(0, 8)
        if grid[row][col] != 0:
            grid[row][col] = 0
            removed += 1


def print_board(board):
    for i, row in enumerate(board):
        if i % 3 == 0 and i != 0:
            print("-" * 21)
        for j, val in enumerate(row):
            if j % 3 == 0 and j != 0:
                print("|", end=" ")
            print(val if val != "0" else ".", end=" ")
        print()


def generate_partial_sudoku(empty_cells=40):
    grid = [[0 for _ in range(9)] for _ in range(9)]
    fill_grid(grid)
    puzzle = copy.deepcopy(grid)
    remove_cells(puzzle, empty_cells)
    return puzzle


def isValidSudoku(board):
    def is_valid_row(board):
        for row in board:
            if not is_valid(row):
                return False
        return True

    def is_valid_column(board):
        for col in zip(*board):
            if not is_valid(col):
                return False
        return True

    def is_valid_square(board):
        for i in (0, 3, 6):
            for j in (0, 3, 6):
                square = [board[x][y] for x in range(i, i + 3) for y in range(j, j + 3)]
                if not is_valid(square):
                    return False
        return True

    def is_valid(value):
        res = [i for i in value if i != 0]
        return len(res) == len(set(res))

    return is_valid_row(board) and is_valid_column(board) and is_valid_square(board)
