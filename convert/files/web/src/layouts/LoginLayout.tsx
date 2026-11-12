// SPDX-FileCopyrightText: 2026 Authelia
// SPDX-FileCopyrightText: 2026 James Norman
//
// SPDX-License-Identifier: Apache-2.0

import { ReactNode, useCallback, useEffect, useState } from "react";

import AhiFrame from "@components/AhiFrame";
import { useLanguageContext } from "@contexts/LanguageContext";
import { Language } from "@models/LocaleInformation";
import { UserInfo } from "@models/UserInfo";
import { getLocaleInformation } from "@services/LocaleInformation";

export interface Props {
    id?: string;
    children?: ReactNode;
    title?: null | string;
    titleTooltip?: null | string;
    subtitle?: null | string;
    subtitleTooltip?: null | string;
    userInfo?: UserInfo;
    maxWidth?: false | string;
}

// Authelia's login layout, in the ArtisanHub frame (convert/convert.py replaces the upstream file with this one
// only while the upstream Props are exactly the ones above).
const LoginLayout = function (props: Props) {
    const { locale, setLocale } = useLanguageContext();
    const [localeList, setLocaleList] = useState<Language[]>([]);

    const fetchLocaleInformation = useCallback(async () => {
        try {
            const data = await getLocaleInformation();
            setLocaleList(data.languages);
        } catch (err) {
            console.error("could not get locale list:", err);
        }
    }, []);

    useEffect(() => {
        void fetchLocaleInformation();
    }, [fetchLocaleInformation]);

    return (
        <AhiFrame
            id={props.id}
            title={props.title}
            subtitle={props.subtitle}
            userInfo={props.userInfo}
            maxWidth={props.maxWidth}
            localeCurrent={locale}
            localeList={localeList}
            onLocaleChange={(value: string) => setLocale(value)}
        >
            {props.children}
        </AhiFrame>
    );
};

export default LoginLayout;
