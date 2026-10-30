import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "vault_audit.py"


class VaultAuditTests(unittest.TestCase):
    def run_audit(self, files, *arguments):
        with tempfile.TemporaryDirectory(prefix="vault-audit-test-") as directory:
            root = Path(directory)
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), *arguments],
                capture_output=True, encoding="utf-8", check=True,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            return json.loads(result.stdout)

    def test_path_must_not_fall_back_to_another_folder(self):
        result = self.run_audit({
            "入口.md": "[[不存在/共享]]\n[[10-当前/共享]]\n",
            "10-当前/共享.md": "# 正文\n",
            "20-历史/共享.md": "# 正文\n",
        })
        self.assertIn("不存在/共享", result["broken_by_target"])
        self.assertNotIn("10-当前/共享", result["broken_by_target"])
        self.assertEqual(result["orphan_formal_pages"], ["20-历史/共享.md"])

    def test_heading_links_include_missing_and_same_note_headings(self):
        result = self.run_audit({
            "入口.md": "# 本页标题\n[[#本页标题]]\n[[#不存在]]\n"
                      "[[10-当前/页面#已有标题|文字]]\n[[10-当前/页面#缺失标题]]\n",
            "10-当前/页面.md": "# 已有标题\n",
        })
        self.assertEqual(set(result["broken_by_target"]), {"#不存在", "10-当前/页面#缺失标题"})

    def test_unsupported_block_anchor_is_not_reported_as_verified(self):
        result = self.run_audit({
            "入口.md": "[[10-当前/页面#^block-1]]\n",
            "10-当前/页面.md": "# 正文\n",
        })
        self.assertIn("10-当前/页面#^block-1", result["unverified_anchors"])

    def test_duplicate_short_link_is_reported_as_ambiguous(self):
        result = self.run_audit({
            "入口.md": "[[共享]]\n",
            "10-当前/共享.md": "# 正文\n",
            "20-历史/共享.md": "# 正文\n",
        })
        self.assertIn("共享", result["ambiguous_links"])
        self.assertNotIn("共享", result["broken_by_target"])

    def test_nonexistent_vault_does_not_report_an_empty_success(self):
        with tempfile.TemporaryDirectory(prefix="vault-audit-test-") as directory:
            missing = Path(directory) / "missing"
            result = subprocess.run([sys.executable, str(SCRIPT), str(missing)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_formal_page_coverage_reflects_selected_prefix(self):
        files = {"个人/未导航.md": "# 正文\n"}
        default = self.run_audit(files)
        selected = self.run_audit(files, "--formal-prefixes", "个人")
        self.assertEqual(default["formal_pages_checked"], 0)
        self.assertEqual(selected["formal_pages_checked"], 1)
        self.assertEqual(selected["orphan_formal_pages"], ["个人/未导航.md"])


if __name__ == "__main__":
    unittest.main()
