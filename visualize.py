import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

data = pd.read_csv("benchmark_results.csv")
# Extract difficulty level from puzzle_id
data["difficulty"] = data["puzzle_id"].str.extract(r"puzzle_d(\d+)_\d+")[0]
data["puzzle_num"] = data["puzzle_id"].str.extract(r"puzzle_d\d+_(\d+)")[0]

summary = (
    data.groupby(["solver", "difficulty"])
    .agg(
        {
            "avg_time": "mean",
            "avg_calls": "mean",
            "avg_checks": "mean",
            "max_depth": "mean",
            "peak_memory_kb": "mean",
        }
    )
    .reset_index()
)

summary_pivot = summary.pivot_table(
    index="solver", columns="difficulty", values=["avg_time", "avg_calls"]
)

print("Summary Table:")
print(summary_pivot.round(6))

sns.set_theme(style="whitegrid")

plt.figure(figsize=(12, 6))
ax = sns.barplot(x="difficulty", y="avg_time", hue="solver", data=summary)
plt.title("Average Solve Time by Difficulty Level")
plt.ylabel("Time (seconds)")
plt.xlabel("Difficulty Level")
plt.yscale("log")
plt.legend(title="Solver")
plt.tight_layout()
plt.savefig("solve_time_by_difficulty.png", dpi=300)
plt.show()

plt.figure(figsize=(12, 6))
ax = sns.barplot(x="difficulty", y="avg_calls", hue="solver", data=summary)
plt.title("Average Number of Calls by Difficulty Level")
plt.ylabel("Number of Calls")
plt.xlabel("Difficulty Level")
plt.yscale("log")  #
plt.legend(title="Solver")
plt.tight_layout()
plt.savefig("calls_by_difficulty.png", dpi=300)
plt.show()


agg_data = (
    data.groupby(["solver", "difficulty"])
    .agg({"avg_time": ["mean", "std"]})
    .reset_index()
)
agg_data.columns = ["solver", "difficulty", "mean_time", "std_time"]

agg_data["difficulty"] = pd.to_numeric(agg_data["difficulty"])

for solver in agg_data["solver"].unique():
    solver_data = agg_data[agg_data["solver"] == solver]
    plt.errorbar(
        solver_data["difficulty"],
        solver_data["mean_time"],
        yerr=solver_data["std_time"],
        marker="o",
        label=solver,
    )

plt.title("Solving Time vs. Difficulty Level")
plt.xlabel("Difficulty Level")
plt.ylabel("Average Time (seconds)")
plt.yscale("log")
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.legend(title="Solver")
plt.tight_layout()
plt.savefig("solve_time_trend.png", dpi=300)
plt.show()

backtracking_data = data[data["solver"] == "Backtracking Solver"]
mrv_data = data[data["solver"] == "Constraint Propagation + MRV"]

bt_times = backtracking_data.groupby("difficulty")["avg_time"].mean()
mrv_times = mrv_data.groupby("difficulty")["avg_time"].mean()

improvement_ratio = bt_times / mrv_times

improvement_df = pd.DataFrame(
    {
        "Difficulty": improvement_ratio.index,
        "Backtracking Time (s)": bt_times.values,
        "MRV Time (s)": mrv_times.values,
        "Improvement Ratio": improvement_ratio.values,
    }
)

print("\nPerformance Improvement (Backtracking vs MRV):")
print(improvement_df.round(6))

hardest_puzzles = data[data["difficulty"].isin(["50", "60"])]
if not hardest_puzzles.empty:
    hardest_comparison = hardest_puzzles.pivot_table(
        index=["puzzle_id"],
        columns="solver",
        values=["avg_time", "avg_calls"],
        aggfunc="mean",
    ).round(4)

    print("\nHardest Puzzles Comparison:")
    print(hardest_comparison)

plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
sns.scatterplot(
    data=data,
    x="avg_calls",
    y="peak_memory_kb",
    hue="solver",
    style="difficulty",
    s=100,
)
plt.xscale("log")
plt.title("Memory Usage vs Number of Calls")
plt.xlabel("Number of Calls (log scale)")
plt.ylabel("Peak Memory (KB)")
plt.legend(title="Solver", bbox_to_anchor=(1.05, 1), loc="upper left")

plt.figure(figsize=(14, 6))
memory_heatmap = data.pivot_table(
    index="solver", columns="difficulty", values="peak_memory_kb"
)

sns.heatmap(
    memory_heatmap,
    annot=True,
    fmt=".1f",
    cmap="YlGnBu",
    cbar_kws={"label": "Peak Memory (KB)"},
)
plt.title("Memory Usage Across Difficulty Levels", fontsize=16)
plt.tight_layout()
plt.savefig("memory_usage_heatmap.png", dpi=300, bbox_inches="tight")
plt.show()

print("Memory Usage Statistics:")
memory_stats = (
    data.groupby("solver")["peak_memory_kb"].agg(["mean", "min", "max", "std"]).round(2)
)
print(memory_stats)

memory_efficiency = (
    data.groupby("solver")
    .agg({"peak_memory_kb": "mean", "avg_calls": "mean", "avg_time": "mean"})
    .reset_index()
)

memory_efficiency["memory_per_call"] = (
    memory_efficiency["peak_memory_kb"] / memory_efficiency["avg_calls"]
)
memory_efficiency["memory_time_ratio"] = (
    memory_efficiency["peak_memory_kb"] / memory_efficiency["avg_time"]
)

print("\nMemory Efficiency Metrics:")
print(memory_efficiency[["solver", "memory_per_call", "memory_time_ratio"]].round(4))

print("\nKey Performance Metrics Summary:")
solver_summary = (
    data.groupby("solver")
    .agg(
        {
            "avg_time": "mean",
            "avg_calls": "mean",
            "avg_checks": "mean",
            "max_depth": "mean",
            "peak_memory_kb": "mean",
        }
    )
    .reset_index()
)

solver_summary["time_per_call"] = (
    solver_summary["avg_time"] / solver_summary["avg_calls"]
)
solver_summary["checks_per_call"] = (
    solver_summary["avg_checks"] / solver_summary["avg_calls"]
)

print(solver_summary.round(6).to_string(index=False))

plt.figure(figsize=(14, 8))
heatmap_data = data.pivot_table(index="solver", columns="difficulty", values="avg_time")

sns.heatmap(
    heatmap_data,
    annot=True,
    fmt=".5f",
    cmap="YlGnBu",
    cbar_kws={"label": "Average Time (s)"},
)
plt.title("Solver Performance Across Difficulty Levels")
plt.tight_layout()
plt.savefig("solver_performance_heatmap.png", dpi=300)
plt.show()
