# artisanhub-auth-portal

ArtisanHub's sign-in: [Authelia](https://github.com/authelia/authelia) with its web portal converted to the
ArtisanHub look. An ArtisanHub installation serves it at `/authelia` of the hub's name. Sign in, second factor,
consent, signed in, sign out and settings all keep Authelia's behaviour; only how they look and a few English words
change, and a "no access" page is added for people who are signed in but may not open something.

This repository holds no copy of Authelia. It holds the steps that turn an Authelia **release** into this image,
and the build applies them to the release named in `upstream.env`:

| File | What it is |
|---|---|
| `upstream.env` | The Authelia release built (its tag, the commit the tag must point at, and its official image), and the [artisanhub-ui](https://github.com/norjms/artisanhub-ui) release that supplies the colours, sizes and fonts. |
| `convert/convert.py` | The conversion, as a script. Each edit names the exact text it changes, and every part of Authelia's markup the look relies on is checked; the build stops, naming what is missing, if a release no longer has it. |
| `convert/files/` | Files added to the portal: the stylesheet, the ArtisanHub frame (mark, card, footer), and the "no access" page. |
| `Dockerfile` | Fetches both releases, checks their commits, runs the conversion, builds the portal and Authelia's binary from the same source, and puts the binary into the official image of that release. |
| `tests/` | The conversion's tests, a check of what this repository may contain, and `screens.sh`, which renders every page of a built image at 1920 x 1080 and 1280 x 860 and checks it. |
| `.github/workflows/upstream-watch.yml` | Checks daily for a new Authelia release and opens a pull request moving `upstream.env` to it, saying whether the conversion still applies. |

## Keeping up with Authelia

1. A new release appears; the watch opens a pull request `Authelia vX.Y.Z`.
2. If it says the conversion failed, fix the named step in `convert/convert.py` on that branch.
3. Build the image for amd64 and arm64, run `tests/screens.sh <image> <folder>` and look at the pages, then merge.
   ArtisanHub's installer then pins the new image by digest.

Only published releases are taken; pre-releases, drafts, branches and nightly builds never are.

## Running it

It is configured exactly like Authelia. Two optional extras:

| Setting | Effect |
|---|---|
| `server.asset_path` with `locales/en/install.json` holding `{"name": "..."}` | The footer says "Signing in to *name*". Without it, the footer names the address people are on. |
| `authentication_backend.password_reset.custom_url` (with `disable: false`) | "Forgot your password?" opens that address in the same tab, for example the hub's own reset page, `https://<hub>/account/password`. Authelia registers none of its own reset endpoints when a custom address is set. Without it (and with `password_reset.disable: true`) the page says to ask the hub's owner for a new link. |

The proxy sends someone Authelia refuses (403) to `/denied?app=<name>` under Authelia's path, for example with
Caddy's `forward_auth`:

```
@denied status 403
handle_response @denied {
	redir * /authelia/denied?app=ArtisanHub%20Farm 302
}
```

## Checks

```sh
tests/prepare.sh                              # fetch the pinned releases into work/
python3 -m unittest discover -s tests -v      # the conversion and its failure cases
python3 tests/check_tree.py HEAD              # what the repository may contain, how its commits are made
tests/screens.sh <image> <folder>             # every page, both sizes: no scroll, fonts, contrast
RESET_URL=https://hub.ahi.test/account/password tests/screens.sh <image> <folder>   # the same, with a reset address
```

## Licence

Authelia is licensed under the Apache License, Version 2.0, and so is this repository: see `LICENSE` and
`NOTICE`, which says what was changed. The fonts come from artisanhub-ui's releases under the SIL Open Font
License.
