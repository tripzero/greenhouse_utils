from thermalobject import Water, Soil, Air, c_to_kelvin, kelvin_to_c
import json


if __name__ == "__main__":

	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('--tube_diameter', help="diameter of tubing in meters", type=float, default=0.0127) # 1/2in ID
	parser.add_argument('--flow_rate', help="flow rate in liters per second", type=float, default=0.22) #3.5gpm = 0.22lps
	parser.add_argument('--max_tube_length', help="maximum length of tubing", type=int, default=10000)
	parser.add_argument('--greenhouse', help="greenhouse characteristics file", type=str)
	parser.add_argument('--transfer_medium', help="air or water", type=str, default="water")
	parser.add_argument('--setpoint', help="desired temperature setpoint", default=32, type=int)
	parser.add_argument('--verbose', help='verbose mode', action='store_true')

	args = parser.parse_args()

	greenhouse = {}

	with open(args.greenhouse, "r") as configFile:
		greenhouse = json.loads(configFile.read())

	startTemp = c_to_kelvin(args.setpoint)
	endTemp = c_to_kelvin(15)

	transfer_medium = Water(mass=1, temperature=startTemp)

	if args.transfer_medium == "air":
		transfer_medium = Air(mass=1, temperature=startTemp)

	soil = Soil(mass=9999999999, temperature=endTemp-1)

	seconds = 999
	length = 0
	time = args.flow_rate
	energy = 0
	greenhouse_dimensions = greenhouse["greenhouse_dimensions"]

	energy_to_sink=greenhouse_dimensions[0] * greenhouse_dimensions[1] * 1000

	while  abs(energy) < (energy_to_sink * time):
		length += 1

		if args.verbose:
			print("trying tubing length: {}".format(length))
			print("{} temp: {}C".format(args.transfer_medium, kelvin_to_c(transfer_medium.temperature)))
			print("{} mass: {}g".format(args.transfer_medium, transfer_medium.mass))

		d = args.tube_diameter
		surface_area = 2 * 3.1415 * (d/2) * length + 2* 3.1415 * ((d/2) * (d/2))

		tube_volume = 3.1415 * ((d/2) * (d/2)) * length # m^3

		transfer_medium.mass = tube_volume * transfer_medium.density
		transfer_medium.temperature = startTemp

		time = tube_volume / (args.flow_rate / 1000)

		if args.verbose:
			print("time to move all medium: {}".format(time))

		transfer_medium.energy += (energy_to_sink * time)

		soil.temperature = endTemp - 1

		energy = transfer_medium.transferTo(soil, contactArea=surface_area, time=time)

		if args.verbose:
			print("energy transferred: {}/{}".format(abs(energy), energy_to_sink*time))

	print("energy to sink: {}W".format(energy_to_sink))
	print("total time for complete cycle of medium: {}".format(time))
	print("final length: {} meters".format(length))
	print("energy transferred {}W/m".format(energy_to_sink / length))
