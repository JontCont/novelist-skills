from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "shared/novelist/scripts"
HOOK = ROOT / "scripts/sdd_gate_hook.py"
COMMANDS = (
    "novelist-new-story",
    "novelist-rule",
    "novelist-plan",
    "novelist-chapter",
    "novelist-write",
    "novelist-review",
)


class PluginTests(unittest.TestCase):
    def run_script(self, name: str, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / name), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_hook(self, event: dict) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HOOK)],
            cwd=ROOT,
            input=json.dumps(event),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_manifest_and_skill_names_are_valid(self) -> None:
        manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        self.assertFalse((ROOT / "skills/novelist").exists())
        for command in COMMANDS:
            skill_path = ROOT / "skills" / command / "SKILL.md"
            skill = skill_path.read_text(encoding="utf-8")
            self.assertRegex(skill, rf"(?m)^name: {re.escape(command)}$")
            self.assertRegex(skill, r"(?m)^user-invocable: true$")
            self.assertRegex(skill, r"(?m)^disable-model-invocation: true$")
            self.assertIn("skill_context", skill)
            self.assertNotIn("../../shared/novelist/references/", skill)
            self.assertLess(len(skill), 2200, f"{command} must remain a thin command reminder")

    def test_project_lifecycle_and_retrieval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            initialized = self.run_script(
                "init_novel.py", "jade-city", "--title", "玉城", "--root", str(root)
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            project = root / "novels/jade-city"

            initial_validation = self.run_script("validate_project.py", str(project))
            self.assertEqual(initial_validation.returncode, 1)
            self.assertIn("unresolved decisions", initial_validation.stdout)

            spec_path = project / "spec.md"
            resolved_spec = re.sub(r"\{\{[^}]+\}\}", "已決定", spec_path.read_text(encoding="utf-8"))
            resolved_spec = resolved_spec.replace("- [ ] Replace every required placeholder before approving this specification.\n", "")
            spec_path.write_text(resolved_spec, encoding="utf-8")
            characters = project / "canon/characters.md"
            characters.write_text(
                characters.read_text(encoding="utf-8") + "\n林夜害怕鐘聲，並保管玉戒。\n",
                encoding="utf-8",
            )

            validation = self.run_script("validate_project.py", str(project))
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
            retrieval = self.run_script("retrieve.py", str(project), "林夜保管什麼", "--json")
            self.assertEqual(retrieval.returncode, 0, retrieval.stderr)
            results = json.loads(retrieval.stdout)
            self.assertGreater(len(results), 0)
            self.assertEqual(results[0]["path"], "canon/characters.md")
            self.assertIn("玉戒", results[0]["text"])

    def test_character_return_is_explicit_and_progress_is_retrievable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            initialized = self.run_script(
                "init_novel.py", "jade-city", "--title", "玉城", "--root", str(root)
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            project = root / "novels/jade-city"
            character = {
                "id": "lin-ye",
                "name": "林夜",
                "aliases": [],
                "role": "protagonist",
                "personality": ["謹慎", "不信任權威"],
                "status": "departed",
                "current_location": "北境",
                "first_appearance_chapter": 1,
                "last_seen_chapter": 3,
                "last_event": "獨自前往北境",
                "return_condition": "找到玉戒來源",
            }
            (project / "characters.json").write_text(
                json.dumps({"characters": [character]}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            progress_path = project / "progress.json"
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
            progress["latest_accepted_chapter"] = 3
            progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")
            draft = project / "chapters/drafts/04.md"
            draft.write_text("林夜推開地窖的門，帶回刻有王印的玉戒。", encoding="utf-8")

            blocked = self.run_script("check_continuity.py", str(project), str(draft))
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("approve the return explicitly", blocked.stdout)

            approved = self.run_script(
                "check_continuity.py", str(project), str(draft), "--allow-return", "lin-ye"
            )
            self.assertEqual(approved.returncode, 0, approved.stdout + approved.stderr)
            unrecordable = self.run_script(
                "record_progress.py",
                str(project),
                "--chapter",
                "4",
                "--title",
                "地窖歸人",
                "--summary",
                "林夜返回地窖並帶回王印玉戒",
                "--present",
                "lin-ye",
            )
            self.assertEqual(unrecordable.returncode, 2)
            self.assertIn("non-active characters require --return", unrecordable.stderr)
            recorded = self.run_script(
                "record_progress.py",
                str(project),
                "--chapter",
                "4",
                "--title",
                "地窖歸人",
                "--summary",
                "林夜返回地窖並帶回王印玉戒",
                "--present",
                "lin-ye",
                "--return",
                "lin-ye=完成尋找玉戒來源的條件",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stdout + recorded.stderr)

            progress = json.loads((project / "progress.json").read_text(encoding="utf-8"))
            registry = json.loads((project / "characters.json").read_text(encoding="utf-8"))
            self.assertEqual(progress["latest_accepted_chapter"], 4)
            self.assertEqual(registry["characters"][0]["last_seen_chapter"], 4)
            self.assertEqual(registry["characters"][0]["status"], "active")
            retrieval = self.run_script("retrieve.py", str(project), "最新進度 王印玉戒", "--json")
            self.assertEqual(retrieval.returncode, 0, retrieval.stderr)
            results = json.loads(retrieval.stdout)
            self.assertTrue(any(result["path"] == "progress.json" for result in results))

    def test_locale_aware_retrieval_normalizes_and_expands_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            initialized = self.run_script(
                "init_novel.py", "glass-moon", "--title", "硝子の月", "--locale", "ja", "--root", str(root)
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            project = root / "novels/glass-moon"
            config_path = project / ".novelist/config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["content_locale"], "ja")
            self.assertEqual(config["skill_context"], {"protocol": "novelist-sdd", "version": 1})
            config["retrieval"]["term_aliases"] = {"計畫": ["计划"]}
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (project / "canon/world.md").write_text(
                "# World Canon\n\nミナは夜明けにＡＲＣＡＤＩＡ計畫を開始する。\n",
                encoding="utf-8",
            )

            for query in ("ミナの夜明け", "Arcadia", "计划"):
                retrieval = self.run_script("retrieve.py", str(project), query, "--json")
                self.assertEqual(retrieval.returncode, 0, retrieval.stderr)
                results = json.loads(retrieval.stdout)
                self.assertGreater(len(results), 0, query)
                self.assertEqual(results[0]["path"], "canon/world.md", query)

            config["retrieval"]["term_aliases"] = {"計畫": "计划"}
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            validation = self.run_script("validate_project.py", str(project))
            self.assertEqual(validation.returncode, 1)
            self.assertIn("term_aliases must map terms to arrays of strings", validation.stdout)

            config["retrieval"]["term_aliases"] = {}
            config.pop("skill_context")
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            context_check = self.run_script("sdd.py", "check", str(project), "constitution.md")
            self.assertEqual(context_check.returncode, 2)
            self.assertIn("skill_context marker is missing or incompatible", context_check.stderr)

            invalid = self.run_script(
                "init_novel.py", "bad-locale", "--title", "Bad", "--locale", "xx", "--root", str(root)
            )
            self.assertEqual(invalid.returncode, 2)
            self.assertIn("unsupported locale", invalid.stderr)

    def test_sdd_hook_blocks_stale_and_allows_current_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            initialized = self.run_script(
                "init_novel.py", "jade-city", "--title", "玉城", "--root", str(root)
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            project = root / "novels/jade-city"
            incomplete = self.run_script("sdd.py", "approve", str(project), "spec.md")
            self.assertEqual(incomplete.returncode, 2)
            self.assertIn("spec.md still contains unresolved decisions", incomplete.stderr)
            spec_path = project / "spec.md"
            spec_path.write_text("# 玉城規格\n\n類型：懸疑\n主角追查王印來源，阻力是城主。\n", encoding="utf-8")
            checklist_path = project / "checklists/requirements.md"
            checklist_path.write_text(
                checklist_path.read_text(encoding="utf-8").replace("- [ ]", "- [x]"), encoding="utf-8"
            )
            character = {
                "id": "lin-ye",
                "name": "林夜",
                "aliases": [],
                "role": "protagonist",
                "personality": ["謹慎", "不信任權威"],
                "status": "active",
                "current_location": "玉城外",
                "first_appearance_chapter": 1,
                "last_seen_chapter": 0,
                "last_event": "準備進城",
                "return_condition": None,
            }
            (project / "characters.json").write_text(
                json.dumps({"characters": [character]}, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            story_path = project / "story.json"
            story = json.loads(story_path.read_text(encoding="utf-8"))
            story["protagonist_ids"] = ["lin-ye"]
            story_path.write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")
            (project / "canon/world.md").write_text("# World Canon\n\n玉城入夜後封門。\n", encoding="utf-8")
            (project / "canon/characters.md").write_text("# Character Canon\n\n林夜不信任城主。\n", encoding="utf-8")
            (project / "canon/timeline.md").write_text("# Timeline\n\n| 前夜 | 王印失竊 | spec |\n", encoding="utf-8")
            (project / "canon/setups.md").write_text("# Setups\n\n| S1 | 王印裂痕 | planned | 第三章 | spec |\n", encoding="utf-8")
            (project / "outline/outline.md").write_text(
                "# Outline\n\n## Constitution Check\n\n- [x] Canon\n- [x] Character\n- [x] Trace\n- [x] Scope\n\n"
                "## Chapters\n\n第一章：林夜進城發現王印。\n",
                encoding="utf-8",
            )
            task = project / "chapters/tasks/01.md"
            task.write_text(
                "# Chapter 01 Task\n\n"
                "- Viewpoint: 林夜\n"
                "- Time and location: 黃昏，玉城門\n"
                "- Outline reference: 第一章：林夜進城發現王印\n"
                "- Chapter goal: 進入玉城\n"
                "- Opposition: 城門守衛阻攔\n"
                "- Emotional movement: 戒備轉為疑惑\n\n"
                "## Required Beats\n\n1. 林夜發現王印。\n\n"
                "## Exit State\n\n"
                "- New situation: 城門封閉\n"
                "- Character state changes: 林夜受困城內\n"
                "- Knowledge revealed or concealed: 王印有裂痕\n"
                "- Next pressure: 守衛開始搜捕\n\n"
                "## Retrieval Query\n\n林夜個性、玉城規則、王印伏筆\n",
                encoding="utf-8",
            )
            draft = project / "chapters/drafts/01.md"
            event = {
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "cwd": str(root),
                "tool_input": {"input": f"*** Add File: {draft}\n+第一章"},
            }

            blocked = self.run_hook(event)
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("Novel SDD gate blocked", blocked.stderr)

            canon_event = {
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "cwd": str(root),
                "tool_input": {"input": f"*** Update File: {project / 'canon/world.md'}\n+尚未完成規格"},
            }
            canon_blocked = self.run_hook(canon_event)
            self.assertEqual(canon_blocked.returncode, 2)
            self.assertIn("artifact is missing approval or stale: constitution.md", canon_blocked.stderr)
            self.assertIn("artifact is missing approval or stale: spec.md", canon_blocked.stderr)

            checklist_event = {
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "cwd": str(root),
                "tool_input": {"input": f"*** Update File: {project / 'checklists/requirements.md'}\n- [ ]\n+ [x]"},
            }
            checklist_blocked = self.run_hook(checklist_event)
            self.assertEqual(checklist_blocked.returncode, 2)
            self.assertIn("reviewer-owned checklist", checklist_blocked.stderr)

            required = (
                "constitution.md",
                "spec.md",
                "characters.json",
                "canon/world.md",
                "canon/characters.md",
                "canon/timeline.md",
                "canon/setups.md",
                "outline/outline.md",
                "chapters/tasks/01.md",
            )
            for artifact in required:
                approved = self.run_script("sdd.py", "approve", str(project), artifact)
                self.assertEqual(approved.returncode, 0, approved.stdout + approved.stderr)
            retrieval = self.run_script(
                "retrieve.py",
                str(project),
                "林夜 玉城 王印 第一章",
                "--receipt",
                "chapters/tasks/01.md",
            )
            self.assertEqual(retrieval.returncode, 0, retrieval.stderr)
            gated = self.run_script("sdd.py", "gate", str(project), "--task", "chapters/tasks/01.md")
            self.assertEqual(gated.returncode, 0, gated.stdout + gated.stderr)
            allowed = self.run_hook(event)
            self.assertEqual(allowed.returncode, 0, allowed.stderr)

            config_path = project / ".novelist/config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["content_locale"] = "zh-Hans"
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            wrong_locale = self.run_hook(event)
            self.assertEqual(wrong_locale.returncode, 2)
            self.assertIn("content_locale must match", wrong_locale.stderr)
            self.assertIn("RAG receipt locale is stale", wrong_locale.stderr)
            config["content_locale"] = "zh-Hant"
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            world = project / "canon/world.md"
            world.write_text(world.read_text(encoding="utf-8") + "\n玉城新增一條規則。\n", encoding="utf-8")
            stale = self.run_hook(event)
            self.assertEqual(stale.returncode, 2)
            self.assertIn("analysis prerequisite is missing approval or stale: canon/world.md", stale.stderr)
            self.assertIn("RAG receipt knowledge corpus is stale", stale.stderr)


if __name__ == "__main__":
    unittest.main()