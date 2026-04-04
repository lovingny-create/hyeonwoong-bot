"""
천문 계산 결과를 카카오톡에 적합한 한국어 텍스트로 변환.
전통적 4분류(태양계 / 항성 / 성운·성단 / 은하)로 그룹화하여 출력.
"""

from config import FOV_W_ARCMIN, FOV_H_ARCMIN

_CATEGORY_EMOJI = {
    "태양계":   "🪐",
    "항성":     "⭐",
    "성운·성단":"🌫",
    "은하":     "🌌",
}
_CATEGORY_ORDER = ["태양계", "항성", "성운·성단", "은하"]


def _fov_hint(size_arcmin: float) -> str:
    """천체 크기와 시야각 비교 문자열."""
    fov = min(FOV_W_ARCMIN, FOV_H_ARCMIN)  # 짧은 변 기준
    if size_arcmin > fov * 1.5:
        return f" [시야초과 {size_arcmin:.0f}']"
    if size_arcmin > fov * 0.5:
        return f" [시야적합 {size_arcmin:.0f}']"
    return f" [{size_arcmin:.0f}']"


def _format_star(t: dict) -> str:
    """항성(이중성/변광성) 항목 포맷."""
    mag_str = f"{t['mag']:.1f}등급" if t.get("mag") is not None else ""

    # 변광성: 등급 범위 + 주기
    extra = ""
    if t.get("mag_range"):
        extra = f" ({t['mag_range']}등급"
        if t.get("period_str"):
            extra += f" 주기 {t['period_str']}"
        extra += ")"
    elif mag_str:
        extra = f" ({mag_str})"

    source_tag = " [AAVSO]" if t.get("source") == "aavso" else ""
    return (
        f"• {t['name']}"
        + (f" - {t['label']}" if t.get("label") else "")
        + f" | {t['type']}{extra}{source_tag}\n"
        f"  고도 {t['altitude']:.0f}° / {t['direction']}쪽"
    )


def _format_dso(t: dict) -> str:
    """딥스카이(성운·성단·은하) 항목 포맷."""
    size_str = _fov_hint(t["size_arcmin"]) if t.get("size_arcmin") else ""
    mag_str  = f" / {t['mag']:.1f}등급" if t.get("mag") is not None else ""
    return (
        f"• {t['name']} - {t['label']}\n"
        f"  {t['type']}{size_str}{mag_str}\n"
        f"  고도 {t['altitude']:.0f}° / {t['direction']}쪽"
    )


def _format_solar(t: dict) -> str:
    """태양계 천체 항목 포맷."""
    return (
        f"• {t['label']} ({t['name']}) | {t['type']}\n"
        f"  고도 {t['altitude']:.0f}° / {t['direction']}쪽"
    )


def format_target_list(fixed: list, solar: list, variable=None) -> str:
    if variable is None:
        variable = []

    # 태양계 객체에 category 태그
    for t in solar:
        t.setdefault("category", "태양계")

    # 변광성에 category 태그 (variable_stars.py에서 이미 설정되지만 보험)
    for t in variable:
        t.setdefault("category", "항성")

    # 전체 목록 합산
    all_targets = solar + variable + fixed

    if not all_targets:
        return (
            "현재 관측 가능한 천체가 없습니다.\n\n"
            "• 아직 해가 지지 않았거나 천문박명 전일 수 있어요.\n"
            "• 고도 30° 이상 조건을 만족하는 천체가 없는 경우입니다."
        )

    # 카테고리별 그룹화 (최대 2~3개씩)
    groups: dict[str, list] = {cat: [] for cat in _CATEGORY_ORDER}
    for t in all_targets:
        cat = t.get("category", "성운·성단")
        if cat in groups:
            groups[cat].append(t)

    lines = ["[관측 추천 천체]\n"]

    for cat in _CATEGORY_ORDER:
        items = groups[cat]
        if not items:
            continue

        # 카테고리별 상위 항목 수 제한
        limit = 2 if cat in ("태양계", "항성") else 3
        items = sorted(items, key=lambda x: x.get("altitude", 0), reverse=True)[:limit]

        emoji = _CATEGORY_EMOJI.get(cat, "")
        lines.append(f"{emoji} {cat}")

        for t in items:
            if cat == "태양계":
                lines.append(_format_solar(t))
            elif cat == "항성":
                lines.append(_format_star(t))
            else:
                lines.append(_format_dso(t))
        lines.append("")  # 카테고리 사이 빈 줄

    lines.append(f"* CDK14 시야각: {FOV_W_ARCMIN:.0f}'×{FOV_H_ARCMIN:.0f}'")
    return "\n".join(lines)


def _simbad_url(name: str) -> str:
    """천체 이름으로 Simbad 검색 URL 생성."""
    encoded = name.replace(" ", "+")
    return f"https://simbad.u-strasbg.fr/simbad/sim-basic?Ident={encoded}"


def _card_description_star(t: dict) -> str:
    """항성 카드 설명 텍스트."""
    parts = [t.get("type", "")]
    if t.get("mag_range"):
        parts.append(f"{t['mag_range']}등급")
        if t.get("period_str"):
            parts.append(f"주기 {t['period_str']}")
    elif t.get("mag") is not None:
        parts.append(f"{t['mag']:.1f}등급")
    parts.append(f"고도 {t['altitude']:.0f}° / {t['direction']}쪽")
    return "\n".join(parts)


def _card_description_dso(t: dict) -> str:
    """딥스카이 카드 설명 텍스트."""
    parts = [t.get("type", "")]
    if t.get("size_arcmin"):
        parts[0] += f" / {t['size_arcmin']:.0f}'"
    if t.get("mag") is not None:
        parts.append(f"{t['mag']:.1f}등급")
    parts.append(f"고도 {t['altitude']:.0f}° / {t['direction']}쪽")
    return "\n".join(parts)


def _card_description_solar(t: dict) -> str:
    """태양계 카드 설명 텍스트."""
    return f"{t.get('type', '행성')}\n고도 {t['altitude']:.0f}° / {t['direction']}쪽"


def format_target_cards(fixed: list, solar: list, variable=None) -> list:
    """관측 대상을 BasicCard 카루셀용 카드 리스트로 변환. Simbad URL 포함."""
    if variable is None:
        variable = []

    for t in solar:
        t.setdefault("category", "태양계")
    for t in variable:
        t.setdefault("category", "항성")

    all_targets = solar + variable + fixed

    if not all_targets:
        return []

    # 카테고리별 그룹화 + 정렬
    groups = {cat: [] for cat in _CATEGORY_ORDER}
    for t in all_targets:
        cat = t.get("category", "성운·성단")
        if cat in groups:
            groups[cat].append(t)

    cards = []
    for cat in _CATEGORY_ORDER:
        items = groups[cat]
        if not items:
            continue
        limit = 2 if cat in ("태양계", "항성") else 3
        items = sorted(items, key=lambda x: x.get("altitude", 0), reverse=True)[:limit]

        for t in items:
            emoji = _CATEGORY_EMOJI.get(cat, "")
            name = t.get("name", "")
            label = t.get("label", "")

            if cat == "태양계":
                title = f"{emoji} {label} ({name})"
                desc = _card_description_solar(t)
            elif cat == "항성":
                title = f"{emoji} {name}"
                if label:
                    title += f" - {label}"
                desc = _card_description_star(t)
            else:
                title = f"{emoji} {name} - {label}"
                desc = _card_description_dso(t)

            card = {
                "title": title,
                "description": desc,
                "buttons": [
                    {
                        "action": "webLink",
                        "label": "Simbad 검색",
                        "webLinkUrl": _simbad_url(name),
                    }
                ],
            }
            cards.append(card)

    return cards


def format_no_night() -> str:
    return (
        "현재 천문박명 전(또는 낮)이라 관측이 어렵습니다.\n\n"
        "광주 기준 천문박명(태양 고도 -18°) 이후 관측을 시작해 주세요.\n"
        "날짜/시간을 지정해서 물어보시면 미리 계획도 도와드릴게요!\n"
        "예: '다음 주 금요일 밤 관측 대상 추천해줘'"
    )
