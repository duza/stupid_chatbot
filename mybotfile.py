import time
import os
import slackclient

GREETINGS = ('hi', 'hello', 'hey',)


def open(token):
    return StubAPI(token)


def open_slack(token):
    return Slack(token)


class StubAPI:

    def __init__(self, token):
        self.token = token

    def read(self):
        return [Message('Que tal?'),
                Message('/teapot test'),
                Message('Just msg'), Message('Hi')
                ]

    def write(self, messages):
        print(messages)

    def is_connected(self):
        return True

    def is_server_connected(self):
        return True


class Slack(StubAPI):
    def __init__(self, token):
        super().__init__(token)
        self.sc = slackclient.SlackClient(token)

    def is_connected(self, *args, **kwargs):
        return self.sc.rtm_connect(*args, **kwargs)

    def is_server_connected(self):
        return self.sc.server.connected

    def read(self):
        # This method returns not Message objects but raw events from Slack API
        # This means that other functions should know about expected structure
        # and this breaks the idea of Single Responsibility and code isolation
        events = self.sc.rtm_read()
        if events:
            return [
                Message(
                    event.get('text'),
                    event.get('channel'),
                    self.get_author(event.get('user')),
                )
                for event in events if event.get('type') == 'message'
            ]
        return []

    def write(self, messages):
        self.sc.rtm_send_message(messages.channel, messages.text)

    def get_user(self, user_id):
        resp = self.sc.api_call('users.info', user=user_id)
        if not resp['ok']:
            raise ValueError('User not found')
        return resp.get('user')

    def get_author(self, user_id):
        if user_id:
            author = {}
            author['id'] = user_id
            user = self.get_user(user_id)
            author['name'] = user['name']
            author['real_name'] = user['real_name']
            return author
        return None


class Message:
    def __init__(self, text, channel=None, author=None):
        self.text = text
        self.channel = channel
        self.author = author

    def __repr__(self):
        return '<Message: text="{}", channel="{}", author="{}">'.format(
            self.text, self.channel, self.author)


def is_greeting(lowercased_text):
    """This small function makes a decision. We can test it also ;)
    >>> is_greeting('hello, world')
    True
    >>> is_greeting('hey jude')
    True
    >>> is_greeting('hi there')
    True
    >>> is_greeting('¡hola!')
    False
    >>> is_greeting('chip and dale')
    True
    """
    return any(phrase in lowercased_text for phrase in GREETINGS)


def process(messages):
    responses = []
    for msg in messages:
        if isinstance(msg, Message):
            text, channel, author = msg.text, msg.channel, msg.author
            if channel and is_greeting(text.lower()):
                name = author.get('real_name', 'Unknown')
                responses.append(Message('Hi, {}!'.format(name), msg.channel))
            # elif text.startswith('/teapot'):
            # responses.append(teapot())
            # elif msg.text.startswith('/author'):
            # responses.append(teapot())
            else:
                echo(msg)
    return responses


def echo(message):
    return message


def teapot():
    return Message('Standart message')


def author():
    return Message('Pavel Mikhadziuk')


def main():
    incoming_queue = []
    outgoing_queue = []
    custom_api = open_slack(os.environ["SLACK_API_TOKEN"])
    if not custom_api.is_connected():
        print('Connection failed')
        exit(1)
    while custom_api.is_server_connected() is True:
        if outgoing_queue:
            for outgoing_message in outgoing_queue:
                custom_api.write(outgoing_message)
            outgoing_queue.clear()
        incoming_queue = custom_api.read()
        print(incoming_queue)
        if incoming_queue:
            outgoing_queue.extend(process(incoming_queue))
        time.sleep(10)


if __name__ == '__main__':
    main()
