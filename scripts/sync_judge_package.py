"""Copy only allowlisted, already-public runtime sources into the judge package."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
for directory, pattern in (("app", "*.py"), ("static", "*.html")):
    target = ROOT / "track_2b" / "src" / directory
    target.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / directory).glob(pattern):
        shutil.copyfile(source, target / source.name)
