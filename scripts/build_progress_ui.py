"""Build a standalone project-progress dashboard."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scopp import ClusteringProfile, ScoppConfig, ScoppPipeline
from scopp.ui import render_progress_ui


def _test_count() -> int:
    env = {**os.environ, "LOKY_MAX_CPU_COUNT": "4"}
    result = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env, check=True)
    match = re.search(r"(\d+) tests? collected", result.stdout)
    return int(match.group(1)) if match else 0


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, default=ROOT / "examples/maps/indoor_lab.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/progress_ui.html")
    args = parser.parse_args()
    runs = []
    for profile in ClusteringProfile:
        result = ScoppPipeline(ScoppConfig(profile, random_seed=0)).run_map(args.map)
        runs.append({"name": profile.value, "cells": [len(path.cell_ids) for path in result.plan.paths], "makespan": result.plan.makespan_distance_m})
    data = {
        "commit": _commit(),
        "tests": _test_count(),
        "pythonFiles": len(tuple(ROOT.glob("src/**/*.py"))) + len(tuple(ROOT.glob("scripts/*.py"))),
        "cellCount": len(ScoppPipeline().run_map(args.map).mapped.cells),
        "profiles": runs,
        "stages": [
            {"name": "지도 모델", "detail": "AOI·no-fly·Shapely", "status": "done"},
            {"name": "격자화", "detail": "FoV 기반 cell", "status": "done"},
            {"name": "Clustering", "detail": "Lloyd·MiniBatch", "status": "done"},
            {"name": "경매", "detail": "Conflict 해결", "status": "done"},
            {"name": "CPP", "detail": "Nearest neighbor", "status": "done"},
            {"name": "평가", "detail": "Makespan·확장성", "status": "done"},
            {"name": "UI", "detail": "경로 이동 재생", "status": "done"},
        ],
        "links": [
            {"name": "경로 이동 UI", "href": "path_ui.html"},
            {"name": "공식 Profile UI", "href": "official_path_ui.html"},
            {"name": "Profile 비교 JSON", "href": "profile_comparison.json"},
            {"name": "확장성 그래프", "href": "indoor_scaling.png"},
            {"name": "README", "href": "../README.md"},
        ],
        "next": [
            {"name": "경로 성능", "detail": "동적 삭제 없는 KD-tree 탐색 병목을 개선합니다."},
            {"name": "장애물 회피", "detail": "Cell 방문 순서를 실제 충돌 없는 이동 경로로 연결합니다."},
            {"name": "실기체 연동", "detail": "시뮬레이터 검증 후 실험실 제어 어댑터를 추가합니다."},
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_progress_ui(data), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
