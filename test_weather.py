import io
import json
import unittest
from unittest.mock import patch

import weather


CITIES_TEXT = "Moscow\nVienna\n"

WEATHER_JSON = {
    "current_condition": [{"temp_C": "12"}],
    "nearest_area": [{"country": [{"value": "Russia"}]}],
}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class FetchCitiesTests(unittest.TestCase):
    @patch("weather.http_get", return_value=CITIES_TEXT.encode())
    def test_returns_stripped_lines(self, _mock):
        self.assertEqual(weather.fetch_cities("http://x"), ["Moscow", "Vienna"])

    @patch("weather.http_get", return_value=b"\n\n  Moscow  \n\n")
    def test_ignores_blank_lines(self, _mock):
        self.assertEqual(weather.fetch_cities("http://x"), ["Moscow"])


class FetchWeatherTests(unittest.TestCase):
    @patch("weather.http_get", return_value=json.dumps(WEATHER_JSON).encode())
    def test_extracts_city_country_temp(self, _mock):
        self.assertEqual(
            weather.fetch_weather("Moscow"),
            weather.WeatherData(city="Moscow", country="Russia", temp_c=12.0),
        )

    @patch("weather.http_get", return_value=json.dumps({"current_condition": [{"temp_C": "5"}]}).encode())
    def test_missing_country_defaults_to_empty(self, _mock):
        self.assertEqual(weather.fetch_weather("Nowhere").country, "")


class HttpGetTests(unittest.TestCase):
    @patch("weather.urllib.request.urlopen", side_effect=TimeoutError)
    @patch("weather.time.sleep")
    def test_retries_then_raises(self, _sleep, urlopen):
        with self.assertRaises(TimeoutError):
            weather.http_get("http://x", timeout=1, retries=3)
        self.assertEqual(urlopen.call_count, 3)

    @patch("weather.urllib.request.urlopen", return_value=FakeResponse(b"ok"))
    def test_returns_body(self, _urlopen):
        self.assertEqual(weather.http_get("http://x"), b"ok")


class StatsTests(unittest.TestCase):
    def test_country_grouping(self):
        results = [
            weather.WeatherData(city="Moscow", country="Russia", temp_c=12.0),
            weather.WeatherData(city="Perm", country="Russia", temp_c=8.0),
            weather.WeatherData(city="Vienna", country="Austria", temp_c=16.0),
        ]
        by_country = weather.group_by_country(results)

        self.assertEqual(sorted(by_country), ["Austria", "Russia"])
        self.assertEqual(sorted(by_country["Russia"]), [8.0, 12.0])
        self.assertEqual(sorted(by_country["Austria"]), [16.0])


if __name__ == "__main__":
    unittest.main()
