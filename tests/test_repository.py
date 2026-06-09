import tempfile
import unittest
from pathlib import Path

from school_list.models import University
from school_list.repository import UniversityRepository


class UniversityRepositoryTest(unittest.TestCase):
    def test_add_and_search_university(self):
        with self.subTest("stores and filters a university"):
            with tempfile.TemporaryDirectory() as tmp_dir:
                repo = UniversityRepository(Path(tmp_dir) / "schools.db")

                university_id = repo.add(
                    University(
                        name="清华大学",
                        province="北京",
                        city="北京",
                        level="本科",
                        school_type="综合",
                    )
                )

                results = repo.search(province="北京")

                self.assertEqual(university_id, 1)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].name, "清华大学")

    def test_requires_name_and_province(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = UniversityRepository(Path(tmp_dir) / "schools.db")

            with self.assertRaises(ValueError):
                repo.add(University(name="", province="北京"))

            with self.assertRaises(ValueError):
                repo.add(University(name="清华大学", province=""))


if __name__ == "__main__":
    unittest.main()
