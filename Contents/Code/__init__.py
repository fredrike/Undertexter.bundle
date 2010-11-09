#opensubtitles.org
#Subtitles service allowed by www.OpenSubtitles.org
from gzip import GzipFile
from StringIO import StringIO
 
OS_API = 'http://api.opensubtitles.org/xml-rpc'
OS_LANGUAGE_CODES = 'http://www.opensubtitles.org/addons/export_languages.php'
OS_PLEX_USERAGENT = 'plexapp.com v9.0'
subtitleExt       = ['utf','utf8','utf-8','sub','srt','smi','rt','txt','ssa','aqt','jss','ass','idx']
 
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
  
class OpenSubtitlesAgent(Agent.Movies):
  name = 'OpenSubtitles.org'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
      id    = 'null',
      score = 100    ))
    
  def update(self, metadata, media, lang):
    HTTP.Headers['User-agent'] = 'plexapp.com v9.0'
    proxy = XMLRPC.Proxy(OS_API)
    for i in media.items:
      for p in i.parts:
        token = proxy.LogIn('', '', 'en', OS_PLEX_USERAGENT)['token']
        requestList = [{'sublanguageid':Prefs["langPref1"], 'moviehash':p.openSubtitleHash, 'moviebytesize':str(p.size)}]
        if Prefs["langPref2"] != 'None':
          requestList.append({'sublanguageid':Prefs["langPref2"], 'moviehash':p.openSubtitleHash, 'moviebytesize':str(p.size)})
        subtitleResponse = proxy.SearchSubtitles(token,requestList)['data']
        #Log(requestList)
        if subtitleResponse != False:
          for st in subtitleResponse:
            if st['SubFormat'] in subtitleExt:
              subUrl = st['SubDownloadLink']
              subGz = StringIO(HTTP.Request(subUrl))
              gzipper = GzipFile(fileobj=subGz)      
              subText = gzipper.read()
              del gzipper
              p.subtitles[Locale.Language.Match(st['SubLanguageID'])][subUrl] = Proxy.Media(subText, ext=st['SubFormat'])