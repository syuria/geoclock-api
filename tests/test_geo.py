import pytest

from app.geo import distance_m


def test_same_point_is_zero():
    assert distance_m(51.5, -0.12, 51.5, -0.12) == 0


def test_london_to_leeds_is_about_270_km():
    # Charing Cross to Leeds city centre, straight line.
    assert distance_m(51.5074, -0.1278, 53.7997, -1.5492) == pytest.approx(272_000, rel=0.02)
