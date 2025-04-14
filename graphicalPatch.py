import pygame
import sys
import time
import random
import copy
from algos import solvers
from utils import generate_partial_sudoku

# Initialize pygame
pygame.init()

WIDTH, HEIGHT = 540, 800
GRID_SIZE = 9
CELL_SIZE = 54
MARGIN = 20
GRID_TOP_MARGIN = 60
GRID_BOTTOM_MARGIN = 200
BUTTON_HEIGHT = 40
BUTTON_MARGIN = 10
SLIDER_HEIGHT = 20
ANIMATION_DELAY_MIN = 0.001  # Fastest
ANIMATION_DELAY_MAX = 0.5  # Slowest
ANIMATION_DELAY_DEFAULT = 0.05

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (230, 230, 230)
HIGHLIGHT = (240, 240, 150)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 0, 139)
SLIDER_BG = (200, 200, 200)
SLIDER_FG = (100, 100, 200)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sudoku Solver Visualizer")

# Fonts
font = pygame.font.SysFont("comicsans", 30)
small_font = pygame.font.SysFont("comicsans", 20)
title_font = pygame.font.SysFont("comicsans", 40)


class SpeedSlider:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.handle_radius = height
        self.handle_x = x + width // 2
        self.min_x = x + self.handle_radius
        self.max_x = x + width - self.handle_radius
        self.dragging = False

    def draw(self):
        # Draw slider background
        pygame.draw.rect(screen, SLIDER_BG, self.rect, 0, 5)
        pygame.draw.rect(screen, BLACK, self.rect, 2, 5)

        # Draw handle
        pygame.draw.circle(
            screen, SLIDER_FG, (self.handle_x, self.rect.centery), self.handle_radius
        )
        pygame.draw.circle(
            screen, BLACK, (self.handle_x, self.rect.centery), self.handle_radius, 2
        )

        # Draw labels
        fast_label = small_font.render("Slow", True, BLACK)
        slow_label = small_font.render("Fast", True, BLACK)
        screen.blit(fast_label, (self.min_x - 20, self.rect.y - 25))
        screen.blit(slow_label, (self.max_x - 20, self.rect.y - 25))

        # Draw current value
        value_label = small_font.render("Animation Speed", True, BLACK)
        screen.blit(
            value_label,
            (self.rect.centerx - value_label.get_width() // 2, self.rect.y - 25),
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                # Move handle to click position
                self.handle_x = max(self.min_x, min(event.pos[0], self.max_x))

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.handle_x = max(self.min_x, min(event.pos[0], self.max_x))

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

    def get_value(self):
        handle_pos_normalized = (self.handle_x - self.min_x) / (self.max_x - self.min_x)
        value = ANIMATION_DELAY_MAX - handle_pos_normalized * (
            ANIMATION_DELAY_MAX - ANIMATION_DELAY_MIN
        )
        return value


class SolverVisualizer:
    def __init__(self):
        self.grid = None
        self.stopped = False
        self.original_grid = None
        self.solving = False
        self.interrupt_solving = False
        self.solved = False
        self.current_solver = None
        self.highlighted_cell = None
        self.highlighted_constraints = []
        self.solver_buttons = []
        self.generate_buttons = []
        self.create_buttons()
        self.generate_new_puzzle(40)

        # Create speed slider
        grid_bottom = GRID_TOP_MARGIN + GRID_SIZE * CELL_SIZE
        slider_width = WIDTH - 2 * MARGIN - 40
        slider_y_pos = (
            grid_bottom + 3 * (BUTTON_HEIGHT + BUTTON_MARGIN) + 60
        )  # Adjusted position
        self.speed_slider = SpeedSlider(
            MARGIN + 20,
            slider_y_pos,
            slider_width,
            SLIDER_HEIGHT,
        )
        self.animation_delay = ANIMATION_DELAY_DEFAULT

    def delay_with_events(self, seconds):
        end_time = time.time() + seconds
        while time.time() < end_time:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    reset_rect, _ = self.reset_button
                    if reset_rect.collidepoint(event.pos) and self.solving:
                        self.interrupt_solving = True
                        return
                self.speed_slider.handle_event(event)

            pygame.event.pump()
            time.sleep(0.01)  # chunked delay

    def create_buttons(self):
        grid_bottom = GRID_TOP_MARGIN + GRID_SIZE * CELL_SIZE

        solver_y_pos = grid_bottom + 40
        button_width = (WIDTH - 2 * MARGIN) // len(solvers)

        for i, solver_name in enumerate(solvers.keys()):
            button_rect = pygame.Rect(
                MARGIN + i * button_width,
                solver_y_pos,
                button_width - BUTTON_MARGIN,
                BUTTON_HEIGHT,
            )
            self.solver_buttons.append((button_rect, solver_name))

        difficulty_y_pos = solver_y_pos + BUTTON_HEIGHT + BUTTON_MARGIN
        difficulties = [("Easy", 30), ("Medium", 40), ("Hard", 50), ("Expert", 60)]
        button_width = (WIDTH - 2 * MARGIN) // len(difficulties)

        for i, (diff_name, empty_cells) in enumerate(difficulties):
            button_rect = pygame.Rect(
                MARGIN + i * button_width,
                difficulty_y_pos,
                button_width - BUTTON_MARGIN,
                BUTTON_HEIGHT,
            )
            self.generate_buttons.append((button_rect, diff_name, empty_cells))

        reset_button_rect = pygame.Rect(
            MARGIN,
            difficulty_y_pos + BUTTON_HEIGHT + BUTTON_MARGIN,
            WIDTH - 2 * MARGIN,
            BUTTON_HEIGHT,
        )
        self.reset_button = (reset_button_rect, "Reset")

    def generate_new_puzzle(self, empty_cells):
        self.grid = generate_partial_sudoku(empty_cells=empty_cells)
        self.original_grid = copy.deepcopy(self.grid)
        self.solving = False
        self.solved = False
        self.stopped = False
        self.highlighted_cell = None
        self.highlighted_constraints = []

    def draw_grid(self):
        # Draw background
        screen.fill(WHITE)

        # Draw title
        title = title_font.render("Sudoku Solver Visualizer", True, DARK_BLUE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 10))

        # Draw grid background
        grid_width = GRID_SIZE * CELL_SIZE
        grid_rect = pygame.Rect(
            (WIDTH - grid_width) // 2,  # Center the grid horizontally
            GRID_TOP_MARGIN,
            grid_width,
            grid_width,
        )
        pygame.draw.rect(screen, LIGHT_GRAY, grid_rect)

        # Draw cells
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cell_rect = pygame.Rect(
                    (WIDTH - grid_width) // 2 + col * CELL_SIZE,
                    GRID_TOP_MARGIN + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )

                # Highlight current cell being processed
                if self.highlighted_cell == (row, col):
                    pygame.draw.rect(screen, HIGHLIGHT, cell_rect)
                # Highlight constraint cells
                elif (row, col) in self.highlighted_constraints:
                    pygame.draw.rect(
                        screen, (255, 200, 200), cell_rect
                    )  # Light red for constraints
                elif self.original_grid[row][col] == 0 and self.grid[row][col] != 0:
                    # Highlight filled cells
                    pygame.draw.rect(screen, LIGHT_BLUE, cell_rect)
                else:
                    pygame.draw.rect(screen, WHITE, cell_rect)

                pygame.draw.rect(screen, GRAY, cell_rect, 1)

                # Draw cell value
                if self.grid[row][col] != 0:
                    color = BLACK if self.original_grid[row][col] != 0 else BLUE
                    value = font.render(str(self.grid[row][col]), True, color)
                    screen.blit(
                        value,
                        (
                            cell_rect.centerx - value.get_width() // 2,
                            cell_rect.centery - value.get_height() // 2,
                        ),
                    )

        for i in range(4):
            line_width = 3 if i % 3 == 0 else 1
            pygame.draw.line(
                screen,
                BLACK,
                ((WIDTH - grid_width) // 2 + i * CELL_SIZE * 3, GRID_TOP_MARGIN),
                (
                    (WIDTH - grid_width) // 2 + i * CELL_SIZE * 3,
                    GRID_TOP_MARGIN + grid_width,
                ),
                line_width,
            )
            pygame.draw.line(
                screen,
                BLACK,
                ((WIDTH - grid_width) // 2, GRID_TOP_MARGIN + i * CELL_SIZE * 3),
                (
                    (WIDTH - grid_width) // 2 + grid_width,
                    GRID_TOP_MARGIN + i * CELL_SIZE * 3,
                ),
                line_width,
            )

    def draw_buttons(self):
        # Draw solver buttons
        for rect, name in self.solver_buttons:
            color = (
                GREEN if self.current_solver == name and self.solving else LIGHT_BLUE
            )
            pygame.draw.rect(screen, color, rect, 0, 5)
            pygame.draw.rect(screen, BLACK, rect, 2, 5)

            short_name = name
            if "Constraint Propagation" in name:
                short_name = name.replace("Constraint Propagation", "CP")

            text = small_font.render(short_name, True, BLACK)
            screen.blit(
                text,
                (
                    rect.centerx - text.get_width() // 2,
                    rect.centery - text.get_height() // 2,
                ),
            )

        # Draw difficulty buttons
        for rect, name, _ in self.generate_buttons:
            pygame.draw.rect(screen, LIGHT_BLUE, rect, 0, 5)
            pygame.draw.rect(screen, BLACK, rect, 2, 5)

            text = small_font.render(name, True, BLACK)
            screen.blit(
                text,
                (
                    rect.centerx - text.get_width() // 2,
                    rect.centery - text.get_height() // 2,
                ),
            )

        # Draw reset button
        reset_rect, label = self.reset_button
        pygame.draw.rect(screen, RED if self.solving else GRAY, reset_rect, 0, 5)
        pygame.draw.rect(screen, BLACK, reset_rect, 2, 5)

        text = small_font.render(label, True, WHITE)
        screen.blit(
            text,
            (
                reset_rect.centerx - text.get_width() // 2,
                reset_rect.centery - text.get_height() // 2,
            ),
        )

        # Draw status
        grid_bottom = GRID_TOP_MARGIN + GRID_SIZE * CELL_SIZE
        status_text = (
            "Solved!"
            if self.solved
            else "Stopped!"
            if self.stopped
            else "Solving..."
            if self.solving
            else "Select a solver"
        )

        status_color = GREEN if self.solved else RED if self.stopped else BLUE
        status = font.render(status_text, True, status_color)

        status_y_pos = grid_bottom + 10
        screen.blit(status, (WIDTH // 2 - status.get_width() // 2, status_y_pos))

        self.speed_slider.draw()

    def handle_click(self, pos):
        reset_rect, _ = self.reset_button
        if reset_rect.collidepoint(pos):
            if self.solving:
                self.interrupt_solving = True
                self.stopped = True
            else:
                self.grid = copy.deepcopy(self.original_grid)
                self.stopped = False

            self.solving = False
            self.solved = False
            return

        if self.solving:
            return

        for rect, name in self.solver_buttons:
            if rect.collidepoint(pos):
                self.current_solver = name
                self.solving = True
                self.solved = False
                self.grid = copy.deepcopy(self.original_grid)
                return

        for rect, _, empty_cells in self.generate_buttons:
            if rect.collidepoint(pos):
                self.generate_new_puzzle(empty_cells)
                return

    class VisualizationStats:
        def __init__(self, visualizer):
            self.visualizer = visualizer
            self.recursive_calls = 0
            self.constraint_checks = 0
            self.current_depth = 0
            self.animation_delay = ANIMATION_DELAY_DEFAULT
            self.max_depth = 0

        def enter_call(self):
            self.recursive_calls += 1
            self.current_depth += 1
            self.max_depth = max(self.max_depth, self.current_depth)

            self.visualizer.draw()
            pygame.display.update()
            self.delay_with_events(self.animation_delay)

        def exit_call(self):
            self.current_depth -= 1

        def check_constraint(self):
            self.constraint_checks += 1

        def delay_with_events(self, seconds):
            return self.visualizer.delay_with_events(seconds)

    def solve_with_animation(self):
        self.interrupt_solving = False
        self.stopped = False
        self.animation_delay = self.speed_slider.get_value()
        solver_func = solvers[self.current_solver]
        grid_copy = copy.deepcopy(self.grid)

        import algos

        original_find_empty = algos.find_empty_cell
        original_is_valid = algos.is_valid

        def find_empty_with_visual(grid):
            if self.interrupt_solving:
                return None
            for row in range(9):
                for col in range(9):
                    if grid[row][col] == 0:
                        self.highlighted_cell = (row, col)
                        self.grid = copy.deepcopy(grid)
                        self.draw()
                        pygame.display.update()
                        self.delay_with_events(self.animation_delay)
                        # Check if we should interrupt after delay
                        if self.interrupt_solving:
                            return None
                        return row, col
            return None

        # Patch for constraint checking visualization
        def is_valid_with_visual(grid, row, col, num, stats=None):
            self.highlighted_cell = (row, col)
            self.highlighted_constraints = []

            for i in range(9):
                if grid[row][i] == num:
                    self.highlighted_constraints.append((row, i))
                    self.draw()
                    pygame.display.update()
                    self.delay_with_events(self.animation_delay)
                    return False
                if grid[i][col] == num:
                    self.highlighted_constraints.append((i, col))
                    self.draw()
                    pygame.display.update()
                    self.delay_with_events(self.animation_delay)
                    return False

            # Check 3x3 box
            start_row, start_col = 3 * (row // 3), 3 * (col // 3)
            for r in range(start_row, start_row + 3):
                for c in range(start_col, start_col + 3):
                    if grid[r][c] == num:
                        self.highlighted_constraints.append((r, c))
                        self.draw()
                        pygame.display.update()
                        self.delay_with_events(self.animation_delay)
                        return False

            # Valid placement
            self.draw()
            pygame.display.update()
            self.delay_with_events(
                self.animation_delay * 0.5
            )  # Shorter delay for valid
            self.highlighted_constraints = []
            return True

        # Apply common patches
        algos.find_empty_cell = find_empty_with_visual
        algos.is_valid = is_valid_with_visual

        stats = self.VisualizationStats(self)

        if "Constraint Propagation" in self.current_solver:
            # Create a custom version of solve_constraint_propagation with visualization hooks
            def solve_cp_with_visualization(grid, stats, use_mrv=False):
                def initialize_domains(grid):
                    domains = {
                        (r, c): set(range(1, 10)) for r in range(9) for c in range(9)
                    }
                    for r in range(9):
                        for c in range(9):
                            val = grid[r][c]
                            if val != 0:
                                if not assign(domains, (r, c), val):
                                    return None
                    return domains

                def assign(domains, cell, value):
                    """Assign a value and propagate constraints. Return False if contradiction."""
                    self.highlighted_cell = cell
                    self.draw()
                    pygame.display.update()
                    self.delay_with_events(self.animation_delay)
                    if self.interrupt_solving:
                        return False

                    other_vals = domains[cell] - {value}
                    for val in other_vals:
                        if not eliminate(domains, cell, val):
                            return False

                    update_grid_from_domains(domains)
                    return True

                def eliminate(domains, cell, value):
                    """Eliminate value from cell's domain, propagate if needed."""
                    self.highlighted_cell = cell
                    self.highlighted_constraints = []

                    if value not in domains[cell]:
                        return True  # Already gone

                    domains[cell].remove(value)
                    if stats:
                        stats.check_constraint()

                    # Show peers when eliminating values
                    for peer in algos.PEERS[cell]:
                        if value in domains[peer]:
                            self.highlighted_constraints.append(peer)

                    self.draw()
                    pygame.display.update()
                    self.delay_with_events(
                        self.animation_delay
                    )  # Shorter delay for eliminate

                    if self.interrupt_solving:
                        return False

                    if len(domains[cell]) == 0:
                        return False

                    elif len(domains[cell]) == 1:
                        v = next(iter(domains[cell]))
                        for peer in algos.PEERS[cell]:
                            if not eliminate(domains, peer, v):
                                return False

                    for unit in get_units(cell):
                        places = [c for c in unit if value in domains[c]]
                        if len(places) == 0:
                            return False
                        elif len(places) == 1:
                            if not assign(domains, places[0], value):
                                return False

                    # Update the visual grid based on domains
                    update_grid_from_domains(domains)
                    return True

                def get_units(cell):
                    r, c = cell
                    row_unit = [(r, j) for j in range(9)]
                    col_unit = [(i, c) for i in range(9)]
                    block_unit = [
                        (i, j)
                        for i in range(r // 3 * 3, r // 3 * 3 + 3)
                        for j in range(c // 3 * 3, c // 3 * 3 + 3)
                    ]
                    return [row_unit, col_unit, block_unit]

                def update_grid_from_domains(domains):
                    grid_view = [[0 for _ in range(9)] for _ in range(9)]
                    for r in range(9):
                        for c in range(9):
                            # If cell has only one possible value, show it
                            if len(domains[(r, c)]) == 1:
                                grid_view[r][c] = next(iter(domains[(r, c)]))
                            elif self.original_grid[r][c] != 0:
                                grid_view[r][c] = self.original_grid[r][c]

                    self.grid = grid_view

                def backtrack(domains, use_mrv=False):
                    if stats:
                        stats.enter_call()

                    # Visualization for backtrack
                    self.draw()
                    pygame.display.update()
                    self.delay_with_events(self.animation_delay)

                    if self.interrupt_solving:
                        if stats:
                            stats.exit_call()
                        return None

                    # Finished
                    if all(len(domains[cell]) == 1 for cell in domains):
                        if stats:
                            stats.exit_call()
                        return domains

                    unassigned = [c for c in domains if len(domains[c]) > 1]
                    if use_mrv:
                        cell = min(unassigned, key=lambda c: len(domains[c]))
                    else:
                        cell = random.choice(unassigned)

                    # Highlight the cell being explored
                    self.highlighted_cell = cell
                    self.draw()
                    pygame.display.update()
                    self.delay_with_events(self.animation_delay)

                    for val in sorted(domains[cell]):
                        new_domains = {c: set(domains[c]) for c in domains}
                        if assign(new_domains, cell, val):
                            result = backtrack(new_domains, use_mrv)
                            if result:
                                if stats:
                                    stats.exit_call()
                                return result

                    if stats:
                        stats.exit_call()
                    return None

                # Start the CP solver with visualization
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

            use_mrv = "MRV" in self.current_solver
            solved = solve_cp_with_visualization(grid_copy, stats, use_mrv)
        else:
            solved = solver_func(grid_copy, stats)

        algos.find_empty_cell = original_find_empty
        algos.is_valid = original_is_valid

        if solved:
            self.grid = grid_copy
            self.solved = True
        self.solving = False
        self.highlighted_cell = None
        self.highlighted_constraints = []
        if self.interrupt_solving:
            self.solving = False
            self.highlighted_cell = None
            self.highlighted_constraints = []
            self.interrupt_solving = False
            return

    def draw(self):
        self.draw_grid()
        self.draw_buttons()

    def run(self):
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

                # Handle slider events
                self.speed_slider.handle_event(event)

            if self.solving and not self.solved:
                self.solve_with_animation()

            self.draw()
            pygame.display.update()
            clock.tick(30)


if __name__ == "__main__":
    visualizer = SolverVisualizer()
    visualizer.run()
