from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_progress_dashboard_builds(tmp_path: Path) -> None:
    output = tmp_path / "progress.html"
    subprocess.run([sys.executable, str(ROOT / "scripts/build_progress_ui.py"), "--output", str(output)], check=True)
    html = output.read_text(encoding="utf-8")
    assert "논문 구현 진행상황" in html
    assert "deterministic_lloyd" in html
    assert "official_minibatch" in html
    assert "__DATA__" not in html
