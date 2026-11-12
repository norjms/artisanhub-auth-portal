// SPDX-FileCopyrightText: 2026 James Norman
//
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from "react";

import { getBasePath } from "@utils/BasePath";

// The installation's name, from a small file the installer puts in Authelia's asset folder
// (server.asset_path, served at locales/en/install.json). Without it, the address people are on.
let pending: null | Promise<string> = null;

function fallback() {
    return window.location.hostname;
}

export function loadInstallName(): Promise<string> {
    pending ??= fetch(`${getBasePath()}/locales/en/install.json`, { credentials: "same-origin" })
        .then((response) => (response.ok ? response.json() : null))
        .then((data: unknown) => {
            const name = (data as null | { name?: unknown })?.name;
            return typeof name === "string" && name.trim() !== "" ? name.trim().slice(0, 120) : fallback();
        })
        .catch(() => fallback());
    return pending;
}

export function useInstallName() {
    const [name, setName] = useState("");

    useEffect(() => {
        let live = true;
        void loadInstallName().then((value) => {
            if (live) setName(value);
        });
        return () => {
            live = false;
        };
    }, []);

    return name;
}
