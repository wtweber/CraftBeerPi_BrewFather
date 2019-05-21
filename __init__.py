# brewfather craftbeerpi3 plugin
# Log Tilt temperature and SG data from CraftBeerPi 3.0 to the brewfather app
# https://brewfather.app/
#
# Note this code is heavily based on the Thingspeak plugin by Atle Ravndal
# and I acknowledge his efforts have made the creation of this plugin possible
#
# 2018.11.09 -	Brewfather can now allocate Tilt by colour in the app. This is
#		a better way to handle this end also, as we do not need separate
#		parameters for each Tilt Colour Beer Name.
#		Get rid if the Beer Name parameters and pass all Tilt data to
#		Brewfather and let it work out where to put the data.
# TODO
#	* Check result of request() call and react

from modules import cbpi
from thread import start_new_thread
import logging
import requests
import datetime

DEBUG = False
drop_first = None

# Parameters
brewfather_comment = None
brewfather_id = None

# brewfather uses brew name to direct data to a particular batch
#   associate a Tilt color with a Brew Name here. I don't like
#   doing it this way must be an array or some way better to do this
# 2018.11.09 - Not any more it doesn't. Remove _beer parameters and processing
#brewfather_RED_beer = None
#brewfather_PINK_beer = None
# 2018.11.09 - End Changed code

def log(s):
    if DEBUG:
        s = "brewfather: " + s
        cbpi.app.logger.info(s)

@cbpi.initalizer(order=9000)
def init(cbpi):
    cbpi.app.logger.info("brewfather plugin Initialize")
    log("Brewfather params")
# the comment that goes along with each post (visible in the edit data screen)
    global brewfather_comment
# the unique id value (the bit following id= in the "Cloud URL" in the setting screen
    global brewfather_custom_stream
# 2018.11.09 - Remove _beer parameters and processing
# the batch number for the Red Tilt
#    global brewfather_RED_beer
# the batch number for the Pink Tilt
# I guess for now you just keep adding these for each additonal tilt
#    global brewfather_PINK_beer
# 2018.11.09 - End Changed code

    brewfather_comment = cbpi.get_config_parameter("brewfather_comment", None)
    log("Brewfather brewfather_comment %s" % brewfather_comment)
    brewfather_id = cbpi.get_config_parameter("brewfather_custom_stream", None)
    log("Brewfather brewfather_custom_stream %s" % brewfather_custom_stream)

    if brewfather_comment is None:
	log("Init brewfather config Comment")
	try:
	    cbpi.add_config_parameter("brewfather_comment", "", "text", "Brewfather comment")
	except:
	    cbpi.notify("Brewfather Error", "Unable to update Brewfather comment parameter", type="danger")
    if brewfather_custom_stream is None:
	log("Init brewfather config URL")
	try:
# TODO: is param2 a default value?
	    cbpi.add_config_parameter("brewfather_custom_stream", "", "text", "Brewfather custom string")
	except:
	    cbpi.notify("Brewfather Error", "Unable to update Brewfather custom string parameter", type="danger")

    log("Brewfather params ends")





# interval=900 is 900 seconds, 15 minutes, same as the Tilt Android App logs.
# if you try to reduce this, brewfather will throw "ignored" status back at you
@cbpi.backgroundtask(key="brewfather_temp_task", interval=900)
def brewfather_temp_background_task(api):
    log("brewfather temperature background task")
    global drop_first
    if drop_first is None:
        drop_first = False
        return False

    if brewfather_custom_stream is None:
        return False

    now = datetime.datetime.now()
    for key, value in cbpi.cache.get("sensors").iteritems():
	log("key %s value.name %s value.instance.last_value %s" % (key, value.name, value.instance.last_value))
#
# TODO: IMPORTANT - Temp sensor must be defined preceeding Gravity sensor and
#		    each Tilt must be defined as a pair without another Tilt
#		    defined between them, e.g.
#			RED Temperature
#			RED Gravity
#			PINK Temperature
#			PINK Gravity
#
	if (value.type == "ONE_WIRE_SENSOR"):
# A Tilt Temperature device is the first of the Tilt pair of sensors so
#    reset the data block to empty
		payload = "{ "
		payload += " \"name\": \"CraftBeerPi\",\r\n"

		temp = value.instance.last_value
# brewfather expects *F so convert back if we use C
		unit = cbpi.get_config_parameter("unit",None)
        payload += " \"temp\": \"%s\",\r\n" % temp
        payload += " \"temp_unit\": \"%s\",\r\n" % unit
        payload += " \"comment\": \"%s\" }" % cbpi.get_config_parameter("brewfather_comment", None)
        log("Payload %s" % payload)
        url = "http://log.brewfather.net/stream"
        headers = {
        'Content-Type': "application/json",
        'Cache-Control': "no-cache"
        }
        id = cbpi.get_config_parameter("brewfather_custom_stream", None)
        querystring = {"id":id}
        r = requests.request("POST", url, data=payload, headers=headers, params=querystring)
        log("Result %s" % r.text)
    log("brewfather done")
