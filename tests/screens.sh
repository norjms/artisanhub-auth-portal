#!/usr/bin/env bash
# Render every portal page of a built image, at 1920 x 1080 and 1280 x 860, and check each: no page scroll,
# the card fully in view, the bundled fonts in use, text contrast at least 4.5:1 (3:1 for large text).
#
#   tests/screens.sh <image> <output folder>
#   RESET_URL=https://hub.ahi.test/account/password tests/screens.sh <image> <output folder>
#
# With RESET_URL, Authelia's password reset points at that address (password_reset.custom_url), as an ArtisanHub
# installation sets it: the sign-in page must show "Forgot your password?" opening it in the same tab. Without it,
# the reset is off and the page must show the line saying to ask the hub's owner.
#
# Runs a throwaway Authelia from the image behind Caddy (as an installation serves it, under /authelia of the
# hub's name), and Playwright in a container on the same network. Everything it starts is labelled and removed.
set -euo pipefail

image="${1:?image}"
out="${2:?output folder}"
here="$(cd "$(dirname "$0")" && pwd)"
run="authportal-test-$$"
label="artisanhub.managed=${MANAGED_LABEL:-auth-portal-test}"
caddy_image="${CADDY_IMAGE:-caddy:2.11-alpine}"
playwright_image="${PLAYWRIGHT_IMAGE:-mcr.microsoft.com/playwright:v1.65.0-noble}"
docker="${DOCKER:-docker}"

work="$(mktemp -d)"
cleanup() {
  $docker rm -f "$run-authelia" "$run-caddy" "$run-browser" > /dev/null 2>&1 || true
  $docker network rm "$run" > /dev/null 2>&1 || true
  # Authelia wrote into the folder as its own user; remove its files the same way.
  $docker run --rm --entrypoint sh -v "$work:/w" "$caddy_image" -c 'rm -rf /w/config' > /dev/null 2>&1 || true
  rm -rf "$work"
}
trap cleanup EXIT

mkdir -p "$work/config/assets/locales/en" "$out"
cp "$here/stack/install.json" "$work/config/assets/locales/en/install.json"
rand() { $docker run --rm --entrypoint authelia "$image" crypto rand --length 64 --charset alphanumeric | sed 's/^Random Value: //'; }
jwks="$($docker run --rm --entrypoint sh "$image" -c \
  'cd /tmp && authelia crypto pair rsa generate --bits 2048 > /dev/null && cat private.pem')"
hash="$($docker run --rm --entrypoint authelia "$image" crypto hash generate argon2 --password test-password-1 | sed 's/^Digest: //')"
RESET="$(rand)" SESSION="$(rand)" STORAGE="$(rand)" HMAC="$(rand)" JWKS="$(printf '%s\n' "$jwks" | sed 's/^/          /')" \
  RESET_URL="${RESET_URL:-}" python3 - "$here/stack/configuration.yml" "$work/config/configuration.yml" <<'PY'
import os, sys
text = open(sys.argv[1]).read()
for key in ("RESET", "SESSION", "STORAGE", "HMAC", "JWKS"):
    text = text.replace(f"@{key}@", os.environ[key])
if os.environ["RESET_URL"]:
    off = "  password_reset:\n    disable: true\n"
    assert text.count(off) == 1, "configuration.yml: password_reset block moved"
    text = text.replace(off, f"  password_reset:\n    disable: false\n    custom_url: \"{os.environ['RESET_URL']}\"\n")
open(sys.argv[2], "w").write(text)
PY
cat > "$work/config/users.yml" <<USERS
users:
  owner:
    displayname: "James Norman"
    password: "$hash"
    email: owner@hub.ahi.test
    groups: [farm]
  maker:
    displayname: "Sam Rivera"
    password: "$hash"
    email: maker@hub.ahi.test
    groups: []
USERS
chmod -R a+rX "$work"

$docker network create --label "$label" "$run" > /dev/null
$docker run -d --name "$run-authelia" --label "$label" --network "$run" --network-alias authelia \
  -v "$work/config:/config" "$image" > /dev/null
$docker run -d --name "$run-caddy" --label "$label" --network "$run" --network-alias hub.ahi.test \
  -v "$here/stack/Caddyfile:/etc/caddy/Caddyfile:ro" "$caddy_image" > /dev/null
for _ in $(seq 60); do
  if $docker exec "$run-authelia" wget -qO- http://127.0.0.1:9091/authelia/api/health > /dev/null 2>&1; then break; fi
  sleep 1
done
$docker exec "$run-authelia" wget -qO- http://127.0.0.1:9091/authelia/api/health > /dev/null \
  || { $docker logs "$run-authelia" | tail -30; exit 1; }

$docker run --name "$run-browser" --label "$label" --network "$run" --ipc=host \
  -v "$here:/tests:ro" -v "$(cd "$out" && pwd):/out" -w /tests -e HOME=/tmp -e RESET_URL="${RESET_URL:-}" \
  "$playwright_image" sh -c 'cp -r /tests /tmp/t && cd /tmp/t && npm init -y > /dev/null && npm install --silent --no-audit --no-fund playwright@1.65.0 > /dev/null && node screens.mjs /out'
