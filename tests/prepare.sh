#!/usr/bin/env bash
# Fetch what the tests convert, exactly as the Dockerfile does: the Authelia release and the openprinthq-ui
# release named in upstream.env, each checked against its commit, openprinthq-ui with its dependencies.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
. "$root/upstream.env"
mkdir -p "$root/work"
cd "$root/work"
rm -rf authelia openprinthq-ui
git clone -q --depth 1 --branch "$AUTHELIA_VERSION" "$AUTHELIA_REPO" authelia
test "$(git -C authelia rev-parse HEAD)" = "$AUTHELIA_COMMIT"
git clone -q --depth 1 --branch "$OPENPRINTHQ_UI_VERSION" "$OPENPRINTHQ_UI_REPO" openprinthq-ui
test "$(git -C openprinthq-ui rev-parse HEAD)" = "$OPENPRINTHQ_UI_COMMIT"
(cd openprinthq-ui && npm ci --omit=dev --omit=peer --ignore-scripts --no-audit --no-fund > /dev/null)
echo "prepared Authelia $AUTHELIA_VERSION and openprinthq-ui $OPENPRINTHQ_UI_VERSION in work/"
