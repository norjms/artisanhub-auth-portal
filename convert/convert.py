#!/usr/bin/env python3
"""Turn an Authelia release into ArtisanHub's sign-in: Authelia with its web portal in the ArtisanHub look.

    python3 convert/convert.py <Authelia source tree> <artisanhub-ui tree, with its dependencies installed>

Only the web portal (web/) changes. Authelia's server, its API and its configuration are untouched, so the
image behaves exactly as the release it is built from. The same steps run for every release:

1. Look. The values come from the pinned artisanhub-ui release (dist/theme.css) and its bundled fonts
   (Manrope, Sora and JetBrains Mono, all under the SIL Open Font License), copied into web/src/ahi/. Every one
   of Authelia's themes is mapped onto them (web/src/ahi/ahi.css).
2. Frame. Authelia's two page layouts are replaced by the ArtisanHub frame: the ArtisanHub mark and name above
   one glass card, and a footer under it naming the installation and Authelia. The replacement only happens
   while the upstream layouts take exactly the props and use exactly the parts they had when this script was
   written; anything new stops the conversion.
3. Copy. The sign-in form: labels without asterisks, "Keep me signed in" as a toggle, and, with Authelia's own
   password reset off, a line saying who gives a new password link. With a reset address configured
   (authentication_backend.password_reset.custom_url), Authelia's own link to it stays, worded "Forgot your
   password?", and opens the address in the same tab (ArtisanHub's hub page, /account/password, links back to
   the sign-in).
4. No access. A page at /denied, where the proxy sends someone signed in whom Authelia refused (403).

Every exact edit names text that must appear a set number of times, and every selector the stylesheet reaches
into upstream markup with is checked to still exist (HOOKS). When a release changes any of it, the script stops
and says what is missing, rather than guessing; fix it here and run it again.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = HERE / "files"
WEB = "web"
SRC = "web/src"

# Fonts from artisanhub-ui's pinned @fontsource packages: (package, file prefix, weights). Latin and Latin
# Extended are bundled; other scripts fall back to the system font.
FONTS = (("manrope", "manrope", (400, 500, 600, 700)), ("sora", "sora", (500, 600)),
         ("jetbrains-mono", "jetbrains-mono", (400,)))
SUBSETS = ("latin-ext", "latin")

# Upstream files replaced whole, with what they must still look like for the replacement to be right: their
# Props interface, exactly, and the set of modules they import.
REPLACED = {
    "layouts/LoginLayout.tsx": (
        "export interface Props {\n"
        "    id?: string;\n"
        "    children?: ReactNode;\n"
        "    title?: null | string;\n"
        "    titleTooltip?: null | string;\n"
        "    subtitle?: null | string;\n"
        "    subtitleTooltip?: null | string;\n"
        "    userInfo?: UserInfo;\n"
        "    maxWidth?: false | string;\n"
        "}",
        {"react", "react-i18next", "@assets/images/user.svg?react", "@components/AppBarLoginPortal",
         "@components/Brand", "@components/PrivacyPolicyDrawer", "@components/TypographyWithTooltip",
         "@constants/constants", "@contexts/LanguageContext", "@models/LocaleInformation", "@models/UserInfo",
         "@services/LocaleInformation", "@utils/Configuration", "@utils/Styles"},
    ),
    "layouts/MinimalLayout.tsx": (
        "export interface Props {\n"
        "    id?: string;\n"
        "    children?: ReactNode;\n"
        "    title?: null | string;\n"
        "    userInfo?: UserInfo;\n"
        "}",
        {"react", "react-i18next", "@assets/images/user.svg?react", "@components/AppBarLoginPortal",
         "@components/PrivacyPolicyDrawer", "@components/TypographyWithTooltip", "@constants/constants",
         "@models/UserInfo", "@utils/Configuration"},
    ),
}

# Files added; none may exist upstream.
ADDED = ("ahi/ahi.css", "components/AhiFrame.tsx", "components/AhiFooter.tsx", "components/AhiMark.tsx",
         "hooks/AhiInstall.ts", "views/Denied/DeniedView.tsx")

# Upstream markup the stylesheet and the added files rely on. Each must still be there.
HOOKS = {
    "components/UI/FloatingInput.tsx": ['data-slot="floating-input"', "<label"],
    "components/UI/Switch.tsx": ['data-slot="switch"', 'data-slot="switch-thumb"', "data-size={size}"],
    "components/UI/Button.tsx": ['"data-slot": "button"', 'ghost: "text-secondary hover:bg-secondary/10"'],
    "components/UI/PasswordVisibilityToggle.tsx": ["absolute right-2 top-1/2 -translate-y-1/2"],
    "components/UI/DropdownMenu.tsx": ['data-slot="dropdown-menu-content"'],
    "components/UI/Dialog.tsx": ['data-slot="dialog-content"'],
    "components/UI/Sheet.tsx": ['data-slot="sheet-content"'],
    "components/AppBarLoginPortal.tsx": ["<header"],
    "layouts/SettingsLayout.tsx": ['className="fixed top-0 z-50 w-full bg-primary text-primary-foreground"'],
    "components/PrivacyPolicyDrawer.tsx": ["const PrivacyPolicyDrawer"],
    "components/PrivacyPolicyLink.tsx": ['ComponentProps<"a">'],
    "constants/constants.ts": ["export const EncodedName", "export const EncodedURL"],
    "utils/BasePath.ts": ["export function getBasePath()"],
    "utils/Configuration.ts": ["export function getPrivacyPolicyEnabled()"],
    "hooks/QueryParam.ts": ["export function useQueryParam(queryParam: string)"],
    "services/LocaleInformation.ts": ["export async function getLocaleInformation()"],
    "contexts/LanguageContext.tsx": ["export function useLanguageContext()"],
    "views/LoginPortal/SecondFactor/SecondFactorForm.tsx": ['id={"second-factor-stage"}',
                                                            "my-4 min-w-[300px] rounded-[10px] border border-border p-8"],
    "views/LoginPortal/SecondFactor/MethodContainer.tsx": ["text-[#5858ff]"],
    "views/LoginPortal/AuthenticatedView/AuthenticatedView.tsx": ["rounded-[10px] border border-border p-8"],
    "views/LoginPortal/FirstFactor/FirstFactorForm.tsx": ['id="sign-in-button"', 'id="reset-password-button"',
                                                          'id="remember-checkbox"'],
}

# The portal's English words that change, by file and key: the sign-in form's wording, and sentence case where
# Authelia uses title case. Authelia's other languages keep their own words. ("Push Notification" stays: the
# portal compares that title by its English words.)
WORDS = {
    "portal": {
        "Remember me": "Keep me signed in",
        "Reset password?": "Forgot your password?",
        "Logout": "Sign out",
        "Switch User": "Switch user",
        "Account Settings": "Account settings",
        "One-Time Password": "One-time password",
        "Enter One-Time Password": "Enter your one-time password",
        "Security Key": "Security key",
        "Security Key - WebAuthn": "Security key (WebAuthn)",
        "Privacy Policy": "Privacy policy",
    },
    "settings": {
        "User Settings": "User settings",
    },
    "consent": {
        "Consent Request": "Consent request",
        "Requested Permissions": "Requested permissions",
        "Requested Resources": "Requested resources",
        "Information Shared": "Information shared",
        "Remember Consent": "Remember consent",
        "Token Audience": "Token audience",
        "Debug Information": "Debug information",
        "Error Code": "Error code",
    },
}
# Words the added parts use, in English; other languages fall back to these.
NEW_WORDS = (
    "Use your ArtisanHub sign-in.",
    "Forgot your password? Ask the hub's owner for a new link.",
    "Signing in to {{name}}.",
    "Protected by",
    "You do not have access",
    "Your sign-in works, but it is not allowed to open {{app}}. Ask the hub's owner to give you access.",
    "this page",
    "Back to the hub",
)


class ConvertError(SystemExit):
    pass


def fail(message: str) -> None:
    raise ConvertError(f"convert: {message}")


def read(root: Path, rel: str) -> str:
    path = root / rel
    if not path.is_file():
        fail(f"{rel}: missing")
    return path.read_text(encoding="utf-8")


def edit(root: Path, rel: str, old: str, new: str, count: int = 1) -> None:
    text = read(root, rel)
    found = text.count(old)
    if found != count:
        fail(f"{rel}: expected {count} of {old[:80]!r}, found {found}")
    (root / rel).write_text(text.replace(old, new), encoding="utf-8")


def sub(root: Path, rel: str, pattern: str, new, count: int = 1) -> None:
    text = read(root, rel)
    out, n = re.subn(pattern, new, text, flags=re.S)
    if n != count:
        fail(f"{rel}: expected {count} match of /{pattern[:80]}/, found {n}")
    (root / rel).write_text(out, encoding="utf-8")


def imports(text: str) -> set[str]:
    return set(re.findall(r'^import\s[^;]*?from\s+"([^"]+)";', text, flags=re.M | re.S))


def check_hooks(root: Path) -> None:
    for rel, needles in HOOKS.items():
        text = read(root, f"{SRC}/{rel}")
        for needle in needles:
            if needle not in text:
                fail(f"{SRC}/{rel}: no longer has {needle!r}, which the ArtisanHub look relies on")


def replace_layouts(root: Path) -> None:
    for rel, (props, modules) in REPLACED.items():
        text = read(root, f"{SRC}/{rel}")
        if props not in text:
            fail(f"{SRC}/{rel}: its Props changed upstream; update convert/files/{SRC}/{rel} to match")
        found = imports(text)
        if found != modules:
            fail(f"{SRC}/{rel}: its imports changed upstream (added {sorted(found - modules)}, "
                 f"removed {sorted(modules - found)}); review what the layout now does")
        ours = (FILES / SRC / rel).read_text(encoding="utf-8")
        if props not in ours:
            fail(f"convert/files/{SRC}/{rel}: its Props differ from the upstream ones")
        (root / SRC / rel).write_text(ours, encoding="utf-8")


def add_files(root: Path) -> None:
    for rel in ADDED:
        target = root / SRC / rel
        if target.exists():
            fail(f"{SRC}/{rel}: exists upstream; this release has a file of the same name")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FILES / SRC / rel, target)


def look(root: Path, ui: Path) -> None:
    theme = ui / "dist/theme.css"
    if not theme.is_file():
        fail(f"{theme}: missing; is this an artisanhub-ui tree?")
    out = root / SRC / "ahi"
    shutil.copy(theme, out / "theme.css")
    fonts = out / "fonts"
    fonts.mkdir(exist_ok=True)
    faces = ["/* Written by convert/convert.py from artisanhub-ui's @fontsource packages (SIL Open Font License). */"]
    for package, prefix, weights in FONTS:
        base = ui / "node_modules/@fontsource" / package
        if not (base / "LICENSE").is_file():
            fail(f"{base}: missing; install artisanhub-ui's dependencies first")
        shutil.copy(base / "LICENSE", fonts / f"{prefix}-LICENSE.txt")
        for weight in weights:
            for subset in SUBSETS:
                css = read(base, f"{subset}-{weight}.css")
                woff2 = f"{prefix}-{subset}-{weight}-normal.woff2"
                if f"./files/{woff2}" not in css:
                    fail(f"{base}/{subset}-{weight}.css: no {woff2}")
                shutil.copy(base / "files" / woff2, fonts / woff2)
                # Only the woff2 source; every browser the portal supports reads it.
                css = re.sub(r"src: url\(\./files/([^)]+\.woff2)\) format\('woff2'\)(, url\([^)]+\) format\('woff'\))?;",
                             r"src: url(./fonts/\1) format('woff2');", css)
                if "./files/" in css:
                    fail(f"{base}/{subset}-{weight}.css: a font source this script does not understand")
                faces.append(css.strip())
    (out / "fonts.css").write_text("\n\n".join(faces) + "\n", encoding="utf-8")
    edit(root, f"{SRC}/index.css", '@import "@themes/tailwind-themes.css";',
         '@import "@themes/tailwind-themes.css";\n@import "./ahi/ahi.css";')
    sub(root, f"{SRC}/index.css", r'font-family:\s*"Roboto",\s*"Helvetica",\s*"Arial",\s*sans-serif;',
        "font-family: var(--ah-font-sans);")
    edit(root, f"{WEB}/index.html", '<meta name="theme-color" content="#000000" />',
         '<meta name="theme-color" content="#172028" />\n        <meta name="application-name" content="ArtisanHub sign-in" />')
    edit(root, f"{WEB}/index.html", "<title></title>", "<title>ArtisanHub</title>")
    # The show-password button sits on the field, which is now under its label rather than around it.
    edit(root, f"{SRC}/components/UI/PasswordVisibilityToggle.tsx", "absolute right-2 top-1/2 -translate-y-1/2 p-1",
         "absolute right-2 bottom-0 flex h-[38px] items-center p-1")


def sign_in_form(root: Path) -> None:
    rel = f"{SRC}/views/LoginPortal/FirstFactor/FirstFactorForm.tsx"
    edit(root, rel, '<LoginLayout id="first-factor-stage" title={translate("Sign in")}>',
         '<LoginLayout\n            id="first-factor-stage"\n            title={translate("Sign in")}\n'
         '            subtitle={translate("Use your ArtisanHub sign-in.")}\n        >')
    edit(root, rel, 'label={`${translate("Username")} *`}', 'label={translate("Username")}')
    edit(root, rel, 'label={`${translate("Password")} *`}', 'label={translate("Password")}')
    edit(root, rel, 'import { Checkbox } from "@components/UI/Checkbox";', 'import { Switch } from "@components/UI/Switch";')
    sub(root, rel, r'<Checkbox(\s+id="remember-checkbox")', r"<Switch\1")
    # Authelia's own reset is off in an ArtisanHub installation unless a reset address is set: say who helps.
    help_line = ('(\n<p id="ahi-password-help" className="ahi-help">\n'
                 '{translate("Forgot your password? Ask the hub\'s owner for a new link.")}\n</p>\n)')
    sub(root, rel, r'(\{translate\("Reset password\?"\)\}\s*</button>\s*</div>\s*\) : )null(\})',
        lambda m: m.group(1) + help_line + m.group(2))
    sub(root, rel, r'(<div className=")-my-2 flex w-full flex-row justify-end(">\s*<button\s+id="reset-password-button")',
        r"\1flex w-full flex-row justify-center\2")
    # The reset address is the hub's own page, which links back here: open it in this tab, not a new one.
    edit(root, rel, "window.open(props.resetPasswordCustomURL);",
         "window.location.assign(props.resetPasswordCustomURL);")
    edit(root, rel, 'className="cursor-pointer py-[13.5px] text-base text-primary underline-offset-4 hover:underline"',
         'className="cursor-pointer text-xs text-primary underline-offset-4 hover:underline"')


def denied_page(root: Path) -> None:
    rel = f"{SRC}/App.tsx"
    edit(root, rel, 'const RevokeResetPasswordTokenView = lazy(() => import("@views/Revoke/RevokeResetPasswordTokenView"));',
         'const RevokeResetPasswordTokenView = lazy(() => import("@views/Revoke/RevokeResetPasswordTokenView"));\n'
         'const DeniedView = lazy(() => import("@views/Denied/DeniedView"));')
    edit(root, rel, "<Route path={LogoutRoute} element={<SignOut />} />",
         '<Route path={LogoutRoute} element={<SignOut />} />\n<Route path="/denied" element={<DeniedView />} />')


def words(root: Path) -> None:
    for namespace, changes in WORDS.items():
        rel = f"internal/server/locales/en/{namespace}.json"
        data = json.loads(read(root, rel))
        for key, value in changes.items():
            if key not in data:
                fail(f"{rel}: no {key!r}")
            data[key] = value
        if namespace == "portal":
            for key in NEW_WORDS:
                if key in data:
                    fail(f"{rel}: already has {key!r}")
                data[key] = key
        (root / rel).write_text(json.dumps(data, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")


def check_copy(root: Path) -> None:
    """No em dashes in anything this script adds or writes."""
    paths = [root / SRC / rel for rel in ADDED] + [root / SRC / rel for rel in REPLACED]
    paths += [root / f"internal/server/locales/en/{namespace}.json" for namespace in WORDS]
    for path in paths:
        if "\u2014" in path.read_text(encoding="utf-8"):
            fail(f"{path.relative_to(root)}: an em dash")


def convert(root: Path, ui: Path) -> None:
    if not (root / SRC / "App.tsx").is_file():
        fail(f"{root}: not an Authelia source tree")
    check_hooks(root)
    replace_layouts(root)
    add_files(root)
    look(root, ui)
    sign_in_form(root)
    denied_page(root)
    words(root)
    check_copy(root)


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        raise SystemExit("usage: convert.py <authelia source> <artisanhub-ui tree>")
    convert(Path(argv[1]), Path(argv[2]))
    print("convert: done")


if __name__ == "__main__":
    main(sys.argv)
