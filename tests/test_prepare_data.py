"""Tests for the mentor data-preparation pipeline."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from prepare_data import (
    DataPreparationError,
    classify_transport,
    prepare_data,
    validate_outputs,
)


def _write_csv(directory: Path, filename: str, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_csv(directory / filename, index=False)


class PrepareDataTests(unittest.TestCase):
    def test_classify_transport_uses_extended_swedish_codes(self) -> None:
        self.assertEqual(classify_transport("401"), "Metro")
        self.assertEqual(classify_transport("700"), "Bus")
        self.assertEqual(classify_transport("900"), "Tram")
        self.assertEqual(classify_transport("1000"), "Ferry")
        self.assertEqual(
            classify_transport("106", "Pendeltåg", "40"),
            "Commuter train / Pendeltåg",
        )
        self.assertEqual(
            classify_transport("106", "Roslagsbanan", "27"),
            "Local train / Roslagsbanan",
        )
        self.assertEqual(
            classify_transport("106", "", "25"),
            "Local train / Saltsjöbanan",
        )

    def test_prepare_data_filters_groups_and_deduplicates(self) -> None:
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        tmp_path = Path(temporary_directory.name)
        raw_dir = tmp_path / "raw"
        output_dir = tmp_path / "output"
        raw_dir.mkdir()
        output_dir.mkdir()

        _write_csv(
            raw_dir,
            "stops.txt",
            [
                {
                    "stop_id": "stop-a",
                    "stop_name": "Central Metro",
                    "stop_lat": 59.33,
                    "stop_lon": 18.05,
                },
                {
                    "stop_id": "stop-b",
                    "stop_name": "Central Bus",
                    "stop_lat": 59.331,
                    "stop_lon": 18.051,
                },
                {
                    "stop_id": "stop-c",
                    "stop_name": "Square",
                    "stop_lat": 59.332,
                    "stop_lon": 18.052,
                },
                {
                    "stop_id": "outside",
                    "stop_name": "Outside",
                    "stop_lat": 60.0,
                    "stop_lon": 18.05,
                },
            ],
        )
        _write_csv(
            raw_dir,
            "routes.txt",
            [
                {
                    "route_id": "metro",
                    "agency_id": "275",
                    "route_short_name": "10",
                    "route_long_name": "",
                    "route_type": "401",
                },
                {
                    "route_id": "bus",
                    "agency_id": "275",
                    "route_short_name": "1",
                    "route_long_name": "",
                    "route_type": "700",
                },
                {
                    "route_id": "excluded-bus",
                    "agency_id": "275",
                    "route_short_name": "999",
                    "route_long_name": "",
                    "route_type": "700",
                },
            ],
        )
        _write_csv(
            raw_dir,
            "trips.txt",
            [
                {
                    "trip_id": "metro-1",
                    "route_id": "metro",
                    "trip_headsign": "Hjulsta",
                },
                {
                    "trip_id": "metro-2",
                    "route_id": "metro",
                    "trip_headsign": "Hjulsta",
                },
                {
                    "trip_id": "bus-1",
                    "route_id": "bus",
                    "trip_headsign": "Frihamnen",
                },
                {
                    "trip_id": "excluded-1",
                    "route_id": "excluded-bus",
                    "trip_headsign": "Nowhere",
                },
            ],
        )
        _write_csv(
            raw_dir,
            "stop_times.txt",
            [
                {"trip_id": "metro-1", "stop_id": "stop-a", "stop_sequence": 1},
                {"trip_id": "metro-1", "stop_id": "stop-c", "stop_sequence": 2},
                {"trip_id": "metro-2", "stop_id": "stop-a", "stop_sequence": 1},
                {"trip_id": "metro-2", "stop_id": "stop-c", "stop_sequence": 2},
                {"trip_id": "bus-1", "stop_id": "stop-b", "stop_sequence": 1},
                {"trip_id": "bus-1", "stop_id": "stop-c", "stop_sequence": 2},
                {
                    "trip_id": "excluded-1",
                    "stop_id": "stop-a",
                    "stop_sequence": 1,
                },
                {"trip_id": "metro-1", "stop_id": "outside", "stop_sequence": 3},
            ],
        )
        groups_path = output_dir / "station_groups.csv"
        _write_csv(
            output_dir,
            "station_groups.csv",
            [
                {
                    "stop_id": "stop-a",
                    "station_id": "central",
                    "station_name": "Central",
                },
                {
                    "stop_id": "stop-b",
                    "station_id": "central",
                    "station_name": "Central",
                },
            ],
        )

        stations, services, line_patterns = prepare_data(
            raw_data_dir=raw_dir,
            output_dir=output_dir,
            station_groups_path=groups_path,
            chunk_size=2,
            min_stations=1,
            max_stations=10,
        )

        station_records = stations.to_dict("records")
        self.assertEqual(len(station_records), 2)
        self.assertEqual(station_records[0]["station_id"], "central")
        self.assertEqual(station_records[0]["station_name"], "Central")
        self.assertAlmostEqual(station_records[0]["latitude"], 59.3305)
        self.assertAlmostEqual(station_records[0]["longitude"], 18.0505)
        self.assertEqual(station_records[1]["station_id"], "stop-c")
        self.assertEqual(station_records[1]["station_name"], "Square")
        self.assertEqual(len(services), 4)
        self.assertEqual(line_patterns["pattern_id"].nunique(), 3)
        pattern_lengths = sorted(
            line_patterns.groupby("pattern_id")["stop_sequence"].size()
        )
        self.assertEqual(pattern_lengths, [2, 2, 3])
        self.assertEqual(
            set(line_patterns["station_id"]), {"central", "stop-c", "outside"}
        )
        self.assertIn("Outside", set(line_patterns["station_name"]))
        self.assertTrue((output_dir / "stations.csv").exists())
        self.assertTrue((output_dir / "stop_services.csv").exists())
        self.assertTrue((output_dir / "line_patterns.csv").exists())

    def test_validation_rejects_services_for_unknown_stations(self) -> None:
        stations = pd.DataFrame(
            [
                {
                    "station_id": "known",
                    "station_name": "Known",
                    "latitude": 59.33,
                    "longitude": 18.05,
                }
            ]
        )
        services = pd.DataFrame(
            [
                {
                    "station_id": "missing",
                    "transport_type": "Metro",
                    "line": "10",
                    "destination": "Hjulsta",
                }
            ]
        )
        line_patterns = pd.DataFrame(
            [
                {
                    "pattern_id": "pattern-1",
                    "route_id": "route-1",
                    "transport_type": "Metro",
                    "line": "10",
                    "direction": "Hjulsta",
                    "station_id": "known",
                    "station_name": "Known",
                    "latitude": 59.33,
                    "longitude": 18.05,
                    "stop_sequence": 1,
                },
                {
                    "pattern_id": "pattern-1",
                    "route_id": "route-1",
                    "transport_type": "Metro",
                    "line": "10",
                    "direction": "Hjulsta",
                    "station_id": "known",
                    "station_name": "Known",
                    "latitude": 59.33,
                    "longitude": 18.05,
                    "stop_sequence": 2,
                },
            ]
        )

        with self.assertRaisesRegex(DataPreparationError, "missing from stations.csv"):
            validate_outputs(
                stations,
                services,
                line_patterns,
                min_stations=1,
                max_stations=10,
            )


if __name__ == "__main__":
    unittest.main()
