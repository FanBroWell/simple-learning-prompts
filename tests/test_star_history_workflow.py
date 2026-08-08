"""Integration checks for the self-hosted star-history automation."""

from __future__ import annotations

import re
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
        checkout_action = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
        setup_python_action = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"

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
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("group: update-star-history", workflow)
        self.assertIn("cancel-in-progress: true", workflow)
        self.assertIn("jobs:\n  test:", workflow)
        self.assertIn("  update:\n    needs: test", workflow)
        self.assertLess(workflow.index("  test:"), workflow.index("  update:"))

        test_job = workflow[workflow.index("  test:") : workflow.index("  update:")]
        update_job = workflow[workflow.index("  update:") :]
        self.assertIn("runs-on: ubuntu-latest", test_job)
        self.assertIn("timeout-minutes: 10", test_job)
        self.assertIn("python3 -m unittest -v", test_job)
        self.assertIn("if: github.ref == 'refs/heads/main'", update_job)
        self.assertIn("permissions:\n      contents: write", update_job)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("timeout-minutes: 10", workflow)
        self.assertEqual(workflow.count(checkout_action), 2)
        self.assertEqual(workflow.count(setup_python_action), 2)
        self.assertIn(checkout_action + " # v4", workflow)
        self.assertIn(setup_python_action + " # v5", workflow)
        self.assertNotIn("actions/checkout@v4", workflow)
        self.assertNotIn("actions/setup-python@v5", workflow)
        self.assertNotRegex(workflow, r"actions/checkout@(?!11d5960a326750d5838078e36cf38b85af677262)")
        self.assertNotRegex(workflow, r"actions/setup-python@(?!a26af69be951a213d495a4c3e4e4022e16d87065)")
        for action, reference in re.findall(r"uses: (actions/[^@\s]+)@([^\s#]+)", workflow):
            with self.subTest(action=action):
                self.assertRegex(reference, r"^[0-9a-f]{40}$")
        self.assertIn("python-version: '3.12'", workflow)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", update_job)
        self.assertIn(
            "python scripts/generate_star_history.py --output assets/star-history.svg", workflow
        )
        self.assertIn("git add -- assets/star-history.svg", update_job)
        self.assertIn("git diff --cached --quiet", update_job)
        self.assertIn(
            'if [ "$(git diff --cached --name-only)" != "assets/star-history.svg" ]; then',
            update_job,
        )
        self.assertIn('git config user.name "github-actions[bot]"', update_job)
        self.assertIn(
            'git commit --only -m "docs: update star history chart" -- assets/star-history.svg',
            update_job,
        )
        self.assertIn("git push origin HEAD:main", update_job)
        self.assertLess(
            update_job.index("git diff --cached --quiet"),
            update_job.index('if [ "$(git diff --cached --name-only)"'),
        )
        self.assertLess(
            update_job.index('if [ "$(git diff --cached --name-only)"'),
            update_job.index("git commit --only"),
        )
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
        labelled_by = root.get("aria-labelledby")
        self.assertTrue(labelled_by)
        element_ids = {element.get("id") for element in root.iter()}
        for element_id in labelled_by.split():
            with self.subTest(element_id=element_id):
                self.assertIn(element_id, element_ids)
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}title"))
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}desc"))


if __name__ == "__main__":
    unittest.main()
