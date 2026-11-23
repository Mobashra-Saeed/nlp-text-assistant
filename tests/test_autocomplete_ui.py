import unittest

from app import app


class AutocompleteUiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_autocomplete_control_is_exposed_in_the_ui(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('editor-autocomplete', html)
        self.assertIn('autocomplete-results', html)
        self.assertNotIn('autocomplete-input', html)


if __name__ == '__main__':
    unittest.main()
