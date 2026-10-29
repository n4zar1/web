# Lee el feed RSS del canal de YouTube y guarda los últimos vídeos en videos.json.
import json, re, sys, time, urllib.request
import xml.etree.ElementTree as ET

CANAL = 'UCpJKRdNKFv1JkyeBxiTC2Cg'
CUANTOS = 6
NS = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}

def limpia(t):
    t = re.sub(r'#\S+', '', t)                                   # hashtags
    t = re.sub(r'[\U0001F000-\U0001FFFF☀-➿️]', '', t)  # emojis
    return re.sub(r'\s+', ' ', t).strip(' -|·')

# El feed de YouTube da 404 o 5xx a ratos: se reintenta y, si sigue fallando, se deja el videos.json de antes.
xml = None
for intento in range(5):
    try:
        xml = urllib.request.urlopen(f'https://www.youtube.com/feeds/videos.xml?channel_id={CANAL}', timeout=30).read()
        break
    except Exception as e:
        print(f'Intento {intento + 1}: {e}')
        time.sleep(20)
if xml is None:
    print('YouTube no responde; se mantiene el videos.json anterior.')
    sys.exit(0)
vids = []
for e in ET.fromstring(xml).findall('a:entry', NS)[:CUANTOS]:
    vid = e.find('yt:videoId', NS).text
    vids.append({'id': vid, 'titulo': limpia(e.find('a:title', NS).text), 'fecha': e.find('a:published', NS).text})
if vids:
    with open('videos.json', 'w', encoding='utf-8') as f:
        json.dump(vids, f, ensure_ascii=False, indent=1)
    print(len(vids), 'vídeos')
