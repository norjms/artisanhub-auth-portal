// Renders each portal page at both desktop sizes and checks it. Run by tests/screens.sh, inside the test network.
import crypto from "node:crypto";
import fs from "node:fs";

import { chromium } from "playwright";

const out = process.argv[2] ?? "/out";
const HUB = "https://hub.ahi.test";
const AUTH = `${HUB}/authelia`;
const PASSWORD = "test-password-1";
const SIZES = [
    [1920, 1080],
    [1280, 860],
];
// The lightest stop of the page gradient, the worst case for light text over glass.
const WORST_GROUND = [0x3f, 0x56, 0x6a];

const failures = [];

async function signIn(page, user, target) {
    await page.goto(target);
    await page.locator("#username-textfield").fill(user);
    await page.locator("#password-textfield").fill(PASSWORD);
    await page.locator("#sign-in-button").click();
    await page.locator("#first-factor-stage").waitFor({ state: "detached", timeout: 20000 });
}

function pkce() {
    const verifier = crypto.randomBytes(32).toString("base64url");
    const challenge = crypto.createHash("sha256").update(verifier).digest("base64url");
    return challenge;
}

// Each page: how to reach it in a fresh browser context, and what shows it is there.
const PAGES = [
    {
        name: "sign-in",
        ready: "#first-factor-stage",
        reach: async (page) => page.goto(`${AUTH}/?rd=${encodeURIComponent(`${HUB}/farm`)}`),
    },
    {
        name: "sign-in-error",
        ready: "#first-factor-stage",
        reach: async (page) => {
            await page.goto(`${AUTH}/`);
            await page.locator("#username-textfield").fill("owner");
            await page.locator("#password-textfield").fill("not-the-password");
            await page.locator("#sign-in-button").click();
            await page.getByText("Incorrect username or password").first().waitFor();
        },
    },
    {
        name: "second-factor",
        ready: "#second-factor-stage",
        reach: async (page) => signIn(page, "maker", `${AUTH}/?rd=${encodeURIComponent(`${HUB}/second`)}`),
    },
    {
        name: "no-access",
        ready: "#denied-stage",
        reach: async (page) => {
            await signIn(page, "maker", `${AUTH}/`);
            await page.goto(`${HUB}/farm`);
        },
    },
    {
        name: "consent",
        ready: "#openid-consent-stage, [id^='openid-consent']",
        reach: async (page) => {
            const query = new URLSearchParams({
                client_id: "shop",
                code_challenge: pkce(),
                code_challenge_method: "S256",
                redirect_uri: `${HUB}/cb`,
                response_type: "code",
                scope: "openid profile email groups",
                state: crypto.randomBytes(12).toString("hex"),
            });
            await signIn(page, "owner", `${AUTH}/api/oidc/authorization?${query}`);
        },
    },
    {
        name: "settings",
        ready: "#root > *",
        reach: async (page) => {
            await signIn(page, "owner", `${AUTH}/`);
            await page.goto(`${AUTH}/settings`);
        },
    },
];

function check(name, condition, message) {
    if (!condition) failures.push(`${name}: ${message}`);
}

async function measure(page) {
    return page.evaluate((worst) => {
        // Any CSS colour (rgb, oklab, color-mix) as [r, g, b, alpha], through a canvas.
        const canvas = document.createElement("canvas");
        canvas.width = canvas.height = 1;
        const ctx = canvas.getContext("2d", { willReadFrequently: true });
        const parse = (value) => {
            if (!value || value === "transparent") return null;
            ctx.clearRect(0, 0, 1, 1);
            ctx.fillStyle = "rgba(0, 0, 0, 0)";
            ctx.fillStyle = value;
            ctx.fillRect(0, 0, 1, 1);
            const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
            return [r, g, b, a / 255];
        };
        const over = (top, bottom) => [0, 1, 2].map((i) => top[i] * top[3] + bottom[i] * (1 - top[3]));
        const lum = (rgb) => {
            const c = rgb.map((v) => {
                const s = v / 255;
                return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
            });
            return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
        };
        const ratio = (a, b) => {
            const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
            return (x + 0.05) / (y + 0.05);
        };
        // The ground under an element: its own and its ancestors' backgrounds, stacked over the worst page stop.
        const ground = (el) => {
            const layers = [];
            for (let node = el; node && node !== document.documentElement; node = node.parentElement) {
                const bg = parse(getComputedStyle(node).backgroundColor);
                if (bg && bg[3] > 0) layers.push(bg);
                if (bg && bg[3] === 1) break;
            }
            let rgb = worst;
            for (const layer of layers.reverse()) rgb = over(layer, rgb);
            return rgb;
        };
        const low = [];
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
            const text = node.textContent.trim();
            const el = node.parentElement;
            if (!text || !el) continue;
            const box = el.getBoundingClientRect();
            const style = getComputedStyle(el);
            if (box.width === 0 || box.height === 0 || style.visibility === "hidden" || Number(style.opacity) === 0) continue;
            const fg = parse(style.color);
            if (!fg) continue;
            const bg = ground(el);
            const value = ratio(over(fg, bg), bg);
            const size = parseFloat(style.fontSize);
            const large = size >= 24 || (size >= 18.66 && Number(style.fontWeight) >= 700);
            if (value < (large ? 3 : 4.5)) low.push(`${text.slice(0, 40)} (${value.toFixed(2)})`);
        }
        const card = document.querySelector(".ahi-card")?.getBoundingClientRect();
        const loaded = new Set(
            [...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family.replaceAll(/["']/g, "")),
        );
        return {
            cardInView: card
                ? card.top >= 0 && card.left >= 0 && card.bottom <= innerHeight && card.right <= innerWidth
                : null,
            fonts: loaded.has("Manrope") && (loaded.has("Sora") || !document.querySelector(".ahi-title, .ahi-name")),
            loaded: [...loaded].join(", "),
            low,
            scrolls:
                document.documentElement.scrollHeight > innerHeight + 1 ||
                document.documentElement.scrollWidth > innerWidth + 1,
            text: document.body.innerText,
        };
    }, WORST_GROUND);
}

const browser = await chromium.launch();
for (const pageSpec of PAGES) {
    for (const [width, height] of SIZES) {
        const label = `${pageSpec.name} ${width}x${height}`;
        const context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { height, width } });
        const page = await context.newPage();
        try {
            await pageSpec.reach(page);
            await page.locator(pageSpec.ready).first().waitFor({ timeout: 20000 });
            await page.waitForLoadState("networkidle");
            await page.mouse.move(0, 0);
            await page.evaluate(() => document.fonts.ready);
            await page.waitForTimeout(600);
            const file = `${out}/${pageSpec.name}-${width}x${height}.png`;
            await page.screenshot({ path: file });
            const m = await measure(page);
            check(label, !m.scrolls, "the page scrolls");
            check(label, m.cardInView !== false, "the card is not fully in view");
            check(label, m.fonts, `Manrope or Sora is not loaded (loaded: ${m.loaded || "none"})`);
            check(label, m.low.length === 0, `low contrast: ${m.low.join("; ")}`);
            check(label, !m.text.includes("\u2014"), "an em dash on the page");
            fs.writeFileSync(`${out}/${pageSpec.name}-${width}x${height}.txt`, m.text);
            console.log(`${label}: ${file}`);
        } catch (err) {
            failures.push(`${label}: ${err.message.split("\n")[0]}`);
            await page.screenshot({ path: `${out}/${pageSpec.name}-${width}x${height}-failed.png` }).catch(() => {});
        }
        await context.close();
    }
}
await browser.close();

if (failures.length) {
    console.error(`${failures.length} problem(s):\n${failures.join("\n")}`);
    process.exit(1);
}
console.log("every page passed");
