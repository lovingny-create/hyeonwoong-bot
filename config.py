"""
망원경 및 관측소 상수 정의
광주과학고등학교 CDK14 + Moravian C3-61000 PRO 기준
"""

from astropy.coordinates import EarthLocation
import astropy.units as u

# ─── 관측소 위치 ───────────────────────────────────────────
OBSERVER_LOCATION = EarthLocation(
    lat=35.17 * u.deg,
    lon=126.85 * u.deg,
    height=50 * u.m,
)
OBSERVER_TIMEZONE = "Asia/Seoul"

# ─── 망원경: PlaneWave CDK14 ──────────────────────────────
APERTURE_MM = 356.0          # 구경 (mm)
FOCAL_LENGTH_MM = 2563.0     # 초점거리 (mm)
FOCAL_RATIO = 7.2            # f/7.2

# ─── 카메라: Moravian C3-61000 PRO (Sony IMX455) ─────────
PIXEL_SIZE_UM = 3.76         # 픽셀 크기 (μm)
SENSOR_W = 9576              # 가로 픽셀 수
SENSOR_H = 6388              # 세로 픽셀 수

# ─── 계산값 ───────────────────────────────────────────────
# 플레이트 스케일: 206265 * pixel_size(mm) / focal_length(mm)
PLATE_SCALE_ARCSEC_PX = 206265 * (PIXEL_SIZE_UM / 1000) / FOCAL_LENGTH_MM  # ≈ 0.303
FOV_W_ARCMIN = PLATE_SCALE_ARCSEC_PX * SENSOR_W / 60   # ≈ 48.4'
FOV_H_ARCMIN = PLATE_SCALE_ARCSEC_PX * SENSOR_H / 60   # ≈ 32.3'
FOV_W_DEG = FOV_W_ARCMIN / 60
FOV_H_DEG = FOV_H_ARCMIN / 60

# ─── 필터 ────────────────────────────────────────────────
FILTERS = ["U", "B", "V", "R", "I"]

# 필터별 대략적 권장 노출 시간 가이드 (초)
# (밝은 성운/성단, 은하/어두운 천체)
FILTER_EXPOSURE_GUIDE = {
    "U": (120, 600),
    "B": (60, 300),
    "V": (30, 180),
    "R": (30, 180),
    "I": (45, 240),
}

# ─── 관측 제약 ────────────────────────────────────────────
MIN_ALTITUDE_DEG = 30.0      # 최소 고도 (°)
LIMITING_MAG = 13.0          # 추천 한계등급

# ─── Claude API ───────────────────────────────────────────
CLAUDE_MODEL = "claude-haiku-4-5"   # 응답 속도 우선
CLAUDE_MAX_TOKENS = 512
