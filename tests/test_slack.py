import unittest

from unittest.mock import patch

from comet_example.comet.slack_wrapper import SlackWrapper, NoDestinationDefined, NoBotTokenDefined

class SlackWrapperTests(unittest.TestCase):
    def test_bad_params(self):
        with self.assertRaises(TypeError):
            s = SlackWrapper()

    def test_no_destination(self):
        s = SlackWrapper(webhook='faker')
        s.webhook = None
        with self.assertRaises(NoDestinationDefined):
            s.post('Title', 'Body', 'Owner')

    def test_mapping_no_bot_token(self):
        s = SlackWrapper(webhook='faker')
        s.webhook = None
        s.mapping = { 
                SlackWrapper.SLACK_BOT_TOKEN: None, 
                SlackWrapper.SLACK_DEFAULT: '#channel' }

        with self.assertRaises(NoBotTokenDefined):
            s.post('Title', 'Body', 'Owner')

    def test_mapping_default_dest(self):
        s = SlackWrapper(webhook='faker')
        s.webhook = None
        s.mapping = { 
                SlackWrapper.SLACK_BOT_TOKEN: None, 
                SlackWrapper.SLACK_DEFAULT: '#channel' }

        r = s.get_destination_from_owner('non-existant')
        self.assertEqual(r, '#channel')

    def test_env_no_bot_token(self):
        s = SlackWrapper(webhook='faker')
        s.webhook = None

        env = { SlackWrapper.SLACK_DEFAULT: '#channel' }
        with patch.dict('os.environ', env):
            with self.assertRaises(NoBotTokenDefined):
                s.post('Title', 'Body', 'Owner')

    def test_env_default_dest(self):
        s = SlackWrapper(webhook='faker')
        s.webhook = None

        env = { SlackWrapper.SLACK_DEFAULT: '#channel' }
        with patch.dict('os.environ', env):
            r = s.get_destination_from_owner('non-existant')
            self.assertEqual(r, '#channel')


if __name__ == '__main__':
    unittest.main()
