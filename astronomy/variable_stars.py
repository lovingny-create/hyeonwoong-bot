"""
AAVSO VSX (Variable Star Index) 연동 모듈.
한국 위치에서 관측 가능한 변광성 목록을 가져와 고도 필터링 후 반환.
실패 시 하드코딩된 fallback 목록 사용.
"""

import time
import logging
from datetime import datetime, timezone, timedelta

import httpx
from astropy.coordinates import SkyCoord, AltAz, get_body
from astropy.time import Time
import astropy.units as u

from config import OBSERVER_LOCATION, MIN_ALTITUDE_DEG, LIMITING_MAG

logger = logging.getLogger(__name__)

# ─── AAVSO VSX API ────────────────────────────────────────
_VSX_URL = "https://vsx.aavso.org/index.php"

# 한국에서 관측 가능한 적위 범위: Dec > -25° (고도 30° 기준)
_VSX_PARAMS = {
    "view":    "api.list",
    "fromra":  0,
    "tora":    360,
    "fromdec": -25,
    "todec":   90,
    "tomag":   9,       # 최대 밝기 9등급 이상인 변광성만
    "format":  "json",
}

# ─── 캐시 (24시간) ────────────────────────────────────────
_cache: dict = {"stars": [], "timestamp": 0.0}
_CACHE_TTL = 86400  # 24시간 (초)

# ─── Fallback 하드코딩 목록 ───────────────────────────────
# AAVSO 접속 불가 시 사용
_FALLBACK_DATA = [
    # (name, label, var_type, ra_deg, dec_deg, max_mag, min_mag, period_days)
    ("Algol",       "페르세우스자리 β",  "EA",    47.04,  40.96, 2.12, 3.39,  2.87),
    ("delta Cep",   "세페우스자리 δ",    "DCEP",  337.29, 58.41, 3.48, 4.37,  5.37),
    ("eta Aql",     "독수리자리 η",      "DCEP",  298.07,  1.00, 3.48, 4.39,  7.18),
    ("beta Lyr",    "거문고자리 β",      "EB",    282.52, 33.36, 3.25, 4.36, 12.94),
    ("RR Lyr",      "거문고자리 RR",     "RR",    291.36, 42.78, 7.06, 8.12,  0.57),
    ("Mira",        "고래자리 ο",        "M",      34.84, -2.98, 2.00, 10.1, 331.96),
    ("chi Cyg",     "백조자리 χ",        "M",     297.63, 32.55, 3.30, 14.2, 408.05),
    ("R Leo",       "사자자리 R",        "M",     146.88, 11.44, 4.40,  11.3, 309.95),
    ("SS Cyg",      "백조자리 SS",       "UG",    325.68, 43.59, 7.70, 12.40, None),
    ("T Cep",       "세페우스자리 T",    "M",     313.29, 68.49, 5.20, 11.30, 388.14),
]


def _make_fallback_catalog() -> list:
    result = []
    for name, label, var_type, ra, dec, max_mag, min_mag, period in _FALLBACK_DATA:
        if max_mag > LIMITING_MAG:
            continue
        period_str = f"{period:.2f}일" if period else None
        result.append({
            "name":        name,
            "label":       label,
            "type":        var_type,
            "category":    "항성",
            "coord":       SkyCoord(ra=ra * u.deg, dec=dec * u.deg),
            "mag":         max_mag,
            "mag_range":   f"{max_mag}~{min_mag}",
            "period_str":  period_str,
            "size_arcmin": None,
            "source":      "fallback",
        })
    return result


_FALLBACK_STARS: list = _make_fallback_catalog()


# ─── 파싱 헬퍼 ───────────────────────────────────────────
def _parse_mag(mag_str) -> float:
    """'9.7 V'  →  9.7 / None → 99.0"""
    if not mag_str:
        return 99.0
    try:
        return float(str(mag_str).split()[0])
    except (ValueError, IndexError):
        return 99.0


def _parse_vsx_objects(raw) -> list:
    """VSX JSON 응답에서 변광성 목록 파싱."""
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []

    stars = []
    for obj in raw:
        try:
            max_mag = _parse_mag(obj.get("MaxMag"))
            min_mag = _parse_mag(obj.get("MinMag"))
            if max_mag > LIMITING_MAG:
                continue

            ra  = float(obj["RA2000"])
            dec = float(obj["Declination2000"])
            period_raw = obj.get("Period")
            try:
                period_days = float(period_raw) if period_raw else None
            except (ValueError, TypeError):
                period_days = None

            period_str = f"{period_days:.2f}일" if period_days else None
            var_type   = str(obj.get("VariabilityType", "변광성"))[:20]
            constellation = str(obj.get("Constellation", ""))

            stars.append({
                "name":        obj["Name"],
                "label":       constellation,
                "type":        var_type,
                "category":    "항성",
                "coord":       SkyCoord(ra=ra * u.deg, dec=dec * u.deg),
                "mag":         max_mag,
                "mag_range":   f"{max_mag}~{min_mag}",
                "period_str":  period_str,
                "size_arcmin": None,
                "source":      "aavso",
            })
        except (KeyError, ValueError, TypeError):
            continue

    return stars


# ─── AAVSO 비동기 fetch (24h 캐시) ───────────────────────
async def fetch_vsx_stars() -> list:
    """AAVSO VSX에서 변광성 목록 가져오기. 캐시 HIT 시 즉시 반환."""
    global _cache

    if _cache["stars"] and (time.time() - _cache["timestamp"]) < _CACHE_TTL:
        return _cache["stars"]

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(4.0, connect=2.0)) as client:
            resp = await client.get(_VSX_URL, params=_VSX_PARAMS)
            resp.raise_for_status()
            data = resp.json()

        raw_objects = data.get("VSXObjects", {}).get("VSXObject", [])
        stars = _parse_vsx_objects(raw_objects)

        if stars:
            _cache["stars"]     = stars
            _cache["timestamp"] = time.time()
            logger.info(f"AAVSO VSX: {len(stars)}개 변광성 로드 완료")
            return stars

    except Exception as e:
        logger.warning(f"AAVSO VSX fetch 실패: {e}. fallback 사용.")

    return _FALLBACK_STARS


# ─── 가시성 필터링 ────────────────────────────────────────
def _azimuth_to_direction(az_deg: float) -> str:
    dirs = [
        (337.5, 360, "북"), (0, 22.5, "북"),
        (22.5, 67.5, "북동"), (67.5, 112.5, "동"),
        (112.5, 157.5, "남동"), (157.5, 202.5, "남"),
        (202.5, 247.5, "남서"), (247.5, 292.5, "서"),
        (292.5, 337.5, "북서"),
    ]
    for lo, hi, label in dirs:
        if lo <= az_deg < hi:
            return label
    return "북"


async def get_visible_variable_stars(n_results: int = 3) -> list:
    """현재 시각에 관측 가능한 변광성 상위 n개 반환."""
    stars = await fetch_vsx_stars()

    kst = timezone(timedelta(hours=9))
    now = Time(datetime.now(kst))
    frame = AltAz(obstime=now, location=OBSERVER_LOCATION)

    # 천문박명 확인 (태양 고도 < -18°)
    try:
        sun = get_body("sun", now, location=OBSERVER_LOCATION)
        sun_alt = float(sun.transform_to(frame).alt.deg)
        if sun_alt > -18:
            return []
    except Exception:
        pass

    results = []
    for star in stars:
        try:
            altaz = star["coord"].transform_to(frame)
            alt = float(altaz.alt.deg)
            if alt < MIN_ALTITUDE_DEG:
                continue
            az = float(altaz.az.deg)
            results.append({
                **star,
                "altitude":  alt,
                "azimuth":   az,
                "direction": _azimuth_to_direction(az),
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["altitude"], reverse=True)
    return results[:n_results]
