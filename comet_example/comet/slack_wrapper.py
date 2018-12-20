import logging
import requests

from os import getenv
from json import load

class SlackWrapper:
    """A wrapper class to assist Comet in outputing alerts to Slack. 
        This aims to solve the challenge of posting alerts to slack and
        determing what channels alerts go to be resolving domains to 
        webhook URLs. 
        
        It assumes that someone manually generates a Webhook in the Slack
        Org and then populates the webhook db.
        """
    def __init__(self, webhook=None, webhook_db=None):
        """
        Keyword Arguments:
            webhook -- (URL) for a single, catch-all webhook
            webhook_db -- (JSON file) for a simple webhook db implementation
        """
        if webhook is None and webhook_db is None:
            raise Exception(
                    'Please define a webhook or a webhook database when using this class')

        self.webhook = webhook

        # Just a real simple way to look up the appropriate webhook 
        self.webhook_db = webhook_db
        if self.webhook_db is not None:
            with open(webhook_db) as f:
                self.webhook_db = load(f)

        self.logger = logging.getLogger(__name__)

    def _get_webhook(self):
        # Just for testing really. 
        if self.webhook is None:
            self.webhook = getenv('SLACK_WEBHOOK', None)
        return self.webhook

    def get_webhook_from_owner(self, owner):
        # TODO: Some db lookup functionality to map owner to webhook
        if self.webhook_db is None:
            return self._get_webhook()
        
        if owner in self.webhook_db:
            return self.webhook_db[owner]

        if 'default' in self.webhook_db:
            return self.webhook_db['default']

        return self._get_webhook()

    @staticmethod
    def post_msg(title, text, webhook):
        """For those that don't want to go through class instantiation, and just 
        want something to send slack message, this method can be called directly. 
        Best to add in your own exception handling. 
        """
        r = requests.post(webhook, json = {
            'text': None,
            'attachments': [
                { 
                    'title': title,
                    'text': text
                    }
                ]
            })
        return bool(r.text == 'ok')

    def post(self, title, text, owner):
        webhook = self.get_webhook_from_owner(owner)
        if webhook is None:
            raise Exception('No webhook defined, cannot post to Slack!')

        try:
            if not SlackWrapper.post_msg(title, text, webhook):
                raise Exception('Post to webhook returned non-"ok" response')
        except (Exception) as e:
            self.logger.error("Exception raised when posting to Slack: "
                    "{} ".format(e))
            return False

        return True

if __name__ == '__main__':
    c = SlackWrapper(webhook = 
            'ENTER_WEBHOOK')
    c.post('Alert', 'Something happened OMG WUT!?', None)
