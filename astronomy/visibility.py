"""
astroplan을 사용한 천체 가시성 계산.
CDK14 관측소 위치 기준으로 고도 30° 이상, 천문박명 이후 조건 확인.
"""

from astroplan import Observer, FixedTarget, AltitudeConstraint, AtNightConstraint
from astroplan import is_observable
from astropy.time import Time
from astropy.coordinates import get_body_barycentric, get_body, AltAz
import astropy.units as u
from datetime import datetime, timezone, timedelta

from config import OBSERVER_LOCATION, OBSERVER_TIMEZONE, MIN_ALTITUDE_DEG, LIMITING_MAG
from astronomy.catalog import FIXED_CATALOG, SOLAR_SYSTEM_TARGETS

# 모듈 레벨에서 Observer 초기화 (요청마다 생성하지 않음)
_observer = Observer(location=OBSERVER_LOCATION, timezone=OBSERVER_TIMEZONE)

_CONSTRAINTS = [
    AltitudeConstraint(min=MIN_ALTITUDE_DEG * u.deg),
    AtNightConstraint.twilight_astronomical(),
]


def _now_kst() -> Time:
    kst = timezone(timedelta(hours=9))
    return Time(datetime.now(kst))


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


def get_visible_fixed_targets(n_results: int = 5) -> list:
    """고정 천체(항성, 성단, 성운, 은하) 중 현재 관측 가능한 상위 n개 반환."""
    now = _now_kst()
    time_range = [now, now + 1 * u.hour]

    results = []
    for obj in FIXED_CATALOG:
        if obj["mag"] > LIMITING_MAG:
            continue
        target = FixedTarget(coord=obj["coord"], name=obj["name"])
        try:
            observable = is_observable(_CONSTRAINTS, _observer, target, time_range=time_range)
        except Exception:
            continue
        if not observable[0]:
            continue
        altaz = _observer.altaz(now, target)
        results.append({
            **obj,
            "altitude": float(altaz.alt.deg),
            "azimuth": float(altaz.az.deg),
            "direction": _azimuth_to_direction(float(altaz.az.deg)),
        })

    results.sort(key=lambda x: x["altitude"], reverse=True)
    return results[:n_results]


def get_visible_solar_system(n_results: int = 3) -> list:
    """태양계 천체 중 현재 관측 가능한 것들 반환."""
    now = _now_kst()
    frame = AltAz(obstime=now, location=OBSERVER_LOCATION)
    results = []

    for obj in SOLAR_SYSTEM_TARGETS:
        try:
            body = get_body(obj["name"], now, location=OBSERVER_LOCATION)
            altaz = body.transform_to(frame)
            alt = float(altaz.alt.deg)
            az = float(altaz.az.deg)
        except Exception:
            continue

        # 낮 시간 체크: 태양 고도 < -18° 이어야 천문박명
        try:
            sun = get_body("sun", now, location=OBSERVER_LOCATION)
            sun_altaz = sun.transform_to(frame)
            if float(sun_altaz.alt.deg) > -18:
                continue
        except Exception:
            pass

        if alt < MIN_ALTITUDE_DEG:
            continue

        results.append({
            "name": obj["name"],
            "label": obj["label"],
            "type": obj["type"],
            "size_arcmin": None,
            "altitude": alt,
            "azimuth": az,
            "direction": _azimuth_to_direction(az),
        })

    results.sort(key=lambda x: x["altitude"], reverse=True)
    return results[:n_results]
