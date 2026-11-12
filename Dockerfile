# artisanhub-auth-portal: an Authelia release with its web portal converted for ArtisanHub by convert/convert.py.
#
# The releases come from upstream.env (passed as build arguments by the maintainer's build script): each tag is
# fetched and must be the commit named there, so a moved tag fails the build instead of changing what is built.
# The image is the official Authelia image of the same release with one file changed: the binary, rebuilt from
# the same source with the converted portal embedded in it.

ARG AUTHELIA_IMAGE

FROM node:22-alpine AS ui
ARG ARTISANHUB_UI_REPO
ARG ARTISANHUB_UI_VERSION
ARG ARTISANHUB_UI_COMMIT
RUN apk add --no-cache git
RUN test -n "$ARTISANHUB_UI_VERSION" && test -n "$ARTISANHUB_UI_COMMIT" \
 && git clone -q --depth 1 --branch "$ARTISANHUB_UI_VERSION" "$ARTISANHUB_UI_REPO" /ui \
 && test "$(git -C /ui rev-parse HEAD)" = "$ARTISANHUB_UI_COMMIT" \
 && cd /ui && npm ci --omit=dev --omit=peer --ignore-scripts --no-audit --no-fund

FROM python:3.12-alpine AS convert
ARG AUTHELIA_REPO
ARG AUTHELIA_VERSION
ARG AUTHELIA_COMMIT
RUN apk add --no-cache git
RUN test -n "$AUTHELIA_VERSION" && test -n "$AUTHELIA_COMMIT" \
 && git clone -q --depth 1 --branch "$AUTHELIA_VERSION" "$AUTHELIA_REPO" /src \
 && test "$(git -C /src rev-parse HEAD)" = "$AUTHELIA_COMMIT" \
 && rm -rf /src/.git /src/docs
COPY --from=ui /ui /ui
COPY convert /convert
RUN python3 /convert/convert.py /src /ui

FROM node:22-alpine AS web
COPY --from=convert /src /src
WORKDIR /src/web
RUN npm install -g --no-audit --no-fund pnpm@12 \
 && pnpm install --frozen-lockfile --ignore-scripts
# The added and changed files are put in the portal's own code style, then the portal is built, type-checked
# and linted by its own build (a remaining problem fails it here).
RUN pnpm exec eslint --fix src/components/Ahi*.tsx src/hooks/AhiInstall.ts src/views/Denied src/layouts \
      src/App.tsx src/views/LoginPortal/FirstFactor/FirstFactorForm.tsx > /dev/null || true \
 && pnpm build
# The API's documentation pages, as Authelia's own build adds them (cmd/authelia-scripts): its api/ folder and
# swagger-ui's files at the version that release names.
RUN apk add --no-cache tar \
 && v="$(sed -n 's/^[[:space:]]*versionSwaggerUI[[:space:]]*=[[:space:]]*"\([0-9.]*\)"$/\1/p' /src/cmd/authelia-scripts/cmd/gen.go)" \
 && test -n "$v" \
 && cp -r /src/api /src/internal/server/public_html \
 && wget -qO /tmp/swagger.tgz "https://github.com/swagger-api/swagger-ui/archive/v$v.tar.gz" \
 && tar -C /src/internal/server/public_html/api --exclude=index.html --exclude='*.map' --exclude='*-es-*' \
      --strip-components=2 -xzf /tmp/swagger.tgz "swagger-ui-$v/dist" \
 && test -s /src/internal/server/public_html/api/index.html && test -s /src/internal/server/public_html/index.html

# glibc, as the official image is: the binary is linked like the one it replaces.
FROM golang:1.27 AS binary
ARG AUTHELIA_VERSION
ARG AUTHELIA_COMMIT
ENV GOTOOLCHAIN=auto CGO_ENABLED=1 \
    CGO_CPPFLAGS="-D_FORTIFY_SOURCE=2 -fstack-protector-strong" CGO_LDFLAGS="-Wl,-z,relro,-z,now"
COPY --from=web /src /src
WORKDIR /src
RUN go mod download
RUN x=github.com/authelia/authelia/v4/internal/utils \
 && go build -buildmode=pie -trimpath -o /authelia \
      -ldflags "-linkmode=external -s -w -X '$x.BuildTag=$AUTHELIA_VERSION' -X '$x.BuildCommit=$AUTHELIA_COMMIT' -X '$x.BuildBranch=master' -X '$x.BuildState=tagged clean' -X '$x.BuildExtra=artisanhub'" \
      ./cmd/authelia/ \
 && /authelia --version

FROM ${AUTHELIA_IMAGE}
ARG AUTHELIA_VERSION
COPY --from=binary /authelia /app/authelia
# The rebuilt binary must run in the official image as it is.
RUN ["/app/authelia", "--version"]
COPY LICENSE NOTICE /app/artisanhub-auth-portal/
COPY --from=convert /src/web/src/ahi/fonts/*-LICENSE.txt /app/artisanhub-auth-portal/fonts/
LABEL org.opencontainers.image.title="artisanhub-auth-portal" \
      org.opencontainers.image.description="ArtisanHub's sign-in: Authelia ${AUTHELIA_VERSION} with its portal in the ArtisanHub look" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="${AUTHELIA_VERSION}"
