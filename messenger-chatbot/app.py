from bottle import route, run, request, abort, static_file
import numpy as np
import requests
import os

from fsm import TocMachine


VERIFY_TOKEN = "Your Webhook Verify Token"
GRAPH_URL = "https://graph.facebook.com/v2.6"
ACCESS_TOKEN = "Your Page Access Token"


def send_text_message(id, text):
    url = "{0}/me/messages?access_token={1}".format(GRAPH_URL, ACCESS_TOKEN)
    payload = {
        "recipient": {"id": id},
        "message": {"text": text}
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print("Unable to send message: " + response.text)
    return response.text

machine = TocMachine(
    states=[
        'user',
        'start',
        'file',
        'anova',
        'describe'
    ],
    transitions=[
        {
            'trigger': 'advance',
            'source': 'user',
            'dest': 'start',
            'conditions': 'is_going_to_start'
        },
        {
            'trigger': 'advance',
            'source': 'start',
            'dest': 'file',
            'conditions': 'is_going_to_file'
        },
        {
            'trigger': 'advance',
            'source': 'file',
            'dest': 'anova',
            'conditions': 'is_going_to_anova'
        },
        {
            'trigger': 'advance',
            'source': 'file',
            'dest': 'describe',
            'conditions': 'is_going_to_describe'
        },
        {
            'trigger': 'advance',
            'source': ['anova', 'describe'],
            'dest': 'file',
            'conditions': 'is_back_to_file'
        },
        {
            'trigger': 'advance',
            'source': 'file',
            'dest': 'user',
            'conditions': 'is_back_to_user'
        }
    ],
    initial='user',
    auto_transitions=False,
    show_conditions=True,
)

@route("/webhook", method="GET")
def setup_webhook():
    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return challenge

    else:
        abort(403)


@route("/webhook", method="POST")
def webhook_handler():
    body = request.json
    print('\nFSM STATE: ' + machine.state)
    print('REQUEST BODY: ')
    print(body, '\n')

    if body['object'] == "page":
        event = body['entry'][0]['messaging'][0]
        machine.advance(event)
        return 'OK'
    


@route('/show-fsm', methods=['GET'])
def show_fsm():
    machine.get_graph().draw('fsm.png', prog='dot', format='png')
    return static_file('fsm.png', root='./', mimetype='image/png')

if __name__ == "__main__":
    run(host="localhost", port=5000, debug=True, reloader=True)
