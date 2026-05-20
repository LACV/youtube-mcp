"""Basic tests for YouTube scheduler."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube.scheduler import calculate_next_schedule
from youtube.upload import generate_title, generate_hashtags


def test_generate_title():
    title = generate_title("el_cuchillo_en_la_sombra")
    assert title == "El Cuchillo En La Sombra"


def test_generate_hashtags():
    hashtags = generate_hashtags("El Cuchillo En La Sombra")
    assert "#El" in hashtags or "#Cuchillo" in hashtags
    assert len(hashtags) > 0


def test_calculate_next_schedule():
    scheduled = []
    result = calculate_next_schedule(scheduled)
    assert " " in result  # Should have date and time


if __name__ == "__main__":
    test_generate_title()
    test_generate_hashtags()
    test_calculate_next_schedule()
    print("✅ All tests passed!")
