"""Publish only browser assets; never include backend code, data or credentials."""
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'dist'
target.mkdir(exist_ok=True)
for name in ('index.html','config.js','api-client.js','exercises.json'):
    shutil.copy2(ROOT/name,target/name)
(target/'.nojekyll').touch()
print('Packaged GitHub Pages frontend in dist/.')
