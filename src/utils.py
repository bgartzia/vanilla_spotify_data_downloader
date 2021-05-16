""" This file include some utils that will be used in the other scripts
    in this project """

from datetime import timezone, datetime

##############################################################################
### Functions to work with the datetime
##############################################################################

def date_to_ts(date):
	''' Converts date formatted like yyyy-mm-dd to timestamp format, 
	    seconds since 1970-1-1
		Dates before of 1970 will return a negative value'''

	# If release date is not given, just put this date.
	d = [1970, 1, 1]
	if date == None:
		return "NA"
	info = date.split('-')
	for i in range(len(info)): d[i] = int(info[i])
	return int(datetime(d[0], d[1], d[2]).replace(tzinfo=timezone.utc).timestamp())


def datetime_to_ts(dt):
	''' Converts datetime formatted like yyyy-mm-ddThh:min:secZ to
	    timestamp format, seconds since 1970-1-1
		Dates before of 1970 will return a negative value'''

	d = dt.split('T')
	# Gather time data
	t = [int(t_info) for t_info in d[1][:-1].split(':')]
	# Gather date data
	d = [int(info) for info in d[0].split('-')]
	dt = datetime(d[0], d[1], d[2], t[0], t[1], t[2])
	return int(dt.replace(tzinfo=timezone.utc).timestamp())

