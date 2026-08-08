"""Integration checks for the self-hosted star-history automation."""

from __future__ import annotations

import xml.etree.ElementTree as ElementTree
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github/workflows/update-star-history.yml"
ASSET_PATH = REPOSITORY_ROOT / "assets/star-history.svg"
STARGAZERS_URL = "https://github.com/FanBroWell/simple-learning-prompts/stargazers"
BADGE_URL = (
    "https://img.shields.io/github/stars/FanBroWell/simple-learning-prompts"
    "?style=for-the-badge&logo=github&label=Stars"
)


class StarHistoryWorkflowTests(unittest.TestCase):
    def test_workflow_is_scheduled_scoped_and_secure(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("name: Update star history", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("cron: '17 3 * * *'", workflow)
        self.assertIn("branches: [main]", workflow)
        for path in (
            ".github/workflows/update-star-history.yml",
            "scripts/generate_star_history.py",
            "tests/test_generate_star_history.py",
            "tests/test_star_history_workflow.py",
        ):
            self.assertIn(path, workflow)
        self.assertIn("permissions:\n  contents: write", workflow)
        self.assertIn("group: update-star-history", workflow)
        self.assertIn("cancel-in-progress: true", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("timeout-minutes: 10", workflow)
        self.assertIn("actions/checkout@v4", workflow)
        self.assertIn("actions/setup-python@v5", workflow)
        self.assertIn("python-version: '3.12'", workflow)
        self.assertIn("python3 -m unittest -v", workflow)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", workflow)
        self.assertIn(
            "python scripts/generate_star_history.py --output assets/star-history.svg", workflow
        )
        self.assertLess(
            workflow.index("python3 -m unittest -v"),
            workflow.index("python scripts/generate_star_history.py --output assets/star-history.svg"),
        )
        self.assertIn("git add -- assets/star-history.svg", workflow)
        self.assertIn("git diff --cached --quiet", workflow)
        self.assertIn('git config user.name "github-actions[bot]"', workflow)
        self.assertIn("docs: update star history chart", workflow)
        self.assertIn("git push", workflow)
        self.assertNotIn("api.star-history.com", workflow)
        self.assertNotIn("PAT", workflow)

    def test_readmes_link_to_the_self_hosted_chart_and_stargazers(self):
        expected_blocks = {
            "README.md": (
                "## 🌟 Star History",
                "[![Star History Chart](assets/star-history.svg)](" + STARGAZERS_URL + ")",
                "[![GitHub Stars](" + BADGE_URL + ")](" + STARGAZERS_URL + ")",
                "曲线由 GitHub Actions 每日自动更新。",
                "如果这个项目对你有帮助，**点个 Star 让更多人看到** ⭐",
            ),
            "README.en.md": (
                "## 🌟 Star History",
                "[![Star History Chart](assets/star-history.svg)](" + STARGAZERS_URL + ")",
                "[![GitHub Stars](" + BADGE_URL + ")](" + STARGAZERS_URL + ")",
                "The chart is updated daily by GitHub Actions.",
                "If this project helps you, **give it a Star so more learners can find it** ⭐",
            ),
        }

        for filename, expected_lines in expected_blocks.items():
            with self.subTest(filename=filename):
                readme = (REPOSITORY_ROOT / filename).read_text(encoding="utf-8")
                self.assertNotIn("api.star-history.com", readme)
                for line in expected_lines:
                    self.assertIn(line, readme)
                self.assertGreater(readme.index("## 🌟 Star History"), readme.index("## License"))

    def test_chart_asset_is_an_accessible_xml_svg(self):
        svg = ASSET_PATH.read_text(encoding="utf-8")
        root = ElementTree.fromstring(svg)

        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(root.get("role"), "img")
        self.assertTrue(root.get("aria-labelledby"))
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}title"))
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}desc"))


if __name__ == "__main__":
    unittest.main()
