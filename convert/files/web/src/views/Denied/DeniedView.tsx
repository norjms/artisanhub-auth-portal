// SPDX-FileCopyrightText: 2026 James Norman
//
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from "react-i18next";

import AhiFrame from "@components/AhiFrame";
import { useQueryParam } from "@hooks/QueryParam";

// Where the proxy sends someone who is signed in but may not open a page (Authelia answered 403).
// ?app= names what they tried to open.
const DeniedView = function () {
    const { t: translate } = useTranslation();
    const app = (useQueryParam("app") ?? "").replaceAll(/[^\p{L}\p{N} .'-]/gu, "").slice(0, 60).trim();
    const target = app || translate("this page");

    return (
        <AhiFrame id="denied-stage">
            <div className="ahi-denied">
                <span className="ahi-tile ahi-tile--bad" aria-hidden="true">
                    <svg
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.7"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <rect x="4" y="11" width="16" height="10" rx="2" />
                        <path d="M8 11V7a4 4 0 0 1 8 0v4" />
                    </svg>
                </span>
                <h1 className="ahi-title">{translate("You do not have access")}</h1>
                <p className="ahi-subtitle">
                    {translate(
                        "Your sign-in works, but it is not allowed to open {{app}}. Ask the hub's owner to give you a role that includes it.",
                        { app: target },
                    )}
                </p>
                <a id="denied-back" className="ahi-btn ahi-btn--secondary" href="/">
                    {translate("Back to the hub")}
                </a>
            </div>
        </AhiFrame>
    );
};

export default DeniedView;
