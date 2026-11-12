// SPDX-FileCopyrightText: 2026 James Norman
//
// SPDX-License-Identifier: Apache-2.0

import { Fragment } from "react";

import { useTranslation } from "react-i18next";

import PrivacyPolicyLink from "@components/PrivacyPolicyLink";
import { EncodedName, EncodedURL } from "@constants/constants";
import { useInstallName } from "@hooks/AhiInstall";
import { getPrivacyPolicyEnabled } from "@utils/Configuration";

// Which installation this sign-in belongs to, and what protects it.
const AhiFooter = function () {
    const { t: translate } = useTranslation();
    const name = useInstallName();
    const authelia = atob(String.fromCodePoint(...EncodedName));

    return (
        <p className="ahi-footer">
            {name ? <Fragment>{translate("Signing in to {{name}}.", { name })} </Fragment> : null}
            {translate("Protected by")}{" "}
            <a href={atob(String.fromCodePoint(...EncodedURL))} target="_blank" rel="noopener noreferrer">
                {authelia}
            </a>
            .
            {getPrivacyPolicyEnabled() ? (
                <Fragment>
                    {" "}
                    <PrivacyPolicyLink />
                </Fragment>
            ) : null}
        </p>
    );
};

export default AhiFooter;
