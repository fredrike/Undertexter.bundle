#opensubtitles.org
#Subtitles service allowed by www.OpenSubtitles.org

OS_API = 'http://plexapp.api.opensubtitles.org/xml-rpc'
OS_LANGUAGE_CODES = 'http://www.opensubtitles.org/addons/export_languages.php'
OS_PLEX_USERAGENT = 'plexapp.com v9.0'
subtitleExt       = ['utf','utf8','utf-8','sub','srt','smi','rt','ssa','aqt','jss','ass','idx']
 
def Start():
  HTTP.CacheTime = CACHE_1DAY
  HTTP.Headers['User-agent'] = 'plexapp.com v9.0'

@expose
def GetImdbIdFromHash(openSubtitlesHash, lang):
  proxy = XMLRPC.Proxy(OS_API)
  try:
    os_movieInfo = proxy.CheckMovieHash('',[openSubtitlesHash])
  except:
    return None
    
  if os_movieInfo['data'][openSubtitlesHash] != []:
    return MetadataSearchResult(
      id    = "tt" + str(os_movieInfo['data'][openSubtitlesHash]['MovieImdbID']),
      name  = str(os_movieInfo['data'][openSubtitlesHash]['MovieName']),
      year  = int(os_movieInfo['data'][openSubtitlesHash]['MovieYear']),
      lang  = lang,
      score = 90)
  else:
    return None

def opensubtitlesProxy():
  HTTP.Headers['User-agent'] = 'plexapp.com v9.0'
  proxy = XMLRPC.Proxy(OS_API)
  username = Prefs["username"]
  password = Prefs["password"]
  if username == None or password == None:
    username = ''
    password = ''
  token = proxy.LogIn(username, password, 'en', OS_PLEX_USERAGENT)['token']
  return (proxy, token)

def fetchSubtitles(proxy, token, part):
  langList = [Prefs["langPref1"]]
  if Prefs["langPref2"] != 'None':
    langList.append(Prefs["langPref2"])
  for l in langList:
    Log('Looking for match for GUID %s and size %d' % (part.openSubtitleHash, part.size))
    subtitleResponse = proxy.SearchSubtitles(token,[{'sublanguageid':l, 'moviehash':part.openSubtitleHash, 'moviebytesize':str(part.size)}])['data']
    if subtitleResponse != False:
      for st in subtitleResponse: #remove any subtitle formats we don't recognize
        if st['SubFormat'] not in subtitleExt:
          Log('Removing a subtitle of type: ' + st['SubFormat'])
          subtitleResponse.remove(st)
      st = sorted(subtitleResponse, key=lambda k: int(k['SubDownloadsCnt']), reverse=True)[0] #most downloaded subtitle file for current language
      if st['SubFormat'] in subtitleExt:
        subUrl = st['SubDownloadLink']
        subGz = HTTP.Request(subUrl, headers={'Accept-Encoding':''}).content
        subData = Archive.GzipDecompress(subGz)
        part.subtitles[Locale.Language.Match(st['SubLanguageID'])][subUrl] = Proxy.Media(subData, ext=st['SubFormat'])
    else:
      Log('No subtitles available for language ' + l)
  
class OpenSubtitlesAgentMovies(Agent.Movies):
  name = 'OpenSubtitles.org'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
      id    = 'null',
      score = 100  ))
    
  def update(self, metadata, media, lang):
    (proxy, token) = opensubtitlesProxy()
    for i in media.items:
      for part in i.parts:
        fetchSubtitles(proxy, token, part)

class OpenSubtitlesAgentTV(Agent.TV_Shows):
  name = 'OpenSubtitles.org'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.thetvdb']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
      id    = 'null',
      score = 100  ))

  def update(self, metadata, media, lang):
    (proxy, token) = opensubtitlesProxy()
    for s in media.seasons:
      # just like in the Local Media Agent, if we have a date-based season skip for now.
      if int(s) < 1900:
        for e in media.seasons[s].episodes:
          for i in media.seasons[s].episodes[e].items:
            for part in i.parts:
              fetchSubtitles(proxy, token, part)
