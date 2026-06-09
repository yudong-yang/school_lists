import unittest

from school_list.models import University
from school_list.web import _render_detail_body, _render_index_body


class WebRenderTest(unittest.TestCase):
    def test_index_contains_required_card_content_and_detail_link(self):
        html = _render_index_body(
            [
                University(
                    id=1,
                    name="清华大学",
                    province="北京",
                    level="985",
                    school_type="综合",
                    ownership="公立",
                    address="北京市海淀区清华园1号",
                    icon_url="https://example.com/logo.png",
                    website="https://www.tsinghua.edu.cn",
                )
            ],
            keyword="",
            level="",
        )

        self.assertIn("清华大学", html)
        self.assertIn("985", html)
        self.assertIn("综合", html)
        self.assertIn("北京市海淀区清华园1号", html)
        self.assertIn("公立", html)
        self.assertIn("https://example.com/logo.png", html)
        self.assertIn("/schools/1", html)

    def test_detail_contains_school_information(self):
        html = _render_detail_body(
            University(
                id=1,
                name="清华大学",
                province="北京",
                level="985",
                address="北京市海淀区清华园1号",
                website="https://www.tsinghua.edu.cn",
            )
        )

        self.assertIn("清华大学", html)
        self.assertIn("985", html)
        self.assertIn("北京市海淀区清华园1号", html)


if __name__ == "__main__":
    unittest.main()
