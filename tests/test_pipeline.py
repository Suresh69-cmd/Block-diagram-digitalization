import unittest

from src.pipeline import run_pipeline


class TestPipeline(unittest.TestCase):
    def test_dummy_pipeline_returns_valid_diagram_json(self):
        result = run_pipeline("data/sample/sample_diagram.png")

        self.assertEqual(result["diagram"]["type"], "control_system_block_diagram")
        self.assertEqual(result["diagram"]["block_count"], 3)
        self.assertEqual(result["diagram"]["text_count"], 3)
        self.assertEqual(result["diagram"]["connection_count"], 3)


if __name__ == "__main__":
    unittest.main()
