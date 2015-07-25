# -*- coding: utf-8 -*-
import re
import nominatim
import sched, time
from osmapi import OsmApi
from bot import OSMbot
import urllib
from configobj import ConfigObj
from typeemoji import typeemoji
from maptools import download,genBBOX

import user as u

def getData(id, geom_type=None):
    if geom_type is None:
        try:
            osm_data = api.NodeGet(int(id))
            if osm_data is None:
                try:
                    osm_data = api.WayGet(int(id))
                except:
                    osm_data = api.RelationGet(int(id))
        except:
            osm_data = None
    elif geom_type == "nod":
        osm_data = api.NodeGet(int(id))
    elif geom_type == "way":
        osm_data = api.WayGet(int(id))
    elif geom_type == "rel":
        osm_data = api.RelationGet(int(id))
    return osm_data

def SearchCommand(message):
    response = []
    t = ""
    search = message[8:].replace("\n", "").replace("\r", "")
    results = nom.query(search)
    if len(results) == 0:
        response = ['Sorry but I couldn\'t find any result for "{0}" \xF0\x9F\x98\xA2\nBut you can try to improve OpenStreetMap\xF0\x9F\x94\x8D\nhttp://www.openstreetmap.org'.format(search)]
    else:
        t = 'Results for "{0}":\n\n'.format(search)
        for result in results:
            if 'osm_id' in result:
                osm_data = getData(result['osm_id'])
            else:
                osm_data = None
            type = result['class']+":"+result['type']
            if type in typeemoji:
                t += typeemoji[result['class']+":"+result['type']]+" "+result["display_name"]+"\n"
            else:
                t += "\xE2\x96\xB6 "+result["display_name"]+"\n"
            t += "\xF0\x9F\x93\x8D http://www.openstreetmap.org/?minlat={0}&maxlat={1}&minlon={2}&maxlon={3}&mlat={4}&mlon={5}\n\n".format(result['boundingbox'][0],result['boundingbox'][1],result['boundingbox'][2],result['boundingbox'][3],result['lat'],result['lon'])
            if osm_data is not None and 'phone' in osm_data['tag']:
                t += "\nMore info /details{0}\nPhone /phone{0}\n\n".format(result['osm_id'])
            else:
                if 'osm_id' in result:
                    if 'osm_type' in result and result['osm_type'] =="node":
                        t += "\nMore info /detailsnod{0}\n\n".format(result['osm_id'])
                    elif 'osm_type' in result and result['osm_type'] == "way":
                        t += "\nMore info /detailsway{0}\n\n".format(result['osm_id'])
                    elif 'osm_type' in result and result['osm_type'] =="relation":
                        t += "\nMore info /detailsrel{0}\n\n".format(result['osm_id'])
                    else:
                        t += "\nMore info /details{0}\n\n".format(result['osm_id'])

        t += "\xC2\xA9 OpenStreetMap contributors\n"
    return response + [t]

def pretty_tags(data):
    tags = data['tag']
    response = []
    t = ""
    if 'name' in tags:
        t = "\xE2\x84\xB9 for "+str(tags['name'])+"\n"
    if 'addr:housenumber' in tags or 'addr:street' in tags or 'addr:city' in tags or 'addr:country' in tags:
        t += "\n"
    if 'addr:housenumber' and 'addr:street' in tags:
        t += "\xF0\x9F\x93\xAE "+tags['addr:street']+", "+tags['addr:housenumber']+"\n"
    else:
        if 'addr:housenumber' in tags:
            t += "\xF0\x9F\x93\xAE "+tags['addr:housenumber']+"\n"
        if 'addr:street' in tags:
            t += "\xF0\x9F\x93\xAE "+tags['addr:street']+"\n"
    if 'addr:city' in tags:
        t += tags['addr:city']+"\n"
    if 'addr:country' in tags:
       t += tags['addr:country']+"\n"
    if 'phone' in tags:
        t += "\xF0\x9F\x93\x9E "+str(tags['phone'])+"\n"
    if 'fax' in tags:
        t += "\xF0\x9F\x93\xA0 "+str(tags['fax'])+"\n"
    if 'email' in tags:
        t += "\xE2\x9C\x89 "+str(tags['email'])+"\n"
    if 'website' in tags:
        t += "\xF0\x9F\x8C\x8D "+str(tags['website'])+"\n"
    if 'opening_hours' in tags:
        t += "\xF0\x9F\x95\x9E "+str(tags['opening_hours'])+"\n"
    if 'internet_access' in tags:
        t += "\xF0\x9F\x93\xB6 "+str(tags['internet_access'])+"\n"
    if 'wheelchair' in tags:
        t += "\xE2\x99\xBF "+str(tags['wheelchair'])+"\n"
    if 'population' in tags:
        t += "\xF0\x9F\x91\xAA "+str(tags['population'])+"\n"
    if 'ele' in tags:
        t += "\xF0\x9F\x93\x8F "+str(tags['ele'])+" meters\n"
    if 'wikidata' in tags:
        t += "\xF0\x9F\x93\x97 https://www.wikidata.org/wiki/{0}".format(urllib.quote(tags["wikidata"]))+"\n"
    if 'wikipedia' in tags:
        if ":" in tags["wikipedia"]:
            lang = str(tags['wikipedia'].split(":")[0])
            term = str(tags['wikipedia'].split(":")[1])
            t += "\xF0\x9F\x93\x92 http://{0}.wikipedia.org/wiki/{1}".format(lang, urllib.quote(term))+"\n"
        else:
            t += "\xF0\x9F\x93\x92 http://wikipedia.org/wiki/{0}".format(urllib.quote(tags["wikipedia"]))+"\n"
    t += "\n\xC2\xA9 OpenStreetMap contributors\n"

    response.append(t)
    return response

def MapCommand(message, chat_id, user_id,zoom=None,imgformat=None,lat=None,lon=None):
    response = []
    message = message[4:]
    if lat is not None and lon is not None:
        bbox = genBBOX(lat, lon, 0.1)
        try:
            data = download(bbox, imageformat=imgformat, zoom=zoom)
        except ValueError as v:
                response.append(v.message)
        else:
            if imgformat == 'pdf':
                bot.sendDocument(chat_id, data, 'map.pdf')
            elif imgformat == 'jpeg':
                bot.sendPhoto(chat_id, data, "map.jpg", "Map")
            elif imgformat == 'png':
                bot.sendPhoto(chat_id, data, "map.png", "Map")
        user.set_field(user_id, 'mode', 'normal')
    else:
        print "message:"+str(message)
        if re.match(" ?(png|jpg|pdf)? ?(\d?\d)?$", message):
            m = re.match(" ?(?P<imgformat>png|jpg|pdf)? ?(?P<zoom>\d{0,2})$",message)
            zoom = m.groupdict()["zoom"]
            imgformat = m.groupdict()["imgformat"]
            response.append("Please send your location to recive the map")
            if imgformat is None:
                imgformat = 'png'
            if zoom == '':
                zoom = 19
            user.set_field(user_id, 'format', imgformat)
            user.set_field(user_id, 'zoom', zoom)
            user.set_field(user_id,'mode', 'map')

        elif re.match(" -?\d+(\.\d*)?,-?\d+(\.\d*)? (pngjpg|pdf)? ?(\d?\d)?", message):
            m = re.match(" (?P<lat>-?\d+(\.\d*)?),(?P<lon>-?\d+(\.\d*)?) ?(?P<imgformat>png|jpeg|pdf)? ?(?P<zoom>\d{0,2})",message)
            lat = float(m.groupdict()["lat"])
            lon = float(m.groupdict()["lon"])
            imgformat = m.groupdict()["imgformat"]
            zoom = m.groupdict()["zoom"]
            bbox = genBBOX(lat, lon, 0.1)
            if imgformat is None:
                imgformat = 'png'
            if zoom == '':
                zoom = 19
            try:
                data = download(bbox, imageformat=imgformat, zoom=zoom)
            except ValueError as v:
                response.append(v.message)
            else:
                if imgformat == 'pdf':
                    bot.sendDocument(chat_id, data, 'map.pdf')
                elif imgformat == 'jpeg':
                    bot.sendPhoto(chat_id, data, "map.jpg", "Map")
                elif imgformat == 'png':
                    bot.sendPhoto(chat_id, data, "map.png", "Map")
        elif re.match(" -?\d+(\.\d*)?,-?\d+(\.\d*)?,-?\d+(\.\d*)?,-?\d+(\.\d*)? ?(png|jpeg|pdf)? ?\d{0,2}",message):
            m = re.match(" (?P<bb1>-?\d+(\.\d*)?),(?P<bb2>-?\d+(\.\d*)?),(?P<bb3>-?\d+(\.\d*)?),(?P<bb4>-?\d+(\.\d*)?) ?(?P<format>png|jpg|pdf)? ?(?P<zoom>\d{0,2})",message)
            if m is not None:
                bbox1 = m.groupdict()["bb1"]
                bbox2 = m.groupdict()["bb2"]
                bbox3 = m.groupdict()["bb3"]
                bbox4 = m.groupdict()["bb4"]
                imgformat = m.groupdict()["format"]
                zoom = m.groupdict()["zoom"]
                if imgformat is None:
                    imgformat = 'png'
                if zoom == '':
                    zoom = 19
                try:
                    data = download([bbox1, bbox2, bbox3, bbox4], imgformat, zoom=zoom)
                except ValueError as v:
                    response.append(v.message)
                else:
                    if imgformat == 'pdf':
                        bot.sendDocument(chat_id, data, 'map.pdf')
                    elif imgformat == 'jpeg':
                        bot.sendPhoto(chat_id, data, "map.jpg", "Map")
                    elif imgformat == 'png':
                        bot.sendPhoto(chat_id, data, "map.png", "Map")
            else:
                response.append("Sorry but i don't undesrtand you")
        else:
            response.append("Sorry but i don't undesrtand you")
    return response

def PhoneCommand(message):
    id = message[6:]
    osm_data = getData(id)
    if "phone" in osm_data["tag"]:
        response = ["\xF0\x9F\x93\x9E "+osm_data["tag"]["phone"]]
    return response

def CleanMessage(message):
    if message.startswith("@osmbot"):
        message = message[8:]
    message = message.replace("\n", "").replace("\r", "")
    return message

def DetailsCommand(message):
    response =[]
    t = ""
    type = message[8:11]
    if type == "nod" or type == "way" or type == "rel":
        id = message[11:]
        osm_data = getData(id, geom_type=type)
    else:
        id = message[8:].strip()
        osm_data = getData(id)
    if osm_data is None:
        response.append("Sorry but I couldn't find any result, please check the id")
    else:
        if osm_data["tag"] == {}:
            response = ["Sorry, but now I can't recognize tags for this element, perhaps with my new features I will do it \xF0\x9F\x98\x8B"]
        else:
            response.append(t)
            t = ""
            message = pretty_tags(osm_data)
            response.append(message)
    return response

def attend(sc):
    if "last_id" in config:
        last_id = int(config["last_id"])
        updates = bot.getUpdates(offset=last_id+1)
    else:
        updates = bot.getUpdates(offset=0)
    if updates['ok']:
        print "Attending "+str(len(updates["result"]))+" "
        for query in updates['result']:
            response = []
            if 'from' in query['message'] and 'id' in query['message']['from']:
                user_config = user.get_user(query['message']['from']['id'])
                user_id = query['message']['from']['id']
            else:
                user_config = user.get_defaultconfig()
                user_id = 0
            t = ""
            if "message" in query:
                if "text" in query["message"]:
                    message = query["message"]["text"]
                else:
                    message = ""
                chat_id = query["message"]["chat"]["id"]
            message = CleanMessage(message)
            if "location" in query["message"]:
                print "loc:"+str(query["message"]["location"])
                if "mode" in user_config and user_config["mode"] == "map":
                    response += MapCommand(message, chat_id, user_id, zoom=user_config["zoom"],imgformat=user_config["format"],lat=float(query["message"]["location"]["latitude"]),lon=float(query["message"]["location"]["longitude"]))
            elif "text" in query["message"]:

                if message == "/start":
                    response = ["Hi, I'm the robot for OpenStreetMap data.\nHow I can help you?"]
                elif re.match(".*geo:-?\d+(\.\d*)?,-?\d+(\.\d*)?", message) is not None and  "mode" in user_config and user_config["mode"] == "map":
                    m = re.match(".*geo:(?P<lat>-?\d+(\.\d*)?),(?P<lon>-?\d+(\.\d*)?).*",message)
                    lat = m.groupdict()["lat"]
                    lon = m.groupdict()["lon"]
                    response += MapCommand(message, chat_id, user_id, zoom=user_config["zoom"], imgformat=user_config["format"], lat=float(lat), lon=float(lon))
                elif message.startswith("/map"):
                    response += MapCommand(message, chat_id, user_id)
                elif re.match("/phone.*", message):
                    response += PhoneCommand(message)
                elif re.match("/details.*", message):
                    response += DetailsCommand(message)
                elif message.startswith("/about"):
                    response = ["OpenStreetMap bot info:\n\nCREDITS&CODE\n\xF0\x9F\x91\xA5 Author: OSM català (Catalan OpenStreetMap community)\n\xF0\x9F\x94\xA7 Code: https://github.com/Xevib/osmbot\n\xE2\x99\xBB License: GPLv3, http://www.gnu.org/licenses/gpl-3.0.en.html\n\nNEWS\n\xF0\x9F\x90\xA4 Twitter: https://twitter.com/osmbot_telegram\n\nRATING\n\xE2\xAD\x90 Rating&reviews: http://storebot.me/bot/osmbot\n\xF0\x9F\x91\x8D Please rate me at: https://telegram.me/storebot?start=osmbot\n\nThanks for use @OSMbot!!"]
                elif message.startswith("/help"):
                    response = ["OpenStreetMap bot help:\n\nYou can control me by sending these commands:\n\n/about - Show info about OSMbot: credits&code, news and ratings&reviews\n\n/details<optional type><osm_id> - Show some tags from OSM database by ID. The ID is generated by /search command, but if you know an OSM ID you can try it.The type it's optional and it can be nod,way,rel if you don't sepecify it the bot will try to deduce it\n\n/search <search_term> - search from Nominatim in all OpenStreetMap database."]
                elif re.match("/search.*", message) is not None and message[8:] != "":
                    response += SearchCommand(message)
                elif re.match("/search", message) is not None:
                    response = ["Please indicate what are you searching with command /search <search term>"]
                else:
                    response = ["Use /search <search term> command to indicate what you are searching"]
                response.append(t)
                t = ""
                bot.sendMessage(chat_id, response,disable_web_page_preview='true')
            config["last_id"] = query["update_id"]
            config.write()
    sc.enter(int(config["update_interval"]), 1, attend, (sc,))

config = ConfigObj("bot.conf")
token = config["token"]

api = OsmApi()
nom = nominatim.Nominatim()
bot = OSMbot(token)
user = u.User("osmbot.db")

s = sched.scheduler(time.time, time.sleep)
s.enter(1, 1, attend, (s,))
s.run()
