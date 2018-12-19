from transitions.extensions import GraphMachine
from utils import send_text_message, send_image_url
import requests
import pandas as pd
import numpy as np
from scipy.stats import f_oneway

data = pd.DataFrame()

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(
            model=self,
            **machine_configs
        )

    def is_going_to_start(self, event):
        return True

    def on_enter_start(self, event):
        print("I'm entering start")
        present = 'Hello :) There are some simple ways for dealing with data.\n'
        form = 'First, send your data please.\n'
             
        sender_id = event['sender']['id']
        responese = send_text_message(sender_id, present)
        responese = send_text_message(sender_id, form)

    def on_exit_start(self, event):
        print('Leaving start')


    def is_going_to_file(self, event):
        global data
        sender_id = event['sender']['id']
        form1 = 'Your data should be formed as a table. First column is the target value,'
        form2 = ' and second column should be the factors of the target value.'

        if event.get("message"):
            if 'attachments' in event['message'].keys():
                file = event['message']['attachments'][0]['payload']['url']
                data = todata(requests.get(file).content)
                print('is going to state2')
                print(data)
                if 'txt' in file or 'csv' in file:
                    if isformat(data) and not data.empty:
                        return True
                    else:
                        send_text_message(sender_id, 'Oops! Wrong format😂')
                        send_text_message(sender_id, form1 + form2)
                        return False
        return False

    def on_enter_file(self, event):
        print("I'm entering file")
        fun1 = 'Choose anova or describe🤔 Send OK if you don\'t want to do anything.' 
        sender_id = event['sender']['id']
        responese = send_text_message(sender_id, fun1)

    def on_exit_file(self, event):
        print('Leaving file')

    def is_going_to_anova(self, event):
        if event.get("message") and 'text' in event['message'].keys():
            text = event['message']['text']
            if text.lower() == 'anova':
                return True
        sender_id = event['sender']['id']
        return False

    def on_enter_anova(self, event):
        global data
        print("I'm entering anova")
        sender_id = event['sender']['id']
        out = anova(data)
        send_text_message(sender_id, out)

    def on_exit_anova(self, event):
        print('Leaving anova')


    def is_going_to_describe(self, event):
        if event.get("message") and 'text' in event['message'].keys():
            text = event['message']['text']
            return text.lower() == 'describe'
        return False

    def on_enter_describe(self, event):
        global data
        print("I'm entering describe")
        sender_id = event['sender']['id']
        out = describe(data)
        print(out)
        send_text_message(sender_id, out)
        
    def on_exit_describe(self, event):
        print('Leaving describe')


    def is_back_to_file(self, event):
        return True

    def is_back_to_user(self, event):
        if event.get("message") and 'text' in event['message'].keys():
            text = event['message']['text']
            return text.lower() == 'ok'
        return False

def isfloat(value):
  try:
    pd.to_numeric(value)
    return True
  except ValueError:
    return False

def isformat(data):
    return isfloat(data.iloc[:, 0])

def todata(string):
    string = string.decode("utf-8").split('\r\n')
    string = [x.split(',') for x in string]
    col = string.pop(0)
    count = string.count([''])
    for i in range(count):
        string.remove([''])
    data = pd.DataFrame(string, columns = col)
    for i in col:
        if isfloat(data[i]):
            data[i] = pd.to_numeric(data[i])
    return data

def describe(x, type = 'sample'):
    descri = '\n size: %-d\n mean: %-.3f\n S.D.: %-.3f\n  min: %-d\n  max: %-d'
    x = x.iloc[:, 0]
    line = '-' * (len(str(round(max(np.mean(x), np.std(x, ddof=0))))) + 12)
    if type == 'pop':
        line = max(line, '-'*17)
        return ' Population Info\n' + line + descri % (len(x), np.mean(x), np.std(x, ddof=0), min(x), max(x))

    return ' Sample Info\n' + line + descri % (len(x), np.mean(x), np.std(x, ddof=1), min(x), max(x))

def anova(x):
    f, p = f_oneway(*[list(x.iloc[:, 0][x.iloc[:, 1] == i]) for i in x.iloc[:, 1].unique()])
    return '  one-way ANOVA   \n' + '-' * 20 + '\n F-value: %.3f' % f + '\n p-value: %.3f' % p