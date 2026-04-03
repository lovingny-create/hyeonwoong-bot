"""
기능 3: 시야각 / 플레이트 스케일 / 노출 시간 안내
순수 수식 계산 (API 호출 없음 → 매우 빠름).
"""

from config import (
    APERTURE_MM, FOCAL_LENGTH_MM, FOCAL_RATIO,
    PIXEL_SIZE_UM, SENSOR_W, SENSOR_H,
    PLATE_SCALE_ARCSEC_PX, FOV_W_ARCMIN, FOV_H_ARCMIN,
    FILTER_EXPOSURE_GUIDE, FILTERS,
)


def _limiting_magnitude() -> float:
    """망원경 극한 등급 추정 (CCD 기준)."""
    # 구경(mm) 기준 CCD 극한등급: ~5 + 5*log10(D_mm) + 2 (CCD 이득)
    import math
    return round(5 + 5 * math.log10(APERTURE_MM) + 2, 1)


async def handle(utterance: str) -> str:
    lim_mag = _limiting_magnitude()
    lines = [
        "[ CDK14 + C3-61000 PRO 계산값 ]",
        "",
        f"● 플레이트 스케일: {PLATE_SCALE_ARCSEC_PX:.3f}\"/pixel",
        f"● 시야각: {FOV_W_ARCMIN:.1f}'×{FOV_H_ARCMIN:.1f}' (0.80°×0.54°)",
        f"● 이미지 크기: {SENSOR_W}×{SENSOR_H} px (61MP)",
        f"● 이론적 극한등급(CCD): ~{lim_mag}등급",
        "",
        "● UBVRI 권장 노출 시간 (가이드)",
    ]
    for f in FILTERS:
        bright, faint = FILTER_EXPOSURE_GUIDE[f]
        lines.append(f"  {f}필터: 성운/성단 {bright}s | 은하 {faint}s")

    lines += [
        "",
        "※ 실제 노출은 대기 상태, 대상 밝기,",
        "   가이딩 성능에 따라 조정하세요.",
    ]
    return "\n".join(lines)
