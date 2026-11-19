// SPDX-FileCopyrightText: 2026 James Norman
//
// SPDX-License-Identifier: Apache-2.0

// The OpenPrintHQ mark (openprinthq-ui's "mark" icon: a hexagon holding stacked print layers) in an accent
// tile, and the name beside it.
const AhiMark = function () {
    return (
        <div className="ahi-mark">
            <span className="ahi-tile" aria-hidden="true">
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
                    <path d="M12 2.5 20.5 7.3v9.4L12 21.5l-8.5-4.8V7.3z" />
                    <path d="M8 16h8M9.5 12.8h5M11 9.6h2" />
                </svg>
            </span>
            <span className="ahi-name">OpenPrintHQ</span>
        </div>
    );
};

export default AhiMark;
