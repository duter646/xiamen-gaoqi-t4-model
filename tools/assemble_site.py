"""Explicit Pages allowlist, excluding raw references and local history."""
from pathlib import Path
import hashlib
import shutil
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '_site'
OUTPUT.mkdir(exist_ok=True)
model = ROOT / 'assets/xiamen-gaoqi-t4.glb'
expected = (ROOT / 'SHA256SUMS.txt').read_text().split()[0]
assert hashlib.sha256(model.read_bytes()).hexdigest() == expected, 'Model checksum mismatch'
for name in ['index.html', 'app.js', 'style.css', 'compare.html', 'arrival-finger-compare.html',
             'EVIDENCE.md', 'REPORT.md', 'README.md', 'THIRD_PARTY_NOTICES.txt', 'SHA256SUMS.txt']:
    shutil.copy2(ROOT / name, OUTPUT / name)
for name in ['assets', 'vendor']:
    shutil.copytree(ROOT / name, OUTPUT / name, dirs_exist_ok=True)
(OUTPUT / 'tests').mkdir(exist_ok=True)
shutil.copy2(ROOT / 'tests/overall.png', OUTPUT / 'tests/overall.png')
(OUTPUT / '.nojekyll').touch()
print(f'Public site assembled: {sum(p.stat().st_size for p in OUTPUT.rglob("*") if p.is_file()):,} bytes')
