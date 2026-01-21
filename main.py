from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

candidate_paths = []
if getattr(sys, "frozen", False):
    candidate_paths.append(Path(getattr(sys, "_MEIPASS", ROOT)))

candidate_paths.extend(
    [
        ROOT / "src",
        ROOT,
        ROOT.parent / "src",
        ROOT.parent,
    ]
)

for path in candidate_paths:
    if (path / "mcconvert_ui").exists():
        sys.path.insert(0, str(path))
        break

from mcconvert_ui.app import main

if __name__ == "__main__":
    main()
