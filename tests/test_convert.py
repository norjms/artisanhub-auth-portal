"""The conversion applies to the pinned Authelia release, and stops, naming what is missing, when anything it
relies on is gone.

    AUTHELIA_SRC=<Authelia source at upstream.env's release> ARTISANHUB_UI=<artisanhub-ui with its dependencies> \
        python3 -m unittest discover -s tests

tests/prepare.sh fetches both as the Dockerfile does.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "convert"))

import convert  # noqa: E402

SRC = Path(os.environ.get("AUTHELIA_SRC", ROOT / "work/authelia"))
UI = Path(os.environ.get("ARTISANHUB_UI", ROOT / "work/artisanhub-ui"))


@unittest.skipUnless((SRC / "web/src/App.tsx").is_file(), "no Authelia source; run tests/prepare.sh")
class Convert(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.tree = self.tmp / "authelia"
        shutil.copytree(SRC, self.tree, ignore=shutil.ignore_patterns(".git", "node_modules", "docs"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def run_convert(self) -> None:
        convert.convert(self.tree, UI)

    def assert_fails(self, *words: str) -> None:
        with self.assertRaises(convert.ConvertError) as caught:
            self.run_convert()
        message = str(caught.exception)
        for word in words:
            self.assertIn(word, message)

    def change(self, rel: str, old: str, new: str) -> None:
        path = self.tree / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"test setup: {rel} has no {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")

    def test_the_pinned_release_converts(self) -> None:
        self.run_convert()
        web = self.tree / "web/src"
        self.assertIn("AhiFrame", (web / "layouts/LoginLayout.tsx").read_text())
        self.assertIn('@import "./ahi/ahi.css";', (web / "index.css").read_text())
        self.assertTrue((web / "ahi/theme.css").read_text().startswith("/* Generated from tokens/tokens.json"))
        fonts = sorted(p.name for p in (web / "ahi/fonts").glob("*.woff2"))
        self.assertEqual(len(fonts), 14, fonts)
        self.assertNotIn("./files/", (web / "ahi/fonts.css").read_text())
        words = json.loads((self.tree / "internal/server/locales/en/portal.json").read_text())
        self.assertEqual(words["Remember me"], "Keep me signed in")
        self.assertIn("Signing in to {{name}}.", words)
        consent = json.loads((self.tree / "internal/server/locales/en/consent.json").read_text())
        self.assertEqual(consent["Consent Request"], "Consent request")
        self.assertEqual(words["Push Notification"], "Push Notification")
        form = (web / "views/LoginPortal/FirstFactor/FirstFactorForm.tsx").read_text()
        self.assertIn("<Switch", form)
        self.assertNotIn("<Checkbox", form)
        self.assertIn('id="ahi-password-help"', form)
        self.assertIn('path="/denied"', (web / "App.tsx").read_text())

    def test_converting_twice_stops(self) -> None:
        self.run_convert()
        self.assert_fails("convert:")

    def test_a_missing_hook_stops_it(self) -> None:
        self.change("web/src/components/UI/FloatingInput.tsx", 'data-slot="floating-input"', 'data-slot="input"')
        self.assert_fails("FloatingInput.tsx", "floating-input")

    def test_a_hard_coded_colour_that_moved_stops_it(self) -> None:
        self.change("web/src/views/LoginPortal/SecondFactor/MethodContainer.tsx", "text-[#5858ff]", "text-info")
        self.assert_fails("MethodContainer.tsx")

    def test_changed_layout_props_stop_it(self) -> None:
        self.change("web/src/layouts/LoginLayout.tsx", "    maxWidth?: false | string;\n",
                    "    maxWidth?: false | string;\n    footer?: ReactNode;\n")
        self.assert_fails("LoginLayout.tsx", "Props")

    def test_a_new_part_in_a_layout_stops_it(self) -> None:
        self.change("web/src/layouts/MinimalLayout.tsx", 'import { getLogoOverride } from "@utils/Configuration";',
                    'import { getLogoOverride } from "@utils/Configuration";\nimport Banner from "@components/Banner";')
        self.assert_fails("MinimalLayout.tsx", "@components/Banner")

    def test_a_moved_anchor_in_the_form_stops_it(self) -> None:
        self.change("web/src/views/LoginPortal/FirstFactor/FirstFactorForm.tsx",
                    'label={`${translate("Username")} *`}', 'label={translate("Username or email")}')
        self.assert_fails("FirstFactorForm.tsx", "Username")

    def test_a_missing_route_anchor_stops_it(self) -> None:
        self.change("web/src/App.tsx", "<Route path={LogoutRoute} element={<SignOut />} />",
                    "<Route path={LogoutRoute} element={<SignOutView />} />")
        self.assert_fails("App.tsx", "LogoutRoute")

    def test_a_missing_word_stops_it(self) -> None:
        self.change("internal/server/locales/en/portal.json", '"Remember me": "Remember me",', "")
        self.assert_fails("portal.json", "Remember me")

    def test_a_new_upstream_file_of_the_same_name_stops_it(self) -> None:
        (self.tree / "web/src/components/AhiMark.tsx").write_text("export default 1;\n")
        self.assert_fails("AhiMark.tsx", "exists upstream")

    def test_the_theme_must_come_from_artisanhub_ui(self) -> None:
        with self.assertRaises(convert.ConvertError) as caught:
            convert.convert(self.tree, self.tmp / "nothing")
        self.assertIn("theme.css", str(caught.exception))

    def test_the_stylesheet_reaches_upstream_only_through_listed_hooks(self) -> None:
        css = (ROOT / "convert/files/web/src/ahi/ahi.css").read_text()
        hooks = " ".join(n for needles in convert.HOOKS.values() for n in needles)
        for slot in ("floating-input", "switch", "switch-thumb", "dropdown-menu-content", "dialog-content",
                     "sheet-content"):
            self.assertIn(f'data-slot="{slot}"', css)
            self.assertIn(f'data-slot="{slot}"', hooks)
        self.assertIn('[data-slot="button"]', css)
        self.assertIn('"data-slot": "button"', hooks)


if __name__ == "__main__":
    unittest.main()
