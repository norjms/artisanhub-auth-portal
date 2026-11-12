// SPDX-FileCopyrightText: 2026 Authelia
// SPDX-FileCopyrightText: 2026 James Norman
//
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from "react";

import AhiFrame from "@components/AhiFrame";
import { UserInfo } from "@models/UserInfo";

export interface Props {
    id?: string;
    children?: ReactNode;
    title?: null | string;
    userInfo?: UserInfo;
}

// Authelia's minimal layout, in the ArtisanHub frame (convert/convert.py replaces the upstream file with this
// one only while the upstream Props are exactly the ones above).
const MinimalLayout = function (props: Props) {
    return (
        <AhiFrame id={props.id} title={props.title} userInfo={props.userInfo}>
            {props.children}
        </AhiFrame>
    );
};

export default MinimalLayout;
