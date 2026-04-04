"""
기능 1: 관측 대상 추천
현재 시각 기준으로 4분류(태양계/항성/성운·성단/은하)별 관측 가능한 천체 반환.
- 태양계: astropy get_body 실시간 계산
- 항성(변광성): AAVSO VSX 24h 캐시
- 항성(이중성) + 성운·성단 + 은하: 고정 카탈로그 + astroplan 가시성 계산

Simbad 검색 URL 포함 카루셀 카드로 응답.
"""

from astronomy.visibility import get_visible_fixed_targets, get_visible_solar_system
from astronomy.variable_stars import get_visible_variable_stars
from astronomy.formatter import format_target_list, format_target_cards
from kakao.response_builder import build_carousel_response, build_simple_text_response


async def handle(utterance: str):
    """관측 대상 추천. dict(카루셀 JSON) 또는 str(텍스트) 반환."""
    solar    = get_visible_solar_system(n_results=2)
    fixed    = get_visible_fixed_targets(n_results=6)
    variable = await get_visible_variable_stars(n_results=3)

    cards = format_target_cards(fixed=fixed, solar=solar, variable=variable)
    if cards:
        return build_carousel_response(cards)

    # 관측 가능한 천체 없으면 텍스트 응답
    return format_target_list(fixed=fixed, solar=solar, variable=variable)
