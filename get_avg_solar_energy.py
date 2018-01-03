from astral import Location
from datetime import datetime, timedelta
import math
import time as tm
import os.path

import json
from urllib.request import urlopen
from pysolar import radiation
from pysolar import solar
import numpy as np

def get_solar_radiation(lat, lon, date):

	solarAlt = solar.get_altitude(lat, lon, date)

	solarPower = 0

	if solarAlt <= 0:
		return 0

	return radiation.get_radiation_direct(date, solarAlt)

def get_solar_radiation_data(date, days, lat, lon):
	radiation = []

	for i in range(days):
		daily_radiation = 0.0
		counted_hrs = 0.0
		for i in range(3600 * 24):

			r = get_solar_radiation(lat, lon, date)

			if r:
				radiation.append(r)

			date += timedelta(seconds = 1)


	return radiation


if __name__ == "__main__":

	import argparse

	def valid_date(s):
		try:
			return datetime.strptime(s, "%Y-%m-%d")
		except ValueError:
			msg = "Not a valid date: '{}'".format(s)
			raise argparse.ArgumentTypeError(msg)

	parser = argparse.ArgumentParser()
	parser.add_argument("--greenhouse", help="greenhouse characteristics file", default=None, type=str)
	parser.add_argument("--lat", help="latitude", default=None, type=float)
	parser.add_argument("--lon", help="longitude", default=None, type=float)
	parser.add_argument("--start", help="starting date in format YYYY-MM-DD", default=datetime, type=valid_date)
	parser.add_argument("--days", help="number of days", default=30, type=int)
	args = parser.parse_args()

	greenhouse = {}


	if args.greenhouse:
                with open(args.greenhouse, "r") as configFile:
       	                greenhouse = json.loads(configFile.read())

	if not args.lat and "latitude" in greenhouse:
		args.lat = greenhouse["latitude"]

	if not args.lon and "longitude" in greenhouse:
		args.lon = greenhouse['longitude']


	radiation = get_solar_radiation_data(args.start, args.days, args.lat, args.lon)

	print("avg radiation: {}W/m^2".format(np.average(radiation)))
	print("max radiation: {}W/m^2".format(np.max(radiation)))
	print("min radiation: {}W/m^2".format(np.min(radiation)))
