from utils import generate_partial_sudoku, print_board, isValidSudoku
import os
import csv
from algos import solvers
import copy
import time
import tracemalloc


class SolverStats:
    def __init__(self):
        self.recursive_calls = 0
        self.constraint_checks = 0
        self.max_depth = 0
        self.current_depth = 0

    def enter_call(self):
        self.recursive_calls += 1
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)

    def exit_call(self):
        self.current_depth -= 1

    def check_constraint(self):
        self.constraint_checks += 1


def benchmark_single_puzzle(puzzle, puzzle_id, runs=50):
    """Benchmark all solvers on a single puzzle."""
    results = []
    print(f"------ Starting Benchmark for {puzzle_id} with {runs} runs ------")
    print_board(puzzle)

    for name, solver in solvers.items():
        print(f"Testing solver: {name}")
        total_time = 0.0
        success = True
        stats_accum = SolverStats()
        peak_memory = 0

        for _ in range(runs):
            grid_copy = copy.deepcopy(puzzle)
            start = time.perf_counter()
            tracemalloc.start()
            stats = SolverStats()
            solved = solver(grid_copy, stats)
            end = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            if not solved:
                success = False
                break

            total_time += end - start
            # Accumulate stats
            stats_accum.recursive_calls += stats.recursive_calls
            stats_accum.constraint_checks += stats.constraint_checks
            stats_accum.max_depth = max(stats_accum.max_depth, stats.max_depth)
            peak_memory = max(peak_memory, peak)

        result = {
            "solver": name,
            "puzzle_id": puzzle_id,
            "solved": success,
            "avg_time": total_time / runs if success else None,
            "avg_calls": stats_accum.recursive_calls // runs if success else None,
            "avg_checks": stats_accum.constraint_checks // runs if success else None,
            "max_depth": stats_accum.max_depth if success else None,
            "peak_memory_kb": peak_memory // 1024 if success else None,
            "runs": runs,
        }

        results.append(result)

        if success:
            print(
                f"{name}: ✔ | Avg Time: {result['avg_time']:.5f}s | "
                f"Avg Calls: {result['avg_calls']} | "
                f"Avg Checks: {result['avg_checks']} | "
                f"Peak Memory: {result['peak_memory_kb']}KB | "
                f"Max Depth: {result['max_depth']}"
            )
        else:
            print(f"{name}: ✘ Failed")

    return results


def benchmark_multiple_puzzles(difficulty_levels=None, runs_per_puzzle=50):
    """Run benchmarks on multiple puzzles with varying difficulty levels."""
    if difficulty_levels is None:
        # Default difficulty levels
        difficulty_levels = [22, 30, 40, 50, 60]

    all_results = []

    for difficulty in difficulty_levels:
        print(f"\n==== Testing puzzles with {difficulty} empty cells ====")
        for i in range(3):  # 3 puzzles per difficulty level
            puzzle_id = f"puzzle_d{difficulty}_{i}"
            puzzle = generate_partial_sudoku(empty_cells=difficulty)
            results = benchmark_single_puzzle(puzzle, puzzle_id, runs=runs_per_puzzle)
            all_results.extend(results)

            write_results_to_csv(results)

    return all_results


def write_results_to_csv(results, filename="benchmark_results.csv"):
    """Write benchmark results to a CSV file."""
    fieldnames = [
        "solver",
        "puzzle_id",
        "solved",
        "avg_time",
        "avg_calls",
        "avg_checks",
        "max_depth",
        "peak_memory_kb",
        "runs",
    ]

    write_header = not os.path.exists(filename)

    with open(filename, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(results)

    print(f"Results written to {filename}")


def main():
    # results = benchmark_single_puzzle(generate_partial_sudoku(empty_cells=50), "quick_test", runs=5)
    # write_results_to_csv(results)

    difficulty_levels = [22, 30, 40, 50, 60]  # Easy to extremely difficult
    benchmark_multiple_puzzles(difficulty_levels=difficulty_levels, runs_per_puzzle=50)


if __name__ == "__main__":
    main()
