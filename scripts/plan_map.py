"""Run the implemented SCoPP pipeline and render the resulting paths."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scopp import ClusteringProfile, ScoppConfig, allocate_conflict_cells, cluster_map, discretize_map, load_map, plan_coverage_paths
from scopp.map.visualization import render_plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("map_file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("plan.png"))
    parser.add_argument("--profile", choices=[item.value for item in ClusteringProfile], default=ClusteringProfile.DETERMINISTIC_LLOYD.value)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    mapped = discretize_map(load_map(args.map_file))
    config = ScoppConfig.from_cli(args.profile, args.seed)
    clustered = cluster_map(mapped, profile=config.clustering_profile, random_seed=config.random_seed, tolerance_m=config.clustering_tolerance_m, max_iterations=config.clustering_max_iterations)
    allocation = allocate_conflict_cells(mapped, clustered)
    plan = plan_coverage_paths(mapped, allocation)
    figure, _ = render_plan(mapped, allocation, plan)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=160, bbox_inches="tight")
    print(f"wrote {args.output}")
    print(f"cells={len(mapped.cells)} conflicts={len(allocation.auction_decisions)} makespan={plan.makespan_distance_m:.3f}m total={plan.total_distance_m:.3f}m")
    for path in plan.paths:
        print(f"{path.node_id}: cells={len(path.cell_ids)} distance={path.distance_m:.3f}m")


if __name__ == "__main__":
    main()
