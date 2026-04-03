"""
기능 1: 관측 대상 추천
현재 시각 기준으로 4분류(태양계/항성/성운·성단/은하)별 관측 가능한 천체 반환.
- 태양계: astropy get_body 실시간 계산
- 항성(변광성): AAVSO VSX 24h 캐시
- 항성(이중성) + 성운·성단 + 은하: 고정 카탈로그 + astroplan 가시성 계산
"""

from astronomy.visibility import get_visible_fixed_targets, get_visible_solar_system
from astronomy.variable_stars import get_visible_variable_stars
from astronomy.formatter import format_target_list


async def handle(utterance: str) -> str:
    solar    = get_visible_solar_system(n_results=2)
    fixed    = get_visible_fixed_targets(n_results=6)
    variable = await get_visible_variable_stars(n_results=3)
    return format_target_list(fixed=fixed, solar=solar, variable=variable)
