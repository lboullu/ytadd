# -*- coding: utf-8 -*-

import os
import sys, getopt

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import numpy as np
import isodate
from oauth2client import client # Added
from oauth2client import tools # Added
from oauth2client.file import Storage # Added

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def main(argv):
    #Reading arguments
    inputplaylist = ''
    outputplaylist = ''
    CriteriaMinute = 0
    outputplaylistCriteria = ''
    dateFrom = '1970-01-01'
    #startFrom = 1
    maxItem = 30
    try:
        opts, args = getopt.getopt(argv,"i:o:c:a:d:s:m:",["iplaylist=","oplaylist=", "criteriaM=", "oplaylist2=", "dateFrom=", "startFrom=", "maxItem="])
    except getopt.GetoptError:
        print('-i PlaylistFrom -o PlaylistTo -c criteria -d PlaylistCriteria')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-i", "--iplaylist"):
            inputplaylist = arg
        elif opt in ("-o", "--oplaylist"):
            outputplaylist = arg
        elif opt in ("-c", "--criteriaM"):            
            CriteriaMinute = int(arg)*60
        elif opt in ("-d", "--dateFrom"):
            dateFrom = arg
        elif opt in ("-a", "--oplaylist2"):
            outputplaylistCriteria = arg
       # elif opt in ("-s", "--startFrom"):
       #     startFrom = int(arg)
        elif opt in ("-m", "--maxItem"):
            maxItem = int(arg)

    ##### Authentification #####
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secret_445098121241.json"

    # Get credentials and create an API client    
    credential_path = os.path.join('./', 'credential_sample.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secrets_file, scopes)
        credentials = tools.run_flow(flow, store)

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    #print("logged in")

    #### Obtaining videos ####

    #print(inputplaylist)

    #Create list of videos from playlist        
    request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=maxItem,
            playlistId=inputplaylist
        )
    response = request.execute()

    #print(response['items'])

    if maxItem > 49:
        newmaxItem = maxItem - 49
        nextPageToken = response.get('nextPageToken')
        while ('nextPageToken' in response) and newmaxItem > 0 :
            nextPage = youtube.playlistItems().list(
                part="snippet",
                playlistId=inputplaylist,
                maxResults=newmaxItem,
                pageToken=nextPageToken
                ).execute()
            response['items'] = response['items'] + nextPage['items']
            if 'nextPageToken' not in nextPage:
                response.pop('nextPageToken', None)
            else:
                nextPageToken = nextPage['nextPageToken']
            newmaxItem = newmaxItem - 49

    
 
    #print("Got playlist item")

    ListVideoId = []
    for video in response['items']:
        ListVideoId.append(video['snippet']['resourceId']['videoId'])

    list_unique = np.unique(np.array(ListVideoId))
    list_unique_join = ','.join(list_unique.tolist())

    #print(len(list_unique))
    #print(list_unique)
    

    request = youtube.videos().list(
    part="snippet,contentDetails,statistics",
    id=list_unique_join
    )
    response_Vid = request.execute()

    #print("Obtained answer")
    
    ListVideoTimeFilter = []    
    
    for videoV in response_Vid['items']:
        vid_date = videoV['snippet']['publishedAt']
        vid_duration = isodate.parse_duration(videoV['contentDetails']['duration']).total_seconds()
        #print(vid_date)
        #print(dateFrom)        
        if vid_duration > CriteriaMinute and vid_date[:10] >= dateFrom:
            #print(vid_date[:10])
            #print(vid_date[:10] >= dateFrom)    
            request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": outputplaylist,
                        "position": 0,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": videoV['id']
                            }
                        }
                    }
                )
            try:
                response_exec = request.execute()
                #print("Added 1 video: ", videoV['id'])
            except googleapiclient.errors.HttpError:
                print("Video ", videoV['id'], " already in playlist")
        elif outputplaylistCriteria !="":
            if vid_date[:10] >= dateFrom:
                request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": outputplaylistCriteria,
                        "position": 0,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": videoV['id']
                            }
                        }
                    }
                )                
                try:
                    response_exec = request.execute()
                    #print("Added 1 video to auxiliary playlist: ", videoV['id'])          
                except googleapiclient.errors.HttpError:
                    print("Video ", videoV['id'], " already in playlist")                    
  
    

    #print ('Playlist to read is "', inputplaylist)
    #print ('Playlist to write is "', outputplaylist)
    

if __name__ == "__main__":
    main(sys.argv[1:])

    
            
        
         
