#!/usr/bin/env python


import json
import RPi.GPIO as GPIO
from datetime import datetime
from time import time
import urllib2
import Queue


PIN_OUT_MODE = 27

PIN_STATUS_ON=2
PIN_STATUS_OFF=3

MODE_ON = GPIO.HIGH
MODE_OFF = GPIO.LOW

STATUS_ON = GPIO.HIGH
STATUS_OFF = GPIO.LOW

PIN_BUTTON_ON = 17
PIN_BUTTON_OFF = 18

STATE_FILE="state.json"

REMOTE_SERVER="http://stiebel.ormhuset.stack.se:8081"

REMOTE_STATE_ID="pump"
REMOTE_STATE_ID_UI="pump_ui"

REMOTE_POLL_INTERVAL = 300

event_queue = Queue.Queue()


def modeSignal(state):
    return state?MODE_ON:MODE_OFF

def statusSignal(state):
    return state?STATUS_ON:STATUS_OFF

def setupGPIO(initalState=False):
    GPIO.setup(PIN_OUT_MODE, GPIO.OUT, initial=modeSignal(initalState))
    GPIO.setup(PIN_STATUS_ON, GPIO.OUT, initial=statusSignal(initialState))
    GPIO.setup(PIN_STATUS_OFF, GPIO.OUT, initial=statusSignal(not initialState))
    GPIO.setup([PIN_BUTTON_ON, PIN_BUTTON_OFF], GPIO.IN, GPIO.PUD_UP)
    GPIO.add_event_detect(PIN_BUTTON_ON, GPIO.FALLING, callback=buttonPressOn, bouncetime=100)
    GPIO.add_event_detect(PIN_BUTTON_OFF, GPIO.FALLING, callback=buttonPressOff, bouncetime=100)


def setOutput(state):
    GPIO.output(PIN_OUT_MODE, modeSignal(state))
    GPIO.output(PIN_STATUS_ON, statusSignal(state))
    GPIO.output(PIN_STATUS_OFF, statusSignal(not state))

def buttonPressOn():
    event_queue.put("button_on")

def buttonPressOff():
    event_queue.put("button_off")


def stateBoolToStr(state):
    return state?"on":"off"

def stateStrToBool(s):
    s = s.strip().lower()

    return not s in ["off", "0", ""]


def loadState():
    state=json.load()
    with open(STATE_FILE, "r") as f:
        statedata = json.load(f)

    if statedata.has_key("state"):
        return stateStrToBool(statedata["state"])

    return False

def saveState(state):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    statedata = {
        "state": stateBoolToStr(state),
        "last_update": timestamp
    }

    with open(STATE_FILE, "w") as f:
        json.dump(statedata, f, sort_keys=True, indent=4, separators=(',', ': '))


def getUpdate():
    url="%s/state/%s" % (REMOTE_SERVER, REMOTE_STATE_ID_UI)
    response = urllib2.urlopen(url)
    data = json.load(response)
    return stateStrToBool(data["state"])

def sendUpdate(state, state_id=REMOTE_STATE_ID):
    url="%s/update/%s/%s" % (REMOTE_SERVER, state_id, stateBoolToStr(state)

    urllib2.urlopen(url)

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print "%s\t%s" % (timestamp, msg.strip())

def newState(new, old, ui_change=False):
    #Do nothing at all if state doesn't actually change
    if new==old:
        return old

    log("State changed to '%s'" % (stateBoolToStr(new)))
    setOutput(new)
    saveState(new)
    log("Updating server")
    sendUpdate(new)
    if(ui_change):
        log("Updating server UI")
        sendUpdate(new, REMOTE_STATE_ID_UI)

    return new

def main():
    log("Pump client starting up")
    state = loadState()
    log("Setting initial state: '%s'" % stateBoolToStr(state))
    setupGPIO(state)
    log("Sending initial state to server")
    sendUpdate(state)

    lastpoll=0

    #Main loop, never quits!
    while True:

        #Deal with button presses
        if event_queue.qsize() > 0:
            event = event_queue.get()
            if event == "button_on":
                log("Button ON pressed")
                state = newState(True, state, True)
            if event == "button_off":
                log("Button OFF pressed")
                state = newState(False, state, True)

        #See if it is time to poll stuff
        now = time.time()
        if (now-REMOTE_POLL_INTERVAL) > lastpoll:
            log("Polling remote ui state")
            remote_ui_state = getUpdate()
            state = newState(remote_ui_state, state)
            lastpoll = now



if __name__=="__main__":
    main()