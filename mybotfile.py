import time
import os
import requests
import slackclient


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
        pass
        print(messages)

    def is_connected(self):
        pass

    def is_server_connected(self):
        pass


class Slack(StubAPI):
    def __init__(self, token):
        super().__init__(token)
        self.sc = slackclient.SlackClient(token)

    def is_connected(self, *args, **kwargs):
        return self.sc.rtm_connect(*args, **kwargs)

    def is_server_connected(self):
        return self.sc.server.connected

    def read(self):
        return self.sc.rtm_read()

    def write(self, messages):
        self.sc.rtm_send_message(messages.channel, messages.text)


class Message:

    def __init__(self, text, channel=None, author=None):
        self.text = text
        self.channel = channel
        self.author = author

    def __repr__(self):
        return 'Message with text {} for channel {} written by {}'.format(
            self.text, self.channel, self.author)


def get_slack_user(user_id):
    url_user = 'https://slack.com/api/users.info?token={}&user={}&pretty=1'.format(
        os.environ["SLACK_API_TOKEN"], user_id,
    )
    resp = requests.get(url_user)
    if resp.status_code == 200:
        return resp.json().get('user')
    return None


def process(messages):
    responses = []
    for msg in messages:
        if isinstance(msg, dict):
            if 'text' in msg:
                text = msg.get('text')
                if isinstance(text, str):
                    if any(phrase in text.lower() for phrase in ('hi', 'hello', 'hey',)):
                        if msg.get('channel'):
                            user = msg.get('user')
                            user = get_slack_user(user) if user else ''
                            responses.append(Message('Hi, {}!'.format(
                                user.get('real_name', 'Unknown')
                            ), msg.get('channel')))
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
    # custom_api = open('token')
    custom_api = open_slack(os.environ["SLACK_API_TOKEN"])
    if custom_api.is_connected():
        while custom_api.is_server_connected() is True:
            if len(outgoing_queue):
                outgoing_message = outgoing_queue.pop(0)
                custom_api.write(outgoing_message)
            incoming_queue = custom_api.read()
            print(incoming_queue)
            if len(incoming_queue):
                outgoing_queue.extend(process(incoming_queue))
            time.sleep(10)
    else:
        print('Connection failed')
    # while True:
    #     print('In start: Incoming - {}, Outgoing - {}'.format(
    #         incoming_queue, outgoing_queue))
    #     if len(outgoing_queue):
    #         outgoing_message = outgoing_queue.pop(0)
    #         custom_api.write(outgoing_message)
    #     if len(incoming_queue):
    #         incoming_messages = custom_api.read()
    #         outgoing_queue.extend(process(incoming_messages))
    #     print('Incoming - {}, Outgoing - {}'.format(incoming_queue,
    #                                                 outgoing_queue))
        # time.sleep(10)
    return


if __name__ == '__main__':
    main()
