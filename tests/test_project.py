from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectTests(unittest.TestCase):
    def test_output_profile_and_seed(self) -> None:
        cfg = json.loads((ROOT / "config" / "baarle.json").read_text(encoding="utf-8"))
        self.assertEqual((cfg["format"]["width"], cfg["format"]["height"], cfg["format"]["fps"]), (1080, 1920, 60))
        self.assertEqual(cfg["voice"]["seed"], 42)

    def test_script_has_eight_scene_paragraphs(self) -> None:
        script = (ROOT / "content" / "baarle_script.txt").read_text(encoding="utf-8").strip()
        chunks = [p.strip() for p in script.split("\n\n") if p.strip()]
        self.assertEqual(len(chunks), 8)
        self.assertTrue(all(len(p.split()) > 8 for p in chunks))

    def test_standalone_ledger_exists(self) -> None:
        path = ROOT / "used_scripts.txt"
        self.assertTrue(path.is_file())
        self.assertEqual(path.read_text(encoding="utf-8"), "")

    def test_single_cell_notebook_and_repo_lock(self) -> None:
        nb = json.loads((ROOT / "colab" / "BAARLE_SINGLE_CELL.ipynb").read_text(encoding="utf-8"))
        self.assertEqual(len(nb["cells"]), 1)
        code = "".join(nb["cells"][0]["source"])
        self.assertIn('GH_REPO = "redk13/gradle"', code)
        self.assertNotRegex(code, re.compile(r"vidmap|english-tenses-tutor", re.I))
        compile(code, "BAARLE_SINGLE_CELL", "exec")

    def test_pipeline_syntax(self) -> None:
        compile((ROOT / "src" / "pipeline.py").read_text(encoding="utf-8"), "pipeline.py", "exec")


if __name__ == "__main__":
    unittest.main()
