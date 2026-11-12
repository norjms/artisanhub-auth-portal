// SPDX-FileCopyrightText: 2026 James Norman
//
// SPDX-License-Identifier: Apache-2.0

import { ReactNode, useEffect } from "react";

import AhiFooter from "@components/AhiFooter";
import AhiMark from "@components/AhiMark";
import AppBarLoginPortal from "@components/AppBarLoginPortal";
import PrivacyPolicyDrawer from "@components/PrivacyPolicyDrawer";
import { Language } from "@models/LocaleInformation";
import { UserInfo } from "@models/UserInfo";

const widths: Record<string, string> = {
    lg: "896px",
    md: "672px",
    sm: "560px",
    xl: "1152px",
    xs: "440px",
};

export interface Props {
    id?: string;
    children?: ReactNode;
    title?: null | string;
    subtitle?: null | string;
    userInfo?: UserInfo;
    maxWidth?: false | string;
    localeCurrent?: string;
    localeList?: Language[];
    onLocaleChange?: (_locale: string) => void;
}

// The ArtisanHub sign-in frame: the mark and name above one glass card, and the footer below it, centred on
// the page. Every portal page renders inside it.
const AhiFrame = function (props: Props) {
    useEffect(() => {
        document.title = props.title ? `${props.title} - ArtisanHub` : "ArtisanHub";
    }, [props.title]);

    const width = props.maxWidth === false ? "1152px" : (widths[props.maxWidth ?? "xs"] ?? widths.xs);

    return (
        <div className="ahi-page">
            <div className="ahi-bar">
                <AppBarLoginPortal
                    userInfo={props.userInfo}
                    onLocaleChange={props.onLocaleChange}
                    localeList={props.localeList}
                    localeCurrent={props.localeCurrent}
                />
            </div>
            <main className="ahi-center">
                <div className="ahi-column" style={{ width: `min(${width}, 100%)` }}>
                    <AhiMark />
                    <section id={props.id} className="ahi-card">
                        {props.title ? <h1 className="ahi-title">{props.title}</h1> : null}
                        {props.subtitle ? <p className="ahi-subtitle">{props.subtitle}</p> : null}
                        <div className="ahi-body">{props.children}</div>
                    </section>
                    <AhiFooter />
                </div>
            </main>
            <PrivacyPolicyDrawer />
        </div>
    );
};

export default AhiFrame;
