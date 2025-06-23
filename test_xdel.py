import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
# Make sure XDel is imported after mocks are potentially set up, or patch its imports.
# from XDel import XReplyDeleter # Moved to after imports within test methods if needed

class TestXDelDateValidation(unittest.TestCase):

    @patch('XDel.ttk') # Patch ttk where it's imported in XDel.py
    @patch('XDel.tk')  # Patch tk where it's imported in XDel.py
    def setUp(self, mock_tk, mock_ttk): # Order of args is important, last decorator first
        # Import XReplyDeleter here, after mocks are in place for its module-level imports
        from XDel import XReplyDeleter

        # Configure the mocks for tk and ttk that XReplyDeleter uses
        # Mocking classes and functions called within XReplyDeleter.__init__
        mock_tk.Label = MagicMock()

        # For Entry, the instance needs to be mockable too if methods are called on it
        mock_entry_instance = MagicMock()
        mock_entry_instance.pack = MagicMock()
        mock_entry_instance.insert = MagicMock()
        mock_entry_instance.get = MagicMock(return_value="test_user") # Example
        mock_tk.Entry = MagicMock(return_value=mock_entry_instance)

        mock_tk.Button = MagicMock()

        mock_stringvar_instance = MagicMock()
        mock_stringvar_instance.get = MagicMock(return_value="Replies") # Example
        mock_tk.StringVar = MagicMock(return_value=mock_stringvar_instance)

        mock_combobox_instance = MagicMock()
        mock_combobox_instance.pack = MagicMock()
        mock_combobox_instance.current = MagicMock()
        mock_combobox_instance.__setitem__ = MagicMock()
        mock_ttk.Combobox = MagicMock(return_value=mock_combobox_instance)

        mock_ttk.Progressbar = MagicMock()

        # Create a mock root object. XReplyDeleter calls root.title and root.geometry.
        mock_root = MagicMock()
        mock_root.title = MagicMock()
        mock_root.geometry = MagicMock()

        # Instantiate the class with the mocked root and patched tk/ttk
        self.deleter = XReplyDeleter(mock_root)
        # Also, XReplyDeleter imports messagebox and parse directly.
        # If these cause issues for instantiation (they don't for validate_dates),
        # they might need patching too, e.g. @patch('XDel.messagebox')

    def test_valid_dates(self):
        start, end, error = self.deleter.validate_dates("2023-01-01", "2023-01-31")
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertIsNone(error)
        self.assertEqual(start, datetime(2023, 1, 1))
        self.assertEqual(end, datetime(2023, 1, 31))

    def test_invalid_date_format(self):
        start, end, error = self.deleter.validate_dates("01-01-2023", "2023-01-31")
        self.assertIsNone(start)
        self.assertIsNone(end)
        self.assertEqual(error, "Invalid date format! Use YYYY-MM-DD")

        start, end, error = self.deleter.validate_dates("2023/01/01", "2023-01-31")
        self.assertIsNone(start)
        self.assertIsNone(end)
        self.assertEqual(error, "Invalid date format! Use YYYY-MM-DD")

        start, end, error = self.deleter.validate_dates("2023-13-01", "2023-12-31") # Invalid month
        self.assertIsNone(start)
        self.assertIsNone(end)
        self.assertEqual(error, "Invalid date format! Use YYYY-MM-DD")

    def test_start_date_after_end_date(self):
        start, end, error = self.deleter.validate_dates("2023-01-31", "2023-01-01")
        self.assertIsNone(start)
        self.assertIsNone(end)
        self.assertEqual(error, "Start date must be before end date!")

    def test_same_start_and_end_date(self):
        start, end, error = self.deleter.validate_dates("2023-01-01", "2023-01-01")
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertIsNone(error)
        self.assertEqual(start, datetime(2023, 1, 1))
        self.assertEqual(end, datetime(2023, 1, 1))

    def test_empty_start_date(self):
        start, end, error = self.deleter.validate_dates("", "2023-01-31")
        self.assertIsNone(start)
        self.assertIsNone(end)
        self.assertEqual(error, "Please fill all date fields!")

    def test_empty_end_date(self):
        start, end, error = self.deleter.validate_dates("2023-01-01", "")
        self.assertIsNone(start)
        self.assertIsNone(end)
        self.assertEqual(error, "Please fill all date fields!")

    def test_empty_both_dates(self):
        start, end, error = self.deleter.validate_dates("", "")
        self.assertIsNone(start)
        self.assertIsNone(end)
        self.assertEqual(error, "Please fill all date fields!")

    def tearDown(self):
        # Clean up the dummy root if it was created
        if hasattr(self, 'dummy_root') and self.dummy_root:
            try:
                self.dummy_root.destroy()
            except Exception:
                pass # Ignore errors during destroy

if __name__ == "__main__":
    unittest.main()
