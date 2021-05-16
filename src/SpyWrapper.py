""" This file defines the class that it will be used in the main function to 
     download the data.
""" 

import sys
import json
from configparser import ConfigParser
import spotipy as spy
from spotipy.oauth2 import SpotifyOAuth as spyOAuth
from .utils import (date_to_ts, datetime_to_ts)

##############################################################################

class SpyWrapper:

	def __init__(self, user_id, user_uri, client_id,
	             client_secret, redirect_uri="http://localhost:1410/",
				 all_playlists=False, output_file="your_spotify_data.json"):

		self.user_id = user_id
		self.user_uri = user_uri
		self.client_id = client_id
		self.client_secret = client_secret
		self.redirect_uri = redirect_uri
		self.get_all_playlists = all_playlists
		self.output_file = output_file
		self.__data = None


	@staticmethod
	def from_INI(ini_path, selector="DEFAULT"):
		''' Reads JSON from path and creates a SpyWrapper object
		    with the configuration within the file. '''

		cfg = ConfigParser()
		cfg.read(ini_path)
		try:
			cfg[selector]
		except KeyError:
			print("Error: the configuration selector didn't match with the "\
			      "configurations in the INI file. Make sure you are using a "\
				  "valid cfg selection, for example, by trying default.")
			sys.exit(2)

		try:
			wrp_spy = SpyWrapper(cfg[selector]['user_id'],
			                   cfg[selector]['user_uri'],
			                    cfg[selector]['client_id'],
								 cfg[selector]['client_secret'],
								  all_playlists=cfg.getboolean(selector, 'get_all_playlists'))
		except KeyError:
			print("Make sure the ini file is not corrupt.")
			sys.exit(2)

		return wrp_spy


	def get_OAuth(self, scope):
		''' Wrappers for the OAuth function '''

		return spyOAuth(client_id=self.client_id,
				        client_secret=self.client_secret,
				        redirect_uri=self.redirect_uri,
				        scope=scope)


	def scope_auth(self, scope):
		''' '''
		self.auth = self.get_OAuth(scope)
		self.sp = spy.Spotify(auth_manager = self.auth)

	
	def get_ALL(self, dbg=False):
		''' Gathers all data from all the liked tracks and those
		    tracks saved in user playlists '''

		if dbg: print('\nStarting to download saved tracks data')
		self.__data = self.get_all_saved_tracks(dbg=dbg)

		if dbg: print('\nStarting to download data from songs from saved playlists')
		self.__data = self.__data | self.get_all_data_from_playlist_tracks(dbg=dbg)
		self.__data = self.__data.values()


	def get_all_saved_tracks(self, dbg=False):
		''' Gets all the information from all the tracks liked by the user '''

		self.scope_auth("user-library-read")
		svd_tracks = self.sp.current_user_saved_tracks()

		data_collection = {}
		while svd_tracks:
			for track in svd_tracks['items']:
				gathered_data = self.gather_track_data(track)
				if gathered_data != None:
					data_collection[track['track']['id']] = gathered_data

			if dbg: print(svd_tracks['next'])

			if svd_tracks['next']:
				svd_tracks = self.sp.next(svd_tracks)
			else:
				svd_tracks = None

		if dbg: print('Gathered ' + str(len(data_collection.keys())) + ' songs data.')

		return data_collection
			

	def get_all_data_from_playlist_tracks(self, dbg=False):
		''' Gets all the information from all the tracks that are stored on 
		    all the playlists of a given user '''
			
		plst_ids = self.get_user_playlist_refs(dbg)

		data_collection = {}
		for plst in plst_ids:
			data_collection = data_collection | self.get_playlist_tracks(plst)

		return data_collection


	def get_user_playlist_refs(self, dbg=False):
		''' Gets the references of all the playlists that the user owns
		    and manages '''

		self.scope_auth("playlist-read-private")
		plsts = self.sp.current_user_playlists()
		ids = []
		while plsts:
			for pll in plsts['items']:
				# Only return uris of playlists created by you
				if pll['owner']['id'] == self.user_id or self.get_all_playlists:
					ids.append(pll['id'])
					if dbg:
						print()
						print(pll['owner'])
						print(pll['name'])
			if plsts['next']:
				plsts = self.sp.next(plsts)
			else:
				plsts = None

		return ids
			
		
	def get_playlist_tracks(self, tracklist_id, key_refs=False):
		''' Function to get all the track ids from the tracks of a playlist '''

		self.scope_auth("")
		tracks = self.sp.playlist_tracks(tracklist_id)

		data_collection = {}
		while tracks:
			for track in tracks['items']:
				gathered_data = self.gather_track_data(track)
				if gathered_data != None:
					data_collection[track['track']['id']] = gathered_data

			if tracks['next']:
				tracks = self.sp.next(tracks)
			else:
				tracks = None

		return data_collection

		
	def gather_track_data(self, track):
		''' Gets the information that could be interesting to have into
		    account when working with user-related tracks data. '''

		if len(track['track']['available_markets']) == 0:
			return None

		data_item = {}
		data_item['added_at'] = datetime_to_ts(track['added_at'])
		data_item['name'] = track['track']['name']
		data_item['album'] = track['track']['album']['name']
		data_item['album_type'] = track['track']['album']['album_type']
		try:
			data_item['added_by'] = track['added_by']['id']
		except KeyError:
			data_item['added_by'] = self.user_id

		data_item['release_date'] = date_to_ts(track['track']['album']['release_date'])
		data_item['popularity'] = track['track']['popularity']
		data_item['explicit'] = track['track']['explicit']
		data_item['artist'] = track['track']['artists'][0]['name']
		if len(track['track']['artists']) > 1:
			data_item['featurings'] = [artist['name'] for artist in track['track']['artists'][1:]]

		# List is returned, [0] to get the only track audio features
		a_feats = self.sp.audio_features(track['track']['id'])[0]
		a_feats.pop('type')
		data_item = data_item | a_feats
		data_item['scale'] = SpyWrapper.get_key(data_item['key'],
											  data_item['mode'])

		artist_data = self.sp.artist(track['track']['artists'][0]['id'])
		data_item['genres'] = artist_data['genres']

		return data_item


	@staticmethod
	def get_mode(mode):
		if mode == 0:
			return 'Major'
		elif mode == 1:
			return 'Minor'
		else:
			return None


	@staticmethod
	def get_key(key_id, mode):
		keys = ['C', 'C#', 'D', 'D#', 'E', 'F',
		        'F#', 'G', 'G#', 'A', 'A#', 'B']
		#TODO: maybe handle get_mode None return
		return keys[key_id] + ' ' + SpyWrapper.get_mode(mode)


	def get_artist(self, artist):
		return self.sp.artist(artist)

	def export_data_to_json(self):
		""" Exports the gathered data to a json file pointed by
		    the output_file configured in the object instance.
		"""
		with open(self.output_file, 'w') as wfile:
			json.dump(list(self.__data), wfile, indent=True)

