// SPDX-FileCopyrightText: 2026 James Norman
//
// SPDX-License-Identifier: Apache-2.0

// The ArtisanHub mark: the cube in an accent tile, and the name beside it.
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
                    <path d="M12 2 3 7v10l9 5 9-5V7l-9-5z" />
                    <path d="M3 7l9 5 9-5M12 12v10" />
                </svg>
            </span>
            <span className="ahi-name">ArtisanHub</span>
        </div>
    );
};

export default AhiMark;
