import logging
import requests

from os import getenv
from json import load

class NoDestinationDefined(Exception):
    pass

class NoBotTokenDefined(Exception):
    pass

class SlackWrapper:
    EP_POST_MSG = 'https://slack.com/api/chat.postMessage'

    # Default webhook or channel if no mapping exists
    SLACK_DEFAULT = 'SLACK_DEFAULT' 

    # Single webhook that all alerts to send to
    SLACK_WEBHOOK = 'SLACK_WEBHOOK'

    # Bot Token, required when posting to channels without using webhooks
    SLACK_BOT_TOKEN = 'SLACK_BOT_TOKEN'

    def __init__(self, webhook=None, mapping_filename=None, use_env=False):
        """A wrapper class to assist Comet in outputing alerts to Slack. 
        This aims to solve the challenge of posting alerts to slack and
        determing what channels alerts go to by resolving owners to 
        webhook URLs or channels. 
            
        Keyword Arguments:
        webhook -- (URL) for a single, catch-all webhook. This must be generated
            from App's configuration page under 'Incoming Webhooks'
        mapping_filename -- (JSON filename) Just a simple key/value store that supports 
            both webhooks (starts with 'http') and channels. Channels start with '#' and
            requires 'bot_token' field to be defined with the bot token from the 
            'OAuth & Permissions' App configuration page. The 'bot_token' field can 
            also be defined in the SLACK_BOT_TOKEN environment variable. This mapping is 
            to map email addresses to  slack channels. 
        use_env -- (Boolean) ignore webhook/bot_token checks and expect them in 
            environment variables
        """
        if webhook is None and mapping_filename is None and not use_env:
            raise TypeError("No webhook or mapping defined, and use_env is False,"
                " dont know where to send messages!")

        self.logger = logging.getLogger(__name__)

        self.webhook = webhook
        self.bot_token = None

        self.mapping = None
        if mapping_filename is not None:
            with open(mapping_filename) as f:
                self.mapping = load(f)

    def _is_webhook(self, key):
        """helper to determine if a key in the mapping looks like a 
        webhook
        """
        return ( key in self.mapping and self.mapping[key] and 
                self.mapping[key].startswith('http') )

    def _is_channel(self, key):
        """helper to determine if a key in the mapping looks like a 
        channel 
        """
        return ( key in self.mapping and self.mapping[key] and 
                self.mapping[key].startswith('#') )

    def _get_webhook(self):
        if self.webhook is None:
            if self.mapping is not None:
                # First look in the mapping for a bot token
                if self._is_webhook(self.SLACK_WEBHOOK):
                    # Webhook might be in the SLACK_WEBHOOK key of the mapping
                    self.webhook = self.mapping[self.SLACK_WEBHOOK]
                elif self._is_webhook(self.SLACK_DEFAULT):
                    # A default key might also exist
                    self.webhook = self.mapping[self.SLACK_DEFAULT]
                else:
                    # Check environment variables
                    self.webhook = getenv(self.SLACK_WEBHOOK, None)
            else:
                # Can't find a mapping then check environment variable
                self.webhook = getenv(self.SLACK_WEBHOOK, None)

        return self.webhook

    def _get_bot_token(self):
        if self.bot_token is None:
            if self.mapping is not None and self.SLACK_BOT_TOKEN in self.mapping:
                # First look in the mapping for a bot token
                self.bot_token = self.mapping[self.SLACK_BOT_TOKEN]
            else:
                # Can't find it in mapping, goto env
                self.bot_token = getenv(self.SLACK_BOT_TOKEN, None)

        return self.bot_token

    def get_destination_from_owner(self, owner):
        if self.mapping is not None:
            if owner in self.mapping and self.mapping[owner]:
                # If we have a mapping, return it! 
                return self.mapping[owner]

            if self._is_channel(self.SLACK_DEFAULT):
                return self.mapping[self.SLACK_DEFAULT]

            # self._get_webhook() also looks at mapping, so no need to add it here

        webhook = self._get_webhook()
        if webhook is not None:
            return webhook

        # No webhooks here, so its either a channel, or nothing
        return getenv(self.SLACK_DEFAULT, None)
        

    @staticmethod
    def get_slack_msg(title, text, channel=None):
        """Single place to call so alerts are standardized accross Webhooks
        and bot users. 

        Keyword Arguments:
        title -- (String) Title of the slack message to be sent
        text -- (String) Body of the slack message to be sent
        """
        return { 'text': None, 'channel': channel, 
                'attachments': [ { 'title': title, 'text': text } ] }

    @staticmethod
    def post_via_webhook(title, text, webhook):
        """Barebones helper method to post via a slack message via 
        a webhook. It might be a good idea to account for exception
        handling in the caller.

        Keyword Arguments:
        title -- (String) Title of the slack message to be sent
        text -- (String) Body of the slack message to be sent
        webhook -- (URL) Where to send the slack message

        Returns: 
        True/False if the post was successful
        """
        msg = SlackWrapper.get_slack_msg(title, text)
        r = requests.post(webhook, json = msg)
        return bool(r.text == 'ok')

    @staticmethod
    def post_via_bot_token(title, text, token, channel):
        """Barebones helper method to post via a slack message via 
        a bot user. It might be a good idea to account for exception
        handling in the caller.

        Keyword Arguments:
        title -- (String) Title of the slack message to be sent
        text -- (String) Body of the slack message to be sent
        token -- (Bot Token) The bot token (starts with `xoxb`)
        channel -- (String) Which channel to send alerts to

        Returns: 
        True/False if the post was successful
        """
        msg = SlackWrapper.get_slack_msg(title, text, channel=channel)

        r = requests.post(SlackWrapper.EP_POST_MSG, 
                headers = {'Authorization': 'Bearer {}'.format(token) },
                json = msg).json()
        return bool( 'ok' in r and r['ok'] is True )

    def post(self, title, text, owner):
        dst = self.get_destination_from_owner(owner)

        if dst is None:
            raise NoDestinationDefined('No destination defined for owner, cannot output via Slack')

        success = False

        if dst.startswith('http'):
            success = SlackWrapper.post_via_webhook(title, text, dst)

        elif dst.startswith('#'):
            token = self._get_bot_token()

            if token is None:
                raise NoBotTokenDefined('Destination is channel, but not bot token has been defined')
            
            success = SlackWrapper.post_via_bot_token(title, text, token, dst)
        
        return success 

