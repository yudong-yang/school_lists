import tempfile
import unittest
from pathlib import Path

from school_list.models import University
from school_list.repository import UniversityRepository
from school_list.web import create_app


class FlaskWebTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "schools.db"
        self.repo = UniversityRepository(self.db_path)
        for index in range(25):
            self.repo.add(
                University(
                    name=f"测试大学{index}",
                    province="北京",
                    city="北京",
                    level="本科",
                    school_type="综合",
                    ownership="公立",
                    address=f"北京市海淀区{index}号",
                    icon_url="https://example.com/logo.png",
                    badges="985、211",
                )
            )
        self.client = create_app(self.db_path).test_client()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_index_page_uses_frontend_assets(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("学校列表", html)
        self.assertIn("schools.js", html)

    def test_schools_api_returns_paginated_data(self):
        response = self.client.get("/api/schools?page=1&page_size=20")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["pagination"]["total"], 25)
        self.assertEqual(payload["pagination"]["total_pages"], 2)
        self.assertEqual(len(payload["items"]), 20)
        self.assertEqual(payload["items"][0]["school_type"], "综合")
        self.assertEqual(payload["items"][0]["badge_list"], ["985", "211"])

    def test_school_detail_api_returns_one_school(self):
        response = self.client.get("/api/schools/1")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["name"], "测试大学0")
        self.assertEqual(payload["display_location"], "北京市海淀区0号")


if __name__ == "__main__":
    unittest.main()
