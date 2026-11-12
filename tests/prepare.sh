#!/usr/bin/env bash
# Fetch what the tests convert, exactly as the Dockerfile does: the Authelia release and the artisanhub-ui
# release named in upstream.env, each checked against its commit, artisanhub-ui with its dependencies.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
. "$root/upstream.env"
mkdir -p "$root/work"
cd "$root/work"
rm -rf authelia artisanhub-ui
git clone -q --depth 1 --branch "$AUTHELIA_VERSION" "$AUTHELIA_REPO" authelia
test "$(git -C authelia rev-parse HEAD)" = "$AUTHELIA_COMMIT"
git clone -q --depth 1 --branch "$ARTISANHUB_UI_VERSION" "$ARTISANHUB_UI_REPO" artisanhub-ui
test "$(git -C artisanhub-ui rev-parse HEAD)" = "$ARTISANHUB_UI_COMMIT"
(cd artisanhub-ui && npm ci --omit=dev --omit=peer --ignore-scripts --no-audit --no-fund > /dev/null)
echo "prepared Authelia $AUTHELIA_VERSION and artisanhub-ui $ARTISANHUB_UI_VERSION in work/"
